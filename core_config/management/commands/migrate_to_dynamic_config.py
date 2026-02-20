"""
Data migration to migrate existing Users, Employees, and Payslips to use dynamic configuration
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import CustomUser
from staff.models import Employee
from payroll.models import Payslip
from core_config.models import UserRole, EmployeePosition, ApprovalStatus


class Command(BaseCommand):
    help = 'Migrates existing data to use dynamic configuration models'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write('Starting data migration...')
        
        # Migrate User Roles
        self.stdout.write('\n=== Migrating User Roles ===')
        role_mapping = {
            'admin': 'admin',
            'hr_admin': 'hr_admin',
            'hr_staff': 'finance',
            'finance': 'finance',
            'staff': 'staff',
        }
        
        users_migrated = 0
        users_with_legacy_roles = CustomUser.objects.filter(legacy_role__isnull=False)
        
        for user in users_with_legacy_roles:
            if user.legacy_role in role_mapping:
                try:
                    role = UserRole.objects.get(code=role_mapping[user.legacy_role])
                    user.role = role
                    user.save(update_fields=['role'])
                    users_migrated += 1
                    self.stdout.write(f'  Migrated user {user.username}: {user.legacy_role} -> {role.name}')
                except UserRole.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  Role not found for {user.username}: {user.legacy_role}'
                    ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'  Unknown legacy role for {user.username}: {user.legacy_role}'
                ))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {users_migrated} users'))
        
        # Migrate Employee Positions
        self.stdout.write('\n=== Migrating Employee Positions ===')
        position_mapping = {
            'CLEANER': 'CLEANER',
            'SECURITY': 'SECURITY',
            'DRIVER': 'DRIVER',
            'ADMINISTRATIVE ASSISTANT': 'ADMINISTRATIVE_ASSISTANT',
            'PHOTOGRAPHER': 'PHOTOGRAPHER',
            'INTERN': 'INTERN',
            'OTHER': 'OTHER',
        }
        
        employees_migrated = 0
        employees_with_legacy_status = Employee.objects.filter(legacy_status__isnull=False)
        
        for employee in employees_with_legacy_status:
            if employee.legacy_status in position_mapping:
                try:
                    position = EmployeePosition.objects.get(code=position_mapping[employee.legacy_status])
                    employee.position = position
                    employee.save(update_fields=['position'])
                    employees_migrated += 1
                    self.stdout.write(f'  Migrated employee {employee.name}: {employee.legacy_status} -> {position.name}')
                except EmployeePosition.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  Position not found for {employee.name}: {employee.legacy_status}'
                    ))
            else:
                # Try to find or create a matching position
                self.stdout.write(self.style.WARNING(
                    f'  Unknown legacy status for {employee.name}: {employee.legacy_status}'
                ))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {employees_migrated} employees'))
        
        # Migrate Payslip Approval Statuses
        self.stdout.write('\n=== Migrating Payslip Approval Statuses ===')
        status_mapping = {
            'pending': 'pending',
            'approved': 'approved',
            'rejected': 'rejected',
        }
        
        payslips_migrated = 0
        payslips_with_legacy_status = Payslip.objects.filter(legacy_approval_status__isnull=False)
        
        for payslip in payslips_with_legacy_status:
            if payslip.legacy_approval_status in status_mapping:
                try:
                    status = ApprovalStatus.objects.get(code=status_mapping[payslip.legacy_approval_status])
                    payslip.approval_status = status
                    payslip.save(update_fields=['approval_status'])
                    payslips_migrated += 1
                except ApprovalStatus.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'  Status not found for payslip {payslip.id}: {payslip.legacy_approval_status}'
                    ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'  Unknown legacy status for payslip {payslip.id}: {payslip.legacy_approval_status}'
                ))
        
        self.stdout.write(self.style.SUCCESS(f'Migrated {payslips_migrated} payslips'))
        
        self.stdout.write(self.style.SUCCESS('\nData migration completed successfully!'))
