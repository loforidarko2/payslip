from django.db import models
from django.conf import settings
from staff.models import Employee

MONTH_YEAR_FORMAT = '%b-%Y'
SYSTEM_CONFIGURATION_LABEL = "System Configuration"


class Payslip(models.Model):
    """Payslip model with approval workflow"""
    # Keep old approval status field for backward compatibility
    APPROVAL_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    # Relationships
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payslips')
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='generated_payslips')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payslips')
    
    # Period information
    month_year = models.CharField(max_length=20, verbose_name="Month/Year", help_text="e.g., Jan-2026")
    
    # Agency information
    agency = models.CharField(max_length=200, blank=True, verbose_name="Agency")
    district = models.CharField(max_length=200, blank=True, verbose_name="District")
    
    # Snapshot information (Employee details at time of generation)
    department = models.CharField(max_length=100, blank=True, verbose_name="Department")
    unit = models.CharField(max_length=100, blank=True, verbose_name="Unit")
    grade = models.CharField(max_length=50, blank=True, verbose_name="Grade")
    level = models.CharField(max_length=50, blank=True, verbose_name="Level")
    
    # Salary components
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Basic Salary")
    allowances = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Allowances")
    gross_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Gross Salary")
    
    # Deductions
    ssnit_deduction = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="SSNIT (5.5%)")
    tier2_deduction = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Tier 2 (3.5%)")
    income_tax = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Income Tax")
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Other Deductions")
    
    # Net salary
    net_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Net Salary")
    
    # Payment details
    payment_mode = models.CharField(max_length=200, blank=True, verbose_name="Payment Mode")
    
    # Old approval workflow - kept for backward compatibility
    approval_status = models.CharField(
        max_length=10, 
        choices=APPROVAL_STATUS_CHOICES, 
        blank=True,
        null=True,
        verbose_name="Approval Status (Legacy)",
        help_text="Legacy approval status field - will be deprecated"
    )
    
    # New approval workflow - Dynamic
    status_config = models.ForeignKey(
        'core_config.ApprovalStatus',
        on_delete=models.PROTECT,
        related_name='payslips',
        null=True,
        blank=True,
        verbose_name="Approval Status (Dynamic)",
        help_text="Approval status from dynamic configuration"
    )
    
    approved_at = models.DateTimeField(null=True, blank=True, verbose_name="Approved At")
    
    # Metadata
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name="Generated At")
    last_modified_at = models.DateTimeField(auto_now=True, verbose_name="Last Modified At")
    last_modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='modified_payslips',
        verbose_name="Last Modified By"
    )
    
    class Meta:
        ordering = ['-generated_at']
        verbose_name = "Payslip"
        verbose_name_plural = "Payslips"
        unique_together = ['employee', 'month_year']
    
    def __str__(self):
        if self.status_config:
            status_name = self.status_config.name
        elif self.approval_status:
            status_name = dict(self.APPROVAL_STATUS_CHOICES).get(self.approval_status, 'Unknown')
        else:
            status_name = 'No Status'
        return f"Payslip for {self.employee.name} - {self.month_year} ({status_name})"
    
    def total_deductions(self):
        return self.ssnit_deduction + self.tier2_deduction + self.income_tax + self.other_deductions
    
    def is_approved(self):
        if self.status_config:
            return self.status_config.is_approved_state
        return self.approval_status == 'approved'
    
    @property
    def period(self):
        """Calculate period range from month_year (e.g., 'Feb-2026' -> '01-FEB-2026 TO 28-FEB-2026')"""
        from datetime import datetime
        import calendar
        try:
            month_dt = datetime.strptime(self.month_year, MONTH_YEAR_FORMAT)
            last_day = calendar.monthrange(month_dt.year, month_dt.month)[1]
            return f"01-{month_dt.strftime(MONTH_YEAR_FORMAT).upper()} TO {last_day}-{month_dt.strftime(MONTH_YEAR_FORMAT).upper()}"
        except (TypeError, ValueError):
            return self.month_year



class PayslipLineItem(models.Model):
    """Detailed line items for payslip payments and deductions"""
    ITEM_TYPE_CHOICES = [
        ('payment', 'Payment'),
        ('deduction', 'Deduction'),
    ]
    
    # Relationships
    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='line_items')
    
    # Line item type and references to dynamic types
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    
    # References to dynamic payment/deduction types
    payment_type = models.ForeignKey(
        'core_config.PaymentType',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='line_items',
        help_text="Payment type (if this is a payment)"
    )
    
    deduction_type = models.ForeignKey(
        'core_config.DeductionType',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='line_items',
        help_text="Deduction type (if this is a deduction)"
    )
    
    # Detailed fields
    nature = models.CharField(max_length=200, verbose_name="Nature/Description")
    hours_or_amount = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Hours/Original Amount"
    )
    rate_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Rate %"
    )
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name="Balance/Amount"
    )
    
    # Ordering
    order = models.IntegerField(default=0, help_text="Display order")
    
    class Meta:
        ordering = ['order', 'id']
        verbose_name = "Payslip Line Item"
        verbose_name_plural = "Payslip Line Items"
    
    def __str__(self):
        if self.item_type == 'payment' and self.payment_type:
            return f"Payment: {self.payment_type.name} - GHS {self.balance}"
        elif self.item_type == 'deduction' and self.deduction_type:
            return f"Deduction: {self.deduction_type.name} - GHS {self.balance}"
        else:
            return f"{self.get_item_type_display()}: {self.nature} - GHS {self.balance}"


class PayslipAudit(models.Model):
    """Audit trail for payslip edits and reverts"""
    ACTION_CHOICES = [
        ('edit', 'Edit'),
        ('revert', 'Revert'),
    ]

    payslip = models.ForeignKey(Payslip, on_delete=models.CASCADE, related_name='audit_entries')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    old_status = models.CharField(max_length=10, blank=True, null=True)
    new_status = models.CharField(max_length=10, blank=True, null=True)
    reason = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payslip_audits'
    )
    performed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-performed_at']
        verbose_name = "Payslip Audit Entry"
        verbose_name_plural = "Payslip Audit Entries"

    def __str__(self):
        return f"{self.get_action_display()} - Payslip {self.payslip_id}"



class SystemConfiguration(models.Model):
    """Global system settings stored in the database"""
    agency_name = models.CharField(max_length=200, default="National Ambulance Service")
    default_district = models.CharField(max_length=200, default="Accra Metropolitan Assembly")
    
    # Financial Rates
    ssnit_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.5, help_text="Default SSNIT Rate (%)")
    tier2_rate = models.DecimalField(max_digits=5, decimal_places=2, default=3.5, help_text="Default Tier 2 Rate (%)")
    
    # Logo
    agency_logo = models.ImageField(upload_to='agency_logos/', null=True, blank=True)
    
    # Contact Info for Payslip
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = SYSTEM_CONFIGURATION_LABEL
        verbose_name_plural = SYSTEM_CONFIGURATION_LABEL

    def __str__(self):
        return SYSTEM_CONFIGURATION_LABEL

    @classmethod
    def get_settings(cls):
        """Helper to get the singleton configuration object"""
        obj, created = cls.objects.get_or_create(id=1)
        return obj
