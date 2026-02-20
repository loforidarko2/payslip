from django.contrib import admin
from .models import Payslip, PayslipLineItem, SystemConfiguration


class PayslipLineItemInline(admin.TabularInline):
    """Inline for line items within payslip"""
    model = PayslipLineItem
    extra = 0
    fields = ['item_type', 'payment_type', 'deduction_type', 'nature', 'hours_or_amount', 'rate_percent', 'balance', 'order']


@admin.register(Payslip)
class PayslipAdmin(admin.ModelAdmin):
    """Admin interface for Payslip"""
    list_display = [
        'employee', 'month_year', 'gross_salary', 'net_salary',
        'approval_status', 'status_config', 'generated_at', 'generated_by'
    ]
    list_filter = ['approval_status', 'status_config', 'generated_at', 'month_year']
    search_fields = ['employee__name', 'employee__staff_id', 'month_year']
    readonly_fields = ['generated_at', 'last_modified_at', 'total_deductions']
    inlines = [PayslipLineItemInline]
    
    fieldsets = (
        ('Employee & Period', {
            'fields': ('employee', 'month_year', 'agency', 'district')
        }),
        ('Snapshot - Employee Details', {
            'fields': ('department', 'unit', 'grade', 'level')
        }),
        ('Salary Components', {
            'fields': ('basic_salary', 'allowances', 'gross_salary')
        }),
        ('Deductions', {
            'fields': ('ssnit_deduction', 'tier2_deduction', 'income_tax', 'other_deductions')
        }),
        ('Net Salary', {
            'fields': ('net_salary', 'payment_mode')
        }),
        ('Approval', {
            'fields': ('approval_status', 'status_config', 'approved_by', 'approved_at')
        }),
        ('Metadata', {
            'fields': ('generated_by', 'generated_at', 'last_modified_by', 'last_modified_at')
        }),
    )


@admin.register(PayslipLineItem)
class PayslipLineItemAdmin(admin.ModelAdmin):
    """Admin interface for PayslipLineItem"""
    list_display = ['payslip', 'item_type', 'payment_type', 'deduction_type', 'nature', 'balance', 'order']
    list_filter = ['item_type', 'payment_type', 'deduction_type']
    search_fields = ['payslip__employee__name', 'nature']


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for SystemConfiguration"""
    fieldsets = (
        ('Agency Information', {
            'fields': ('agency_name', 'default_district', 'agency_logo', 'address', 'phone', 'email')
        }),
        ('Financial Rates', {
            'fields': ('ssnit_rate', 'tier2_rate')
        }),
    )
