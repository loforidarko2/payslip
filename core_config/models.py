from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class UserRole(models.Model):
    """Dynamic user roles for system access"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the role")
    name = models.CharField(max_length=100, help_text="Display name for the role")
    description = models.TextField(blank=True, help_text="Description of this role's purpose")
    
    # Permissions flags
    can_manage_users = models.BooleanField(default=False, help_text="Can create/edit/delete users")
    can_manage_employees = models.BooleanField(default=False, help_text="Can create/edit/delete employees")
    can_generate_payslips = models.BooleanField(default=False, help_text="Can generate payslips")
    can_approve_payslips = models.BooleanField(default=False, help_text="Can approve/reject payslips")
    can_view_all_payslips = models.BooleanField(default=False, help_text="Can view all payslips")
    can_edit_configuration = models.BooleanField(default=False, help_text="Can edit system configuration")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
    
    def __str__(self):
        return self.name


class EmployeePosition(models.Model):
    """Dynamic employee positions/job titles"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the position")
    name = models.CharField(max_length=100, help_text="Display name for the position")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Employee Position"
        verbose_name_plural = "Employee Positions"
    
    def __str__(self):
        return self.name


class Department(models.Model):
    """Dynamic departments"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the department")
    name = models.CharField(max_length=100, help_text="Department name")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Department"
        verbose_name_plural = "Departments"
    
    def __str__(self):
        return self.name


class Unit(models.Model):
    """Organizational units"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the unit")
    name = models.CharField(max_length=100, help_text="Unit name")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Unit"
        verbose_name_plural = "Units"
    
    def __str__(self):
        return self.name


class Grade(models.Model):
    """Employee grades"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the grade")
    name = models.CharField(max_length=100, help_text="Grade name")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
    
    def __str__(self):
        return self.name


class Level(models.Model):
    """Employee levels"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the level")
    name = models.CharField(max_length=100, help_text="Level name")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Level"
        verbose_name_plural = "Levels"
    
    def __str__(self):
        return self.name


class PaymentType(models.Model):
    """Types of payments/allowances that can be added to payslips"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the payment type")
    name = models.CharField(max_length=200, help_text="Payment type name")
    description = models.TextField(blank=True)
    is_taxable = models.BooleanField(default=True, help_text="Is this payment subject to income tax?")
    default_rate_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Default rate % (if applicable)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Payment Type"
        verbose_name_plural = "Payment Types"
    
    def __str__(self):
        return self.name


class DeductionType(models.Model):
    """Types of deductions that can be applied to payslips"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the deduction type")
    name = models.CharField(max_length=200, help_text="Deduction type name")
    description = models.TextField(blank=True)
    is_statutory = models.BooleanField(default=False, help_text="Is this a statutory deduction (SSNIT, Tax, etc.)?")
    default_rate_percent = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Default rate % (if applicable)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Deduction Type"
        verbose_name_plural = "Deduction Types"
    
    def __str__(self):
        return self.name


class ApprovalStatus(models.Model):
    """Dynamic approval statuses for payslips"""
    code = models.CharField(max_length=50, unique=True, help_text="Internal code for the status")
    name = models.CharField(max_length=100, help_text="Display name for the status")
    description = models.TextField(blank=True)
    is_approved_state = models.BooleanField(default=False, help_text="Does this status mean approved?")
    is_rejected_state = models.BooleanField(default=False, help_text="Does this status mean rejected?")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = "Approval Status"
        verbose_name_plural = "Approval Statuses"
    
    def __str__(self):
        return self.name
