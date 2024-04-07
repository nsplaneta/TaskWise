from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from tasks.models import Company, Individual, Task, Product, Sale, SaleProduct, StatusChoices, Category, SubCategory
from django.db.utils import IntegrityError
import random
import uuid
from faker import Faker

fake = Faker()

class Command(BaseCommand):
    help = 'Populates the database with initial data'

    def handle(self, *args, **kwargs):
        # Create some Users and assign them to random groups
        groups = ['Managers', 'Sales Advisors', 'Logistic Operators', 'Testers', 'Marketing']
        for i in range(5):
            username = fake.user_name()
            email = fake.email()
            user = User.objects.create_user(username, email, 'password')
            group = random.choice(groups)
            user.groups.add(Group.objects.get_or_create(name=group)[0])
            self.stdout.write(f'User {username} created and added to group {group}')

        # Ensure unique Individuals creation
        existing_emails = set(Individual.objects.values_list('email', flat=True))
        for _ in range(50):
            while True:
                email = fake.email()
                if email not in existing_emails:
                    existing_emails.add(email)
                    individual = Individual.objects.create(
                        name=fake.name(),
                        email=email,
                        phone=fake.phone_number(),
                        address=fake.address()
                    )
                    break

        # Get a list of all individuals
        individuals = list(Individual.objects.all())

        # Randomly pair individuals to ensure unique assignments
        while individuals:
            if len(individuals) < 2:
                break  # Stop if there aren't enough individuals left for pairing
            reference, owner = random.sample(individuals, 2)

            # Create a company with these individuals
            company = Company.objects.create(
                name=fake.company(),
                email=fake.company_email(),
                phone=fake.phone_number(),
                address=fake.address(),
                additional_details='Details: ' + fake.paragraph(),
                registration_number=fake.bothify(text='Reg####Number'),
                reference=reference,
                owner=owner
            )

            # Assign the company to the corresponding individual
            reference.company = company
            reference.save()
            owner.company = company
            owner.save()

            # Remove the selected individuals from the list
            individuals.remove(reference)
            if reference != owner:  # Ensure not to double-remove if randomly chosen the same
                individuals.remove(owner)

            # Create 5 Tasks for this company
            tasks_list = []
            for _ in range(5):  # Assuming you want 10 tasks with unique titles for each company
                unique_id = uuid.uuid4().hex[:4].upper()
                second_unique_id = uuid.uuid4().hex[:4].upper()
                task_title = f"TASK-{unique_id}-{second_unique_id}"  # Generate unique title inside loop
                task = Task(
                    user=random.choice(User.objects.all()),
                    title=task_title,
                    description=fake.text(),
                    contact=random.choice([reference, owner]),
                    category=random.choice(Category.objects.all()),
                    subcategory=random.choice(SubCategory.objects.all()),
                    status=random.choice([status[0] for status in StatusChoices.choices])
                )
                tasks_list.append(task)
            Task.objects.bulk_create(tasks_list)

        # Create 50 Products with unique serial numbers
        products_list = []
        for i in range(50):
            serial_number = fake.bothify(text='????-####-####', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            while serial_number in [p.serial_number for p in products_list]:  # Ensure unique serial numbers
                serial_number = fake.bothify(text='????-####-####', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
            products_list.append(Product(
                name=fake.word().capitalize() + ' Product',
                description=fake.text(),
                price=random.uniform(10.0, 1000.0),
                serial_number=serial_number
            ))
        Product.objects.bulk_create(products_list)

        # Create 50 Sales
        sales_list = [
            Sale(
                task=random.choice(Task.objects.all()),
                status=random.choice([status[0] for status in StatusChoices.choices])
            ) for _ in range(50)
        ]
        Sale.objects.bulk_create(sales_list)

        # Create multiple SaleProduct connections
        for sale in Sale.objects.all():
            selected_products = random.sample(list(Product.objects.all()), min(Product.objects.count(), 5))
            for product in selected_products:
                SaleProduct.objects.create(
                    sale=sale,
                    product=product,
                    quantity=random.randint(1, 10)
                )

        self.stdout.write(self.style.SUCCESS('Successfully populated database with initial data'))
