from django import forms
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.db.models import CharField, Q
from django.db.models.functions import Cast
from django.forms import inlineformset_factory
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from .forms import CompanyForm, ProductForm, SaleForm, TaskForm
from .models import Company, Individual, Product, Sale, SaleProduct, StatusChoices, SubCategory, Task
from django.contrib.auth.models import User
from django.views.generic.edit import CreateView

# Define a constant for the admin group name.
ADMIN_GROUP = 'Managers'

def user_in_group(user):
    """Check if a user belongs to a specified group or is a superuser."""
    return user.groups.filter(name=ADMIN_GROUP).exists() or user.is_superuser

def index(request):
    """Redirect authenticated users to the dashboard; others to the index page."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return render(request, 'index.html', {})
    
def dashboard(request):
    """Render dashboard with tasks and sales data for the logged-in user."""
    user = request.user

    # Calculate the start of the current month and get the current month's name.
    now = timezone.now()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_name = now.strftime('%B')

    # Gather tasks and sales totals, for all time and for the current month.
    total_tasks = Task.objects.filter(user=user).count()
    total_sales = Sale.objects.filter(task__user=user).count()
    total_tasks_this_month = Task.objects.filter(user=user, created_at__gte=start_of_month).count()
    total_sales_this_month = Sale.objects.filter(task__user=user, date__gte=start_of_month).count()

    # Fetch the last 5 tasks and sales for the user.
    tasks = Task.objects.filter(user=user).order_by('-created_at')[:5]
    sales = Sale.objects.filter(task__user=user).order_by('-date')[:5]

    # Determine if the user is an admin.
    is_admin = user.groups.filter(name='Admin').exists()

    # Compile context for rendering.
    context = {
        'total_tasks': total_tasks,
        'total_sales': total_sales,
        'total_tasks_this_month': total_tasks_this_month,
        'total_sales_this_month': total_sales_this_month,
        'current_month_name': current_month_name,
        'tasks': tasks,
        'sales': sales,
        'user_info': user,
        'is_admin': is_admin,
        'current_section': 'home',
    }
    return render(request, 'index.html', context)

def sale_detail(request, sale_id):
    """Display details for a specific sale."""
    sale = get_object_or_404(Sale, pk=sale_id)
    sale_products = SaleProduct.objects.filter(sale=sale).select_related('product')
    return render(request, 'sales/sale_detail.html', {
        'sale': sale, 
        'sale_products': sale_products,
        'current_section': 'sales'
        })

# Configure the formset for managing SaleProducts in a Sale.
SaleProductFormSet = inlineformset_factory(
    Sale,
    SaleProduct,
    fields=('product', 'quantity'),
    extra=1,
    widgets={'product': forms.Select(attrs={'class': 'form-select'}), 'quantity': forms.NumberInput(attrs={'min': 1})}
)

def create_sale(request, task_id):
    """Create a sale for a given task, ensuring the task is assigned to the user."""
    task = get_object_or_404(Task, id=task_id)
    
    if task.user != request.user:
        messages.error(request, 'You are not allowed to create a sale for a task not assigned to you.')
        return redirect('task_detail', task_id=task.id)
    
    if request.method == 'POST':
        formset = SaleProductFormSet(request.POST)
        sale = Sale(task=task, status=StatusChoices.NEW, date=timezone.now())
        if formset.is_valid():
            sale.save()  # First save the sale to generate an ID for the foreign key.
            instances = formset.save(commit=False)
            for instance in instances:
                instance.sale = sale
                instance.save()
            return redirect(reverse('sale_detail', args=[sale.id]))
    else:
        formset = SaleProductFormSet()

    return render(request, 'sales/create_sale.html', {
        'formset': formset,
        'task': task,
        'current_section': 'sales'
    })

def edit_sale(request, sale_id):
    """Allow users to edit a sale if they have the correct permissions."""
    sale = get_object_or_404(Sale, id=sale_id)

    # Check permissions based on user's relation to the sale.
    same_group = sale.task.user.groups.filter(name__in=request.user.groups.values_list('name', flat=True)).exists()
    can_edit = sale.task.user == request.user or same_group or user_in_group(request.user)
    if not can_edit:
        messages.error(request, 'You are not allowed to edit this sale')
        return redirect('sale_detail', sale_id=sale.id)

    if request.method == 'POST':
        form = SaleForm(request.POST, instance=sale)
        formset = SaleProductFormSet(request.POST, instance=sale)
        if form.is_valid() and formset.is_valid():
            sale = form.save(commit=False)
            sale.last_updated_by = request.user
            sale.save()
            formset.save()
            return redirect('sale_detail', sale_id=sale.id)
    else:
        form = SaleForm(instance=sale)
        formset = SaleProductFormSet(instance=sale)

    return render(request, 'sales/edit_sale.html', {
        'sale': sale,
        'form': form,
        'formset': formset,
        'current_section': 'sales'
    })

@require_http_methods(["POST"])
def delete_sale(request):
    """Delete selected sales, ensuring they are owned by the user."""
    sale_ids = request.POST.getlist('sale_ids', [])
    forbidden_sales = []

    for sale_id in sale_ids:
        sale = get_object_or_404(Sale, id=sale_id)
        can_delete = sale.task.user == request.user
        if not can_delete:
            forbidden_sales.append(sale_id)

    if forbidden_sales:
        messages.error(request, 'You are not allowed to delete some or all selected sales.')
    else:
        Sale.objects.filter(id__in=sale_ids, task__user=request.user).delete()
        messages.success(request, 'Selected sales have been successfully deleted.')

    return redirect('sale_list')

def contact_list(request):
    """Handle AJAX requests for contact lists with pagination, filtering by type and search term."""
    paginate_by = 7  # Defines the number of contacts per page.
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        contact_type = request.GET.get('contact_type')
        search_query = request.GET.get('search_term', '')

        # Filter contacts based on the contact type (individuals or companies).
        if contact_type == 'individuals':
            individuals = Individual.objects.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query)
            ).select_related('company').values(
                'id', 'name', 'email', 'phone', 'company__name'
            ).order_by('-created_at')
            contacts_data = list(individuals)
        else:  # Fetch companies with a similar filtering approach.
            companies = Company.objects.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(registration_number__icontains=search_query)
            ).values(
                'id', 'name', 'email', 'phone', 'registration_number', 'reference__name'
            ).order_by('-created_at')
            contacts_data = list(companies)

        return JsonResponse({'data': contacts_data})
    else:
        # Render the initial contact list page for non-AJAX requests.
        return render(request, 'contacts/contact_list.html', {'current_section': 'contacts'})

def contact_detail(request, id, contact_type):
    """Display detailed information for an individual or company contact."""
    # Check if the user has admin privileges.
    user_info = request.user
    is_superuser_or_manager = user_info.is_superuser or user_info.groups.filter(name='Admin').exists()

    context = {
        'is_superuser_or_manager': is_superuser_or_manager, 
        'current_section': 'contacts'}

    # Load the appropriate contact based on the type and ID.
    if contact_type == 'individual':
        individual = get_object_or_404(Individual, pk=id)
        context['contact'] = individual
        context['type'] = 'individual'
    elif contact_type == 'company':
        company = get_object_or_404(Company, pk=id)
        context['contact'] = company
        context['type'] = 'company'
    
    return render(request, 'contacts/contact_detail.html', context)

def task_detail(request, task_id):
    """Show details for a specific task."""
    task = get_object_or_404(Task, pk=task_id)
    return render(request, 'tasks/task_detail.html', {'task': task, 'current_section': 'tasks'})

def create_task(request):
    """Handle the creation of a new task through a form submission."""
    if request.method == 'POST':
        form = TaskForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm(user=request.user)

    # Specify fields to exclude from the form.
    exclude_fields = ['user', 'status']
    
    return render(request, 'tasks/create_task.html', {
        'form': form,
        'exclude_fields': exclude_fields,
        'current_section': 'tasks'
    })

def ajax_load_subcategories(request):
    """Dynamically load subcategories based on a selected category."""
    category_id = request.GET.get('category')
    subcategories = SubCategory.objects.filter(category_id=category_id).order_by('name')
    html = render_to_string('tasks/subcategory_dropdown_list_options.html', {'subcategories': subcategories})
    return JsonResponse({'html': html})

def edit_task(request, task_id):
    """Edit an existing task, ensuring the user has permission."""
    task = get_object_or_404(Task, id=task_id)

    # Verify if the user is authorized to edit the task.
    same_group = task.user.groups.filter(name__in=request.user.groups.values_list('name', flat=True)).exists()
    can_edit = task.user == request.user or same_group or user_in_group(request.user)
    if not can_edit:
        messages.error(request, 'You are not allowed to edit this task')
        return redirect('task_detail', task_id=task.id)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            task = form.save(commit=False)
            task.last_updated_by = request.user
            task.save()
            form.save_m2m()
            return redirect('task_detail', task_id=task.id)
    else:
        form = TaskForm(instance=task, user=request.user)

    # Exclude specific fields from being edited.
    exclude_fields = ['user', 'status', 'title']

    return render(request, 'tasks/edit_task.html', {
        'form': form,
        'task_id': task_id,
        'exclude_fields': exclude_fields,
        'current_section': 'tasks'
    })

@require_http_methods(["GET", "POST"])
def delete_task(request):
    """Allow users to delete their own tasks, verifying ownership first."""
    if request.method == 'POST':
        task_ids = request.POST.getlist('task_ids')
        tasks_to_delete = Task.objects.filter(id__in=task_ids, user=request.user)

        if not tasks_to_delete:
            messages.error(request, 'You are not allowed to delete the selected tasks.')
            return redirect('task_list')

        tasks_to_delete.delete()
        messages.success(request, 'Selected tasks have been successfully deleted.')
        return redirect('task_list')

    # For GET requests, show a list of tasks to select from for deletion.
    tasks = Task.objects.filter(user=request.user)
    return render(request, 'tasks/delete_task.html', {'tasks': tasks})

def assign_to_me(request, task_id):
    """Assign a specific task to the logged-in user, verifying permissions."""
    task = Task.objects.get(id=task_id)
    
    # Verify if the user has the required permissions to assign the task to themselves.
    if request.user.groups.filter(name=ADMIN_GROUP).exists() or request.user.is_superuser:
        task.user = request.user
        task.save()
        messages.success(request, 'Task assigned to you successfully.')
    else:
        # Check if the user belongs to the same group as the task's assigned user.
        if task.user.groups.filter(name=request.user.groups.first().name).exists():
            task.user = request.user
            task.save()
            messages.success(request, 'Task assigned to you successfully.')
        else:
            messages.success(request, 'You do not have permission to assign this task.')
    return redirect('task_detail', task_id=task_id)

class TaskListView(LoginRequiredMixin, ListView):
    """Display a list of tasks with filters for viewing personal, team, or all tasks."""
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    paginate_by = 7  # Number of tasks per page

    def get_queryset(self):
        # Filter tasks based on search term and list type (all, my_team, my_tasks).
        search_term = self.request.GET.get('search', '')
        queryset = Task.objects.filter(title__icontains=search_term) if search_term else Task.objects.all()

        list_type = self.request.GET.get('list', 'all')
        if list_type == 'my_team':
            groups = self.request.user.groups.all()
            users_in_same_groups = User.objects.filter(groups__in=groups).distinct()
            queryset = queryset.filter(user__in=users_in_same_groups)
        elif list_type == 'my_tasks':
            queryset = queryset.filter(user=self.request.user)

        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        # Add search term and page title to the context.
        context = super().get_context_data(**kwargs)
        context['search_term'] = self.request.GET.get('search', '')
        list_type = self.request.GET.get('list', 'all')
        context['page_title'] = self._determine_page_title(list_type)
        context['current_section'] = 'tasks'
        return context

    def _determine_page_title(self, list_type):
        # Helper method to set the page title based on the list type.
        if list_type == 'my_team':
            return mark_safe('<i class="bi bi-people"></i> My Team\'s Tasks')
        elif list_type == 'my_tasks':
            return mark_safe('<i class="bi bi-tags"></i> My Tasks')
        return mark_safe('<i class="bi bi-check-all"></i> All Tasks')

    def render_to_response(self, context, **response_kwargs):
        # Handle AJAX requests separately to return JSON data.
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            tasks_data = list(self.get_queryset().values('id', 'title', 'description', 'status', 'user__username', 
                                                         'category__name', 'subcategory__name', 'contact__name', 
                                                         'created_at', 'updated_at'))
            return JsonResponse({'data': tasks_data})
        else:
            return super().render_to_response(context, **response_kwargs)

class SaleListView(LoginRequiredMixin, ListView):
    """Display a list of sales with filters for personal, team, or all sales."""
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'

    def get_queryset(self):
        # Filter sales based on the search term and list type.
        search_term = self.request.GET.get('search', '')
        queryset = self.model.objects.all()
        if search_term:
            queryset = queryset.annotate(id_str=Cast('id', output_field=CharField())).filter(id_str__startswith=search_term)

        list_type = self.request.GET.get('list', 'all')
        if list_type == 'my_team':
            groups = self.request.user.groups.all()
            users_in_same_groups = User.objects.filter(groups__in=groups).distinct()
            queryset = queryset.filter(task__user__in=users_in_same_groups)
        elif list_type == 'my_sales':
            queryset = queryset.filter(task__user=self.request.user)

        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        # Add search term and dynamically determined page title to the context.
        context = super().get_context_data(**kwargs)
        list_type = self.request.GET.get('list', 'all')
        context['page_title'] = self._determine_page_title(list_type)
        context['current_section'] = 'sales'
        return context

    def _determine_page_title(self, list_type):
        # Helper method to set the page title based on the list type.
        if list_type == 'my_team':
            return mark_safe('<i class="bi bi-people"></i> My Team Sales')
        elif list_type == 'my_sales':
            return mark_safe('<i class="bi bi-tags"></i> My Sales')
        return mark_safe('<i class="bi bi-check-all"></i> All Sales')

    def render_to_response(self, context, **response_kwargs):
        # Handle AJAX requests to return JSON data for sales.
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            sales_data = list(self.get_queryset().values('id', 'task__user__username', 'date', 'status'))
            for sale in sales_data:
                sale_products = SaleProduct.objects.filter(sale_id=sale['id']).select_related('product')
                sale['products'] = [{'name': sp.product.name, 'quantity': sp.quantity} for sp in sale_products]
            return JsonResponse({'data': sales_data})
        else:
            return super().render_to_response(context, **response_kwargs)
class ProductListView(LoginRequiredMixin, ListView):
    """Display a list of products, allowing for filtering by search terms."""
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'

    def get_queryset(self):
        # Filter products based on search term.
        search_term = self.request.GET.get('search', '')
        queryset = Product.objects.filter(
            Q(name__icontains=search_term) | Q(serial_number__icontains=search_term)
        ) if search_term else Product.objects.all()
        return queryset.order_by('-id')  # Newest products first

    def get_context_data(self, **kwargs):
        # Add additional context for rendering.
        context = super().get_context_data(**kwargs)
        context['current_section'] = 'products'
        context['is_superuser_or_manager'] = self.request.user.is_superuser or self.request.user.groups.filter(name='Admin').exists()
        return context

    def render_to_response(self, context, **response_kwargs):
        # Handle AJAX requests by returning JSON data.
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            products_data = list(self.get_queryset().values('id', 'name', 'description', 'price', 'serial_number'))
            return JsonResponse({'data': products_data})
        else:
            return super().render_to_response(context, **response_kwargs)

# SETTINGS
def settings_view(request):
    """Display settings page for current user."""
    context = {
        'user_info': request.user,
        'is_superuser_or_manager': request.user.is_superuser or request.user.groups.filter(name=ADMIN_GROUP).exists(),
    }
    return render(request, 'auth/settings/index.html', context)

def update_user_info(request):
    """Allow users to update their profile information."""
    if request.method == 'POST':
        user = request.user  # Current user
        # Update user details with form data
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()  # Apply changes
        messages.success(request, 'Info updated successfully.')
        return redirect('settings')  # Redirect to prevent double POST
    else:
        return render(request, 'auth/settings/index.html', {'user_info': request.user})
    
def change_password(request):
    """Allows user to change their password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Prevents logout
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password_done')  # Redirect to confirmation page
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'auth/password_change.html', {
        'form': form,
        'is_superuser_or_manager': request.user.is_superuser or request.user.groups.filter(name=ADMIN_GROUP).exists(),
    })

