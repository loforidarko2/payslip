from django.contrib import admin
from .models import (
    UserRole, EmployeePosition, Department, Unit,
    Grade, Level, PaymentType, DeductionType, ApprovalStatus
)


@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'can_manage_users', 'can_generate_payslips', 'can_approve_payslips', 'is_active']
    list_filter = ['is_active', 'can_manage_users', 'can_generate_payslips', 'can_approve_payslips']
    search_fields = ['name', 'code', 'description']
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Permissions', {
            'fields': (
                'can_manage_users',
                'can_manage_employees',
                'can_generate_payslips',
                'can_approve_payslips',
                'can_view_all_payslips',
                'can_edit_configuration'
            )
        }),
    )


@admin.register(EmployeePosition)
class EmployeePositionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'code', 'description']


@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_taxable', 'default_rate_percent', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_taxable']
    search_fields = ['name', 'code', 'description']


@admin.register(DeductionType)
class DeductionTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_statutory', 'default_rate_percent', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_statutory']
    search_fields = ['name', 'code', 'description']


@admin.register(ApprovalStatus)
class ApprovalStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'is_approved_state', 'is_rejected_state', 'is_active', 'created_at']
    list_filter = ['is_active', 'is_approved_state', 'is_rejected_state']
    search_fields = ['name', 'code', 'description']
