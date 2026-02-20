from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    System users and employees who use the application.
    
    System users (admins, HR staff) manage the system, while employees 
    can log in to view their payslips.
    """
    # Keep old role field for backward compatibility
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('hr_admin', 'HR Admin'),
        ('finance', 'Finance'),
    ]
    
    role = models.CharField(
        max_length=15, 
        choices=ROLE_CHOICES, 
        blank=True,
        null=True,
        help_text="Legacy role field - will be deprecated"
    )
    
    # New dynamic role using ForeignKey to core_config.UserRole
    role_config = models.ForeignKey(
        'core_config.UserRole',
        on_delete=models.PROTECT,
        related_name='users',
        null=True,
        blank=True,
        verbose_name="Role (Dynamic)",
        help_text="User's role in the system (dynamic configuration)"
    )
    
    # Note: staff_id is kept for backward compatibility and system user identification
    # It is NOT linked to the Employee model (employees cannot log in)
    staff_id = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        help_text="System User ID (distinct from Casual Employee Staff ID)"
    )
    
    # Organizational attributes for system users
    # (Note: These are for organizational purposes only, NOT linked to Employee records)
    department = models.CharField(max_length=100, blank=True, verbose_name="Department", help_text="Department this system user belongs to")
    unit = models.CharField(max_length=100, blank=True, verbose_name="Unit", help_text="Organizational unit")
    grade = models.CharField(max_length=50, blank=True, verbose_name="Grade", help_text="System user grade level")
    level = models.CharField(max_length=50, blank=True, verbose_name="Level", help_text="System user level")
    
    must_change_password = models.BooleanField(
        default=False, 
        help_text="If True, user will be prompted to change password on login"
    )
    
    def __str__(self):
        if self.role_config:
            role_name = self.role_config.name
        elif self.role:
            role_name = dict(self.ROLE_CHOICES).get(self.role, 'Unknown')
        else:
            role_name = 'No Role'
        return f"{self.username} ({role_name})"
    
    def get_role_code(self):
        """Get the role code from either field"""
        if self.role_config:
            return self.role_config.code
        return self.role
    
    def is_admin(self):
        """Check if user is an admin"""
        return self.get_role_code() == 'admin'
    
    def is_hr_admin(self):
        """Check if user is an HR admin"""
        return self.get_role_code() == 'hr_admin'
        
    def is_hr_staff(self):
        """Backward-compatible alias for finance role"""
        return self.is_finance()

    def is_finance(self):
        """Check if user is finance staff"""
        return self.get_role_code() == 'finance'
    
    def is_staff_role(self):
        """Check if user is regular staff"""
        return self.get_role_code() == 'staff'
    
    # Permission methods based on role
    def can_manage_users(self):
        """Can create/edit/delete users"""
        if self.role_config:
            return self.role_config.can_manage_users
        return self.role in ['admin', 'hr_admin']
    
    def can_manage_employees(self):
        """Can create/edit/delete employees"""
        if self.role_config:
            return self.role_config.can_manage_employees
        return self.role in ['admin', 'hr_admin', 'finance']
    
    def can_generate_payslips(self):
        """Can generate payslips"""
        if self.role_config:
            return self.role_config.can_generate_payslips
        return self.role in ['admin', 'finance']
    
    def can_approve_payslips(self):
        """Can approve/reject payslips"""
        if self.role_config:
            return self.role_config.can_approve_payslips
        return self.role in ['admin', 'finance']
    
    def can_view_all_payslips(self):
        """Can view all payslips"""
        if self.role_config:
            return self.role_config.can_view_all_payslips
        return self.role in ['admin', 'hr_admin', 'finance']
    
    def can_edit_configuration(self):
        """Can edit system configuration"""
        if self.role_config:
            return self.role_config.can_edit_configuration
        return self.role == 'admin'