def settings_contact_list(request):
    """Display settings for managing contacts."""
    context = {
        'is_superuser_or_manager': request.user.is_superuser or request.user.groups.filter(name=ADMIN_GROUP).exists(),
    }
    return render(request, 'auth/settings/contacts.html', context)

def contact_settings(request, id, contact_type):
    """Manage settings for an individual contact or company."""
    context = {
        'is_superuser_or_manager': request.user.is_superuser or request.user.groups.filter(name='Admin').exists(),
        'current_section': 'contacts'
    }

    if contact_type == 'individual':
        individual = get_object_or_404(Individual, pk=id)
        context.update({
            'contact': individual,
            'type': 'individual',
            'all_companies': Company.objects.all(),
        })
    elif contact_type == 'company':
        company = get_object_or_404(Company, pk=id)
        context.update({
            'contact': company,
            'type': 'company',
            'company_individuals': Individual.objects.filter(company=company),
        })
    return render(request, 'auth/settings/contact_settings.html', context)

def update_contact_info(request, contact_id, contact_type):
    """Updates information for a contact (individual or company) based on provided data."""
    if contact_type == 'individual':
        contact = get_object_or_404(Individual, pk=contact_id)
    elif contact_type == 'company':
        contact = get_object_or_404(Company, pk=contact_id)
    else:
        messages.error(request, "Invalid contact type.")
        return redirect(f'/contacts/{contact_type}/contact_detail/{contact_id}')

    if request.method == 'POST':
        # Update contact details from form data
        contact.name = request.POST.get('name', contact.name)
        contact.email = request.POST.get('email', contact.email)
        contact.phone = request.POST.get('phone', contact.phone)
        contact.address = request.POST.get('address', contact.address)
        contact.additional_details = request.POST.get('additional_details', contact.additional_details)

        if contact_type == 'company':
            contact.registration_number = request.POST.get('registration_number', contact.registration_number)
        
        contact.save()
        messages.success(request, 'Contact information updated successfully.')
        return redirect(f'/contacts/{contact_type}s/contact_detail/{contact_id}')

    return redirect(f'/contacts/{contact_type}s/contact_detail/{contact_id}')

