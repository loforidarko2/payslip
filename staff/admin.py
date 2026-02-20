from django.contrib import admin
from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    Admin interface for casual employees who receive payslips.
    NOTE: Employees cannot log into the system - they are data records only.
    """
    list_display = [
        'staff_id', 'name', 'status', 'position_config', 'department',
        'monthly_salary', 'is_active', 'separated_at', 'date_of_hire'
    ]
    list_filter = ['is_active', 'position_config', 'status', 'department', 'gender']
    search_fields = ['staff_id', 'name', 'email', 'contact', 'ghana_card', 'ssnit_number']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Identification', {
            'fields': ('staff_id', 'name', 'date_of_birth', 'gender')
        }),
        ('Employment Details', {
            'fields': (
                'status', 'position_config', 'date_of_hire', 'is_active',
                'separation_reason', 'separated_at', 'separated_by', 'monthly_salary'
            )
        }),
        ('Organizational Details', {
            'fields': ('department', 'unit', 'grade', 'level')
        }),
        ('Contact Information', {
            'fields': ('email', 'contact')
        }),
        ('Identification Numbers', {
            'fields': ('ghana_card', 'ssnit_number')
        }),
        ('Banking Information', {
            'fields': ('bank_name', 'bank_account', 'bank_branch')
        }),
    )
