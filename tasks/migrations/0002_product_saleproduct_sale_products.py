# Generated by Django 4.2.9 on 2024-02-05 16:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='SaleProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.product')),
                ('sale', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.sale')),
            ],
        ),
        migrations.AddField(
            model_name='sale',
            name='products',
            field=models.ManyToManyField(related_name='sales', through='tasks.SaleProduct', to='tasks.product'),
        ),
    ]
