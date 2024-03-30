from django import forms
from .models import Company, Product, Task, Category, SubCategory, Sale
import uuid

# TaskForm: Handles the form logic for creating and updating Task instances.
class TaskForm(forms.ModelForm):
    # Hidden field for task title, not required by the user to fill out.
    title = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Task
        # Specifies the model fields to include in the form.
        fields = ['user', 'title', 'description', 'contact', 'category', 'subcategory', 'status', 'regarding', 'priority']
        widgets = {
            # Custom widgets can be specified here.
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)

        # Assigns a unique title to new task instances.
        if not self.instance.pk:
            unique_id = uuid.uuid4().hex[:4].upper()
            second_unique_id = uuid.uuid4().hex[:4].upper()
            self.fields['title'].initial = f"TASK-{unique_id}-{second_unique_id}"
            self.fields['category'].queryset = Category.objects.all()
            self.fields['subcategory'].queryset = SubCategory.objects.none()

        # Applies Bootstrap classes to form fields for styling.
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if isinstance(field, (forms.fields.ChoiceField, forms.ModelChoiceField)):
                field.widget.attrs['class'] += ' form-select'

        # Sets initial values for some fields if 'user' is provided.
        if user:
            self.fields['user'].initial = user
        self.fields['status'].initial = 'New'
        self.fields['priority'].initial = 'Low Priority'

        # Dynamically updates 'subcategory' queryset based on 'category' selection.
        if 'category' in self.data:
            try:
                category_id = int(self.data.get('category'))
                self.fields['subcategory'].queryset = SubCategory.objects.filter(category_id=category_id).order_by('name')
            except (ValueError, TypeError):
                # Handles invalid input; falls back to an empty queryset.
                pass
        elif self.instance.pk:
            self.fields['subcategory'].queryset = self.instance.category.subcategories.order_by('name')

        # Updates queryset for 'regarding' to exclude self-references for existing instances.
        if self.instance.pk:
            self.fields['regarding'].queryset = Task.objects.exclude(pk=self.instance.pk)
        else:
            self.fields['regarding'].queryset = Task.objects.all()
        
        # Applies 'form-select' class to certain fields.
        select_fields = ['category', 'subcategory', 'contact', 'regarding', 'priority']
        for field_name in select_fields:
            field = self.fields.get(field_name)
            if field:
                field.widget.attrs['class'] = 'form-select'

    # Custom save method to handle additional logic.
    def save(self, commit=True):
        instance = super(TaskForm, self).save(commit=False)
        # Links task to a company based on the contact's company.
        if instance.contact:
            instance.company = instance.contact.company

        # Prevents title change for existing instances.
        if self.instance.pk:
            original_instance = Task.objects.get(pk=self.instance.pk)
            instance.title = original_instance.title

        # Saves the instance.
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

    def __init__(self, *args, **kwargs):
        super(CompanyForm, self).__init__(*args, **kwargs)
        # Applies Bootstrap classes for styling.
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if isinstance(field, (forms.fields.ChoiceField, forms.ModelChoiceField)):
                field.widget.attrs['class'] += ' form-select'
