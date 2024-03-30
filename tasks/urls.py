from django.urls import path
from . import views
from .views import CreateProductView, ProductListView, TaskListView, SaleListView, change_password, contact_settings, create_company, index, create_task, product_delete, settings_contact_list, task_detail, delete_task, sale_detail, create_sale, edit_sale, delete_sale, contact_list, contact_detail, settings_view, update_user_info

urlpatterns = [
    # Homepage URL
    path('', index, name='home'),
    
    # Dashboard URL, displaying an overview of the application
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Task-related URLs for listing, detail view, creation, and deletion
    path('tasks/', TaskListView.as_view(), name='task_list'),
    path('tasks/<int:task_id>/', task_detail, name='task_detail'),
    path('tasks/create_task/', create_task, name='create_task'),
    path('ajax/load-subcategories/', views.ajax_load_subcategories, name='ajax_load_subcategories'),
    path('tasks/edit_task/<int:task_id>/', views.edit_task, name='edit_task'),
    path('tasks/delete_task', delete_task, name='delete_task'),
    path('tasks/assign_to_me/<int:task_id>/', views.assign_to_me, name='assign_to_me'),

    # Sale-related URLs for listing, detail view, creation, and editing
    path('sales/', SaleListView.as_view(), name='sale_list'),
    path('sales/<int:sale_id>/', sale_detail, name='sale_detail'),
    path('sales/create_sale/<int:task_id>/', create_sale, name='create_sale'),
    path('sales/edit_sale/<int:sale_id>/', views.edit_sale, name='edit_sale'),
    path('sales/delete/', delete_sale, name='delete_sale'),
    
    # Contact-related URLs for listing and detailed views
    path('contacts/', contact_list, name='contact_list'),
    path('contacts/individuals/contact_detail/<int:id>/', contact_detail, {'contact_type': 'individual'}, name='individual_contact_detail'),
    path('contacts/companies/contact_detail/<int:id>/', contact_detail, {'contact_type': 'company'}, name='company_contact_detail'),

    # Product-related URLs for listing, detail view, and settings
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:id>/', views.product_detail, name='product_detail'),
    path('settings/products/<int:id>/', views.product_settings, name='product_settings'),
    path('delete_product/', product_delete, name='product_delete'),  
    path('product/create/', CreateProductView.as_view(), name='create_product'),

    # Settings and user information update URLs
    path('settings/', settings_view, name='settings'),
    path('update_user_info/', update_user_info, name='update_user_info'),
    path('settings/password/', change_password, name='change_password'),
    path('settings/contacts/', settings_contact_list, name='settings_contact_list'),
    path('settings/individuals/<int:id>/', contact_settings, {'contact_type': 'individual'}, name='individual_contact_settings'),
    path('settings/companies/<int:id>/', contact_settings, {'contact_type': 'company'}, name='company_contact_settings'),
    path('update_contact_info/<int:contact_id>/<contact_type>/', views.update_contact_info, name='update_contact_info'),
    path('contact/delete/<int:contact_id>/<str:contact_type>/', views.contact_delete, name='contact_delete'),

    # Company creation URL
    path('contacts/company/create/', create_company, name='create_company'),
]