def contact_delete(request, contact_id, contact_type):
    """Deletes a contact (individual or company), with an option to delete related individuals for companies."""
    if contact_type == 'individual':
        contact = get_object_or_404(Individual, pk=contact_id)
    elif contact_type == 'company':
        contact = get_object_or_404(Company, pk=contact_id)
        if request.POST.get('delete_related') == 'yes':
            contact.individuals.all().delete()
            messages.success(request, 'Company and all related individuals deleted successfully.')
        else:
            messages.success(request, 'Company deleted successfully.')
    else:
        messages.error(request, "Invalid contact type.")
        return redirect('/contacts/')

    if not request.user.is_superuser and not request.user.groups.filter(name='Admin').exists():
        messages.error(request, 'You do not have permission to delete this contact.')
        return redirect('/contacts/')

    contact.delete()
    return redirect('/contacts/')

def product_detail(request, id):
    """Displays details for a specific product."""
    product = get_object_or_404(Product, pk=id)
    context = {
        'product': product,
        'is_superuser_or_manager': request.user.is_superuser or request.user.groups.filter(name='Admin').exists(),
        'current_section': 'products'
    }
    return render(request, 'products/product_detail.html', context)

def product_settings(request, id):
    """Allows editing of product details."""
    product = get_object_or_404(Product, pk=id)

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.serial_number = request.POST.get('serial_number', product.serial_number)
        product.save()
        return redirect('product_detail', id=id)

    context = {
        'product': product,
        'is_superuser_or_manager': request.user.is_superuser or request.user.groups.filter(name='Admin').exists(),
        'current_section': 'products'
    }
    return render(request, 'auth/settings/product_settings.html', context)

def product_delete(request):
    """Deletes a specified product."""
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, pk=product_id)

    if not request.user.is_superuser and not request.user.groups.filter(name='Manager').exists():
        messages.error(request, 'You do not have permission to delete this product.')
        return redirect('/products/')

    product.delete()
    messages.success(request, 'Product deleted successfully.')
    return redirect('/products/')

class CreateProductView(CreateView):
    """View to handle the creation of a new product via a form."""
    model = Product
    form_class = ProductForm
    template_name = 'auth/settings/create_product.html'
    success_url = reverse_lazy('product_list')

def create_company(request):
    """Handles the creation of a new company via a form."""
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Company created successfully!')
            return redirect('contact_list')
    else:
        form = CompanyForm()

    context = {'form': form, 'page_title': 'Create New Company'}
    return render(request, 'auth/settings/create_company.html', context)


