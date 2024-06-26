# Generated by Django 4.2.9 on 2024-02-15 11:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_alter_sale_status_alter_task_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='company_owners', to='tasks.individual'),
        ),
        migrations.AddField(
            model_name='company',
            name='reference',
            field=models.ForeignKey(default=1245, on_delete=django.db.models.deletion.CASCADE, related_name='company_references', to='tasks.individual'),
            preserve_default=False,
        ),
    ]
