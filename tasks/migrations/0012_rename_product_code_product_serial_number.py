# Generated by Django 4.2.9 on 2024-02-17 15:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0011_alter_product_product_code'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='product_code',
            new_name='serial_number',
        ),
    ]
