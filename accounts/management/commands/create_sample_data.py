"""
Management command to create sample users and data for testing
"""
from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from staff.models import Employee
from payroll.models import Payslip
from decimal import Decimal
from datetime import date
from payroll.utils import calculate_ssnit, calculate_tier2, calculate_income_tax


class Command(BaseCommand):
    help = 'Creates sample users and employee data for testing'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating sample data...')
        
        # Create admin user
        if not CustomUser.objects.filter(username='admin').exists():
            admin = CustomUser.objects.create_superuser(
                username='admin',
                email='admin@nas.gov.gh',
                password='admin123',
                first_name='System',
                last_name='Administrator',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created admin user (username: admin, password: admin123)'))
        else:
            admin = CustomUser.objects.get(username='admin')
            self.stdout.write(self.style.WARNING('Admin user already exists'))
        
        # Create sample employee
        employee_data = {
            'staff_id': 'P19S0110/61',
            'name': 'LOUISA LAAR',
            'status': 'CLEANER',
            'ssnit_number': 'P19S0110/61',
            'ghana_card': 'GHA-123245878-8',
            'bank_name': 'GCB',
            'bank_account': '1141024014787',
            'bank_branch': 'OSU',
            'contact': '24954990',
            'monthly_salary': Decimal('920.00'),
            'department': 'Administration',
            'unit': 'Estate',
            'grade': 'Temporal Worker',
            'level': 'Cleaner',
            'is_active': True
        }
        
        employee, created = Employee.objects.get_or_create(
            staff_id=employee_data['staff_id'],
            defaults=employee_data
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created sample employee: {employee.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Employee {employee.name} already exists'))
        
        # Create staff user linked to employee
        if not CustomUser.objects.filter(username='staff').exists():
            staff_user = CustomUser.objects.create_user(
                username='staff',
                email='staff@nas.gov.gh',
                password='staff123',
                first_name='Louisa',
                last_name='Laar',
                role='staff',
                staff_id=employee.staff_id
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created staff user (username: staff, password: staff123)'))
        else:
            self.stdout.write(self.style.WARNING('Staff user already exists'))
        
        # Create sample payslip
        if not Payslip.objects.filter(employee=employee, month_year='Jan-2026').exists():
            gross = employee.monthly_salary
            ssnit = calculate_ssnit(gross)
            tier2 = calculate_tier2(gross)
            tax = calculate_income_tax(gross)
            net = gross - ssnit - tier2 - tax
            
            payslip = Payslip.objects.create(
                employee=employee,
                month_year='Jan-2026',
                district='Accra Metropolitan Assembly',
                basic_salary=employee.monthly_salary,
                allowances=Decimal('0'),
                gross_salary=gross,
                ssnit_deduction=ssnit,
                tier2_deduction=tier2,
                income_tax=tax,
                other_deductions=Decimal('0'),
                net_salary=net,
                payment_mode='Ghana Commercial Bank, Ministries',
                approval_status='pending',
                generated_by=admin
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created sample payslip for {employee.name}'))
        else:
            self.stdout.write(self.style.WARNING('Sample payslip already exists'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Sample data creation complete!'))
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Admin - username: admin, password: admin123')
        self.stdout.write('  Staff - username: staff, password: staff123')
