"""
Data migration to populate initial configuration data
"""
from django.core.management.base import BaseCommand
from core_config.models import (
    UserRole, EmployeePosition, Department, Unit,
    Grade, Level, PaymentType, DeductionType, ApprovalStatus
)


class Command(BaseCommand):
    help = 'Populates initial configuration data from existing hardcoded values'

    def handle(self, *args, **kwargs):
        self.stdout.write('Populating initial configuration data...')
        
        # Create User Roles
        self.stdout.write('Creating user roles...')
        roles_data = [
            {
                'code': 'admin',
                'name': 'Admin',
                'description': 'System administrator with full access',
                'can_manage_users': True,
                'can_manage_employees': True,
                'can_generate_payslips': True,
                'can_approve_payslips': True,
                'can_view_all_payslips': True,
                'can_edit_configuration': True,
            },
            {
                'code': 'hr_admin',
                'name': 'HR Admin',
                'description': 'HR administrator',
                'can_manage_users': True,
                'can_manage_employees': True,
                'can_generate_payslips': False,
                'can_approve_payslips': False,
                'can_view_all_payslips': True,
                'can_edit_configuration': False,
            },
            {
                'code': 'finance',
                'name': 'Finance',
                'description': 'Finance officer responsible for generation and approval',
                'can_manage_users': False,
                'can_manage_employees': True,
                'can_generate_payslips': True,
                'can_approve_payslips': True,
                'can_view_all_payslips': True,
                'can_edit_configuration': False,
            },
            {
                'code': 'staff',
                'name': 'Staff',
                'description': 'Regular staff user',
                'can_manage_users': False,
                'can_manage_employees': False,
                'can_generate_payslips': False,
                'can_approve_payslips': False,
                'can_view_all_payslips': False,
                'can_edit_configuration': False,
            },
        ]
        
        for role_data in roles_data:
            role, created = UserRole.objects.get_or_create(
                code=role_data['code'],
                defaults=role_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created role: {role.name}'))
            else:
                self.stdout.write(f'  Role already exists: {role.name}')
        
        # Create Employee Positions
        self.stdout.write('Creating employee positions...')
        positions_data = [
            {'code': 'CLEANER', 'name': 'Cleaner'},
            {'code': 'SECURITY', 'name': 'Security'},
            {'code': 'DRIVER', 'name': 'Driver'},
            {'code': 'ADMINISTRATIVE_ASSISTANT', 'name': 'Administrative Assistant'},
            {'code': 'PHOTOGRAPHER', 'name': 'Photographer'},
            {'code': 'INTERN', 'name': 'Intern'},
            {'code': 'OTHER', 'name': 'Other'},
        ]
        
        for pos_data in positions_data:
            pos, created = EmployeePosition.objects.get_or_create(
                code=pos_data['code'],
                defaults=pos_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created position: {pos.name}'))
            else:
                self.stdout.write(f'  Position already exists: {pos.name}')
        
        # Create Approval Statuses
        self.stdout.write('Creating approval statuses...')
        statuses_data = [
            {
                'code': 'pending',
                'name': 'Pending',
                'description': 'Awaiting approval',
                'is_approved_state': False,
                'is_rejected_state': False,
            },
            {
                'code': 'approved',
                'name': 'Approved',
                'description': 'Approved and ready for payment',
                'is_approved_state': True,
                'is_rejected_state': False,
            },
            {
                'code': 'rejected',
                'name': 'Rejected',
                'description': 'Rejected and needs revision',
                'is_approved_state': False,
                'is_rejected_state': True,
            },
        ]
        
        for status_data in statuses_data:
            status, created = ApprovalStatus.objects.get_or_create(
                code=status_data['code'],
                defaults=status_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created status: {status.name}'))
            else:
                self.stdout.write(f'  Status already exists: {status.name}')
        
        # Create default Payment Types
        self.stdout.write('Creating payment types...')
        payment_types_data = [
            {'code': 'BASIC_SALARY', 'name': 'Basic Salary', 'is_taxable': True},
            {'code': 'OVERTIME', 'name': 'Overtime', 'is_taxable': True},
            {'code': 'ALLOWANCE', 'name': 'General Allowance', 'is_taxable': True},
            {'code': 'BONUS', 'name': 'Bonus', 'is_taxable': True},
        ]
        
        for payment_data in payment_types_data:
            payment, created = PaymentType.objects.get_or_create(
                code=payment_data['code'],
                defaults=payment_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created payment type: {payment.name}'))
            else:
                self.stdout.write(f'  Payment type already exists: {payment.name}')
        
        # Create default Deduction Types
        self.stdout.write('Creating deduction types...')
        deduction_types_data = [
            {'code': 'SSNIT', 'name': 'SSNIT (5.5%)', 'is_statutory': True, 'default_rate_percent': 5.5},
            {'code': 'TIER2', 'name': 'Tier 2 (3.5%)', 'is_statutory': True, 'default_rate_percent': 3.5},
            {'code': 'INCOME_TAX', 'name': 'Income Tax', 'is_statutory': True},
            {'code': 'OTHER', 'name': 'Other Deductions', 'is_statutory': False},
        ]
        
        for deduction_data in deduction_types_data:
            deduction, created = DeductionType.objects.get_or_create(
                code=deduction_data['code'],
                defaults=deduction_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Created deduction type: {deduction.name}'))
            else:
                self.stdout.write(f'  Deduction type already exists: {deduction.name}')
        
        self.stdout.write(self.style.SUCCESS('\nConfiguration data populated successfully!'))
        self.stdout.write('\nNote: Departments, Units, Grades, and Levels will be automatically')
        self.stdout.write('created from existing employee data during the next migration step.')
