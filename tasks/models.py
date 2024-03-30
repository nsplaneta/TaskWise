from django.db import models
from django.forms import ValidationError
from django.utils import timezone
from django.contrib.auth.models import User

# Provides predefined choices for the status of tasks and sales.
class StatusChoices(models.TextChoices):
    NEW = 'New', 'New'
    IN_PROGRESS = 'In Progress', 'In Progress'
    PENDING_CUSTOMER = 'Pending Customer', 'Pending Customer'
    PENDING_PARTNER = 'Pending Partner', 'Pending Partner'
    ESCALATED = 'Escalated', 'Escalated'
    COMPLETED = 'Completed', 'Completed'

# Defines priority levels for tasks to help with sorting and management.
class PriorityChoices(models.TextChoices):
    HIGH_PRIORITY = 'High Priority', 'High Priority'
    MEDIUM_HIGH_PRIORITY = 'Medium-High Priority', 'Medium-High Priority'
    MEDIUM_LOW_PRIORITY = 'Medium-Low Priority', 'Medium-Low Priority'
    LOW_PRIORITY = 'Low Priority', 'Low Priority'

# Represents an individual, potentially a contact for a company.
class Individual(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    company = models.ForeignKey('Company', related_name='individuals', on_delete=models.SET_NULL, null=True, blank=True)
    additional_details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# Represents a company, which may be associated with various individuals.
class Company(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    additional_details = models.TextField(blank=True)
    registration_number = models.CharField(max_length=100, unique=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    reference = models.ForeignKey(Individual, related_name='company_references', on_delete=models.SET_NULL, null=True, blank=True)
    owner = models.ForeignKey(Individual, related_name='company_owners', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name

    def clean(self):
        # Validates that reference and owner are not associated with a different company.
        if self.reference and self.reference.company and self.reference.company != self:
            raise ValidationError("Reference must not be associated with a different company")
        if self.owner and self.owner.company and self.owner.company != self:
            raise ValidationError("Owner must not be associated with a different company")

    def save(self, *args, **kwargs):
        self.clean()  # Calls clean method to perform custom validation before saving.
        super().save(*args, **kwargs)

# Represents a product that can be sold.
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    serial_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# Represents a sale transaction.
class Sale(models.Model):
    task = models.ForeignKey('Task', related_name='sales', on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, choices=StatusChoices.choices, default=StatusChoices.NEW)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name='sale_updates', on_delete=models.SET_NULL, null=True, blank=True)
    products = models.ManyToManyField(Product, through='SaleProduct', related_name='sales')

    def __str__(self):
        return f"Sale {self.id}"

# Intermediate model for Sale and Product to include quantity.
class SaleProduct(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.sale} - {self.product} (Quantity: {self.quantity})"
    
# Represents a general category for grouping tasks.
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

# Represents a more specific grouping within a Category for tasks.
class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategories', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
# Represents a task or job to be done, associated with various details like status and priority.
class Task(models.Model):
    user = models.ForeignKey(User, related_name='tasks', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField()
    contact = models.ForeignKey(Individual, related_name='tasks', on_delete=models.SET_NULL, null=True, blank=True)
    category = models.ForeignKey(Category, related_name='tasks', on_delete=models.SET_NULL, null=True)
    subcategory = models.ForeignKey(SubCategory, related_name='tasks', on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=50, choices=StatusChoices.choices, default=StatusChoices.NEW)
    priority = models.CharField(max_length=20, choices=PriorityChoices.choices, default=PriorityChoices.LOW_PRIORITY)
    regarding = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='related_tasks')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name='task_updates', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title
