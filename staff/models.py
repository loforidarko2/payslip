from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.conf import settings


class Employee(models.Model):
    """
    Casual employees who receive payslips.
    
    Casual employees who receive payslips.
    
    Employees can log into the system to view their personal payslips.
    Their accounts correspond to a CustomUser record with matching staff_id.
    Payslips are generated for these employees by HR staff.
    """
    # Keep old status field for backward compatibility
    STATUS_CHOICES = [
        ('CLEANER', 'Cleaner'),
        ('SECURITY', 'Security'),
        ('DRIVER', 'Driver'),
        ('ADMINISTRATIVE ASSISTANT', 'Administrative Assistant'),
        ('PHOTOGRAPHER', 'Photographer'),
        ('INTERN', 'Intern'),
        ('OTHER', 'Other'),
    ]
    
    # Primary identification
    staff_id = models.CharField(max_length=50, primary_key=True, verbose_name="Staff ID")
    name = models.CharField(max_length=200, verbose_name="Full Name")
    
    # Personal information
    date_of_hire = models.DateField(verbose_name="Date of Hire", null=True, blank=True)
    date_of_birth = models.DateField(verbose_name="Date of Birth", null=True, blank=True)
    
    # Old status field - kept for backward compatibility
    status = models.CharField(
        max_length=50, 
        choices=STATUS_CHOICES, 
        blank=True,
        null=True,
        verbose_name="Position/Status (Legacy)",
        help_text="Legacy status field - will be deprecated"
    )
    
    # New position - Dynamic from core_config
    position_config = models.ForeignKey(
        'core_config.EmployeePosition',
        on_delete=models.PROTECT,
        related_name='employees',
        null=True,
        blank=True,
        verbose_name="Position (Dynamic)",
        help_text="Employee position from dynamic configuration"
    )
    
    # Identification numbers
    ssnit_number = models.CharField(max_length=50, blank=True, verbose_name="SSNIT #")
    ghana_card = models.CharField(max_length=50, blank=True, verbose_name="Ghana Card")
    
    # Banking information
    bank_name = models.CharField(max_length=100, blank=True, verbose_name="Bank")
    bank_account = models.CharField(max_length=50, blank=True, verbose_name="Account Number")
    bank_branch = models.CharField(max_length=100, blank=True, verbose_name="Branch")
    
    # Contact information
    contact = models.CharField(max_length=50, blank=True, verbose_name="Contact/Phone")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    gender = models.CharField(max_length=10, blank=True, null=True, verbose_name="Gender")
    
    # Work details
    department = models.CharField(max_length=100, blank=True, verbose_name="Department")
    unit = models.CharField(max_length=100, blank=True, verbose_name="Unit")
    grade = models.CharField(max_length=50, blank=True, verbose_name="Grade")
    level = models.CharField(max_length=50, blank=True, verbose_name="Level")
    
    # Salary information
    monthly_salary = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Monthly Basic Salary"
    )
    
    # Employment status
    is_active = models.BooleanField(default=True, verbose_name="Active")
    separation_reason = models.TextField(blank=True, verbose_name="Separation Reason")
    separated_at = models.DateTimeField(null=True, blank=True, verbose_name="Separated At")
    separated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='separated_employees',
        verbose_name="Separated By",
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Employee"
        verbose_name_plural = "Employees"
    
    def __str__(self):
        return f"{self.name} ({self.staff_id})"
    
    def get_position_name(self):
        """Get position name from either field"""
        if self.position_config:
            return self.position_config.name
        elif self.status:
            return dict(self.STATUS_CHOICES).get(self.status, self.status)
        return "Unknown"

