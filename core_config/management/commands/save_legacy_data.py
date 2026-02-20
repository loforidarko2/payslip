"""
Pre-migration script to save existing data to legacy fields
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import CustomUser
from staff.models import Employee
from payroll.models import Payslip


class Command(BaseCommand):
    help = 'Saves existing hardcoded data to legacy fields before migration'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Saving existing data to legacy fields...')
        
        # Save user roles to legacy_role
        self.stdout.write('\n=== Saving User Roles ===')
        users_updated = 0
        
        # This command should be run BEFORE the model changes are applied
        # So we need to check if the field exists
        try:
            # Check if we have the old 'role' CharField
            for user in CustomUser.objects.all():
                # Try to access the role field as a string (old way)
                if hasattr(user, 'role'):
                    role_value = getattr(user, 'role')
                    # Check if it's a string (not a ForeignKey)
                    if isinstance(role_value, str):
                        user.legacy_role = role_value
                        users_updated += 1
            
            if users_updated > 0:
                CustomUser.objects.bulk_update(CustomUser.objects.all(), ['legacy_role'])
                self.stdout.write(self.style.SUCCESS(f'Saved {users_updated} user roles'))
        except (AttributeError, TypeError, ValueError) as e:
            self.stdout.write(self.style.WARNING(f'Could not save user roles: {e}'))
        
        # Save employee status to legacy_status
        self.stdout.write('\n=== Saving Employee Statuses ===')
        employees_updated = 0
        
        try:
            for employee in Employee.objects.all():
                if hasattr(employee, 'status'):
                    status_value = getattr(employee, 'status')
                    if isinstance(status_value, str):
                        employee.legacy_status = status_value
                        employees_updated += 1
            
            if employees_updated > 0:
                Employee.objects.bulk_update(Employee.objects.all(), ['legacy_status'])
                self.stdout.write(self.style.SUCCESS(f'Saved {employees_updated} employee statuses'))
        except (AttributeError, TypeError, ValueError) as e:
            self.stdout.write(self.style.WARNING(f'Could not save employee statuses: {e}'))
        
        # Save payslip approval statuses
        self.stdout.write('\n=== Saving Payslip Approval Statuses ===')
        payslips_updated = 0
        
        try:
            for payslip in Payslip.objects.all():
                if hasattr(payslip, 'approval_status'):
                    status_value = getattr(payslip, 'approval_status')
                    if isinstance(status_value, str):
                        payslip.legacy_approval_status = status_value
                        payslips_updated += 1
            
            if payslips_updated > 0:
                Payslip.objects.bulk_update(Payslip.objects.all(), ['legacy_approval_status'])
                self.stdout.write(self.style.SUCCESS(f'Saved {payslips_updated} payslip statuses'))
        except (AttributeError, TypeError, ValueError) as e:
            self.stdout.write(self.style.WARNING(f'Could not save payslip statuses: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\nLegacy data saved successfully!'))
        self.stdout.write('\nYou can now run: python manage.py migrate')
