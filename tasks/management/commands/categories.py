from django.core.management.base import BaseCommand, CommandError
from tasks.models import Category, SubCategory

class Command(BaseCommand):
    help = 'Adds categories and subcategories to the database'

    def handle(self, *args, **options):
        categories_and_subcategories = {
            "Information/General": [
                "Request Information",
                "Update Personal Information",
                "General Feedback"
            ],
            "Customer Complaint": [
                "Product Issues",
                "Service Dissatisfaction",
                "Billing Disputes",
                "Delivery Problems"
            ],
            "Sales": [
                "Lead Inquiry",
                "Quote Request",
                "Order Placement"
            ],
            "Technical Support": [
                "Troubleshooting",
                "Warranty Claims",
                "Product Returns"
            ],
            "Account Management": [
                "Account Setup",
                "Account Review",
                "Subscription Management"
            ],
            "Payment and Billing": [
                "Payment Processing",
                "Invoice Inquiries",
                "Refund Requests",
                "Payment Arrangements"
            ],
        }

        for category_name, subcategories in categories_and_subcategories.items():
            category, created = Category.objects.get_or_create(name=category_name)
            for subcategory_name in subcategories:
                SubCategory.objects.get_or_create(
                    category=category,
                    name=subcategory_name
                )
            self.stdout.write(self.style.SUCCESS(f"Successfully added category '{category_name}' with {len(subcategories)} sub-categories."))