from django.urls import path
from . import views

app_name = 'staff'

urlpatterns = [
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<path:staff_id>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<path:staff_id>/delete/', views.employee_delete, name='employee_delete'),
    path('employees/import/', views.import_employees, name='import_employees'),
]
