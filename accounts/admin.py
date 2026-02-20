from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for system users (NOT employees)"""
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'role_config', 'is_active', 'is_staff']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'role', 'role_config']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Organization', {
            'fields': ('role', 'role_config', 'department', 'unit', 'grade', 'level'),
            'description': 'System user role and organizational information (NOT employee data)'
        }),
        ('Password Management', {
            'fields': ('must_change_password',)
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role & Organization', {
            'fields': ('role', 'role_config', 'department', 'unit', 'grade', 'level')
        }),
    )
