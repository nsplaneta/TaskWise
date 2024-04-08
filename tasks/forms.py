from django import forms
from .models import Company, Individual, Product, Task, Category, SubCategory, Sale
import uuid

# TaskForm: Handles the form logic for creating and updating Task instances.
class TaskForm(forms.ModelForm):
    title = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Task
        fields = ['user', 'title', 'description', 'contact', 'category', 'subcategory', 'status', 'regarding', 'priority']
        widgets = {
            # You can specify any custom widgets here.
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)

        # Ensure unique title for new tasks
        if not self.instance.pk:
            unique_id = uuid.uuid4().hex[:4].upper()
            second_unique_id = uuid.uuid4().hex[:4].upper()
            self.fields['title'].initial = f"TASK-{unique_id}-{second_unique_id}"

        # Set querysets for category and subcategory
        self.fields['category'].queryset = Category.objects.all()
        self.fields['subcategory'].queryset = SubCategory.objects.none()

        # Apply Bootstrap classes for styling
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name in ['category', 'subcategory', 'contact', 'regarding', 'priority']:
                field.widget.attrs['class'] += ' form-select'

        # Set initial values for certain fields
        if user:
            self.fields['user'].initial = user
        self.fields['status'].initial = 'New'
        self.fields['priority'].initial = 'Low Priority'

        # Update subcategory queryset based on category selection
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                pass  # An empty queryset will be used if the category ID is invalid
        elif self.instance.pk:
            self.fields['subcategory'].queryset = self.instance.category.subcategories.order_by('name')

        # Update regarding queryset to exclude current instance
        if self.instance.pk:
            self.fields['regarding'].queryset = Task.objects.exclude(pk=self.instance.pk)
        else:
            self.fields['regarding'].queryset = Task.objects.all()

    def save(self, commit=True):
        instance = super(TaskForm, self).save(commit=False)
        
        # Link task to a company based on the contact's company, if available
        if instance.contact:
            instance.company = instance.contact.company
        
        # Prevent title change for existing tasks
        if self.instance.pk:
            original_instance = Task.objects.get(pk=self.instance.pk)
            instance.title = original_instance.title
        
        if commit:
            instance.save()
            self._save_m2m()

        return instance

# SaleForm: Manages Sale instance forms.
class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super(SaleForm, self).__init__(*args, **kwargs)
        # Applies Bootstrap classes for styling.
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control form-select'

# ProductForm: Handles forms for Product instances.
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'serial_number']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Applies Bootstrap classes for styling.
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if isinstance(field, (forms.fields.ChoiceField, forms.ModelChoiceField)):
                field.widget.attrs['class'] += ' form-select'

# CompanyForm: Manages forms for Company instances.
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'email', 'phone', 'address', 'additional_details', 'registration_number']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),  # Changed to TextInput
            'additional_details': forms.TextInput(attrs={'class': 'form-control'}),  # Changed to TextInput
        }

    def __init__(self, *args, **kwargs):
        super(CompanyForm, self).__init__(*args, **kwargs)
        # Applies Bootstrap classes for styling.
        for field_name, field in self.fields.items():
            if field_name not in ['address', 'additional_details']:  # These already have custom widgets
                field.widget.attrs['class'] = 'form-control'
            if isinstance(field, (forms.fields.ChoiceField, forms.ModelChoiceField)):
                field.widget.attrs['class'] += ' form-select'

# IndividualForm: Manages forms for Individual instances.
class IndividualForm(forms.ModelForm):
    class Meta:
        model = Individual
        fields = ['name', 'email', 'phone', 'address', 'company', 'additional_details']
        widgets = {
            'address': forms.TextInput(attrs={'class': 'form-control'}),  # Already set to TextInput
            'additional_details': forms.TextInput(attrs={'class': 'form-control'}),  # Add this line
        }

    def __init__(self, *args, **kwargs):
        super(IndividualForm, self).__init__(*args, **kwargs)
        # Applies Bootstrap classes for styling.
        for field_name, field in self.fields.items():
            if field_name not in ['address', 'additional_details']:  # These already have custom widgets
                field.widget.attrs['class'] = 'form-control'
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs['class'] += ' form-select'
