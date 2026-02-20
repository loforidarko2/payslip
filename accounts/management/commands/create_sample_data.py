"""
Management command to create sample users and data for testing.
"""
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from accounts.models import CustomUser
from payroll.models import Payslip
from payroll.utils import calculate_income_tax, calculate_ssnit, calculate_tier2
from staff.models import Employee


class Command(BaseCommand):
    help = "Creates sample users and employee data for testing"

    def handle(self, *args, **kwargs):
        default_password = settings.DEFAULT_USER_PASSWORD
        if not default_password:
            raise CommandError(
                "DEFAULT_USER_PASSWORD is not set. Add it to your environment or .env file."
            )

        self.stdout.write("Creating sample data...")

        if not CustomUser.objects.filter(username="admin").exists():
            admin = CustomUser.objects.create_superuser(
                username="admin",
                email="admin@nas.gov.gh",
                password=default_password,
                first_name="System",
                last_name="Administrator",
                role="admin",
            )
            self.stdout.write(self.style.SUCCESS("Created admin user (username: admin)"))
        else:
            admin = CustomUser.objects.get(username="admin")
            self.stdout.write(self.style.WARNING("Admin user already exists"))

        employee_data = {
            "staff_id": "P19S0110/61",
            "name": "LOUISA LAAR",
            "status": "CLEANER",
            "ssnit_number": "P19S0110/61",
            "ghana_card": "GHA-123245878-8",
            "bank_name": "GCB",
            "bank_account": "1141024014787",
            "bank_branch": "OSU",
            "contact": "24954990",
            "monthly_salary": Decimal("920.00"),
            "department": "Administration",
            "unit": "Estate",
            "grade": "Temporal Worker",
            "level": "Cleaner",
            "is_active": True,
        }
        employee, created = Employee.objects.get_or_create(
            staff_id=employee_data["staff_id"],
            defaults=employee_data,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created sample employee: {employee.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"Employee {employee.name} already exists"))

        if not CustomUser.objects.filter(username="staff").exists():
            CustomUser.objects.create_user(
                username="staff",
                email="staff@nas.gov.gh",
                password=default_password,
                first_name="Louisa",
                last_name="Laar",
                role="staff",
                staff_id=employee.staff_id,
            )
            self.stdout.write(self.style.SUCCESS("Created staff user (username: staff)"))
        else:
            self.stdout.write(self.style.WARNING("Staff user already exists"))

        if not Payslip.objects.filter(employee=employee, month_year="Jan-2026").exists():
            gross = employee.monthly_salary
            ssnit = calculate_ssnit(gross)
            tier2 = calculate_tier2(gross)
            tax = calculate_income_tax(gross)
            net = gross - ssnit - tier2 - tax

            Payslip.objects.create(
                employee=employee,
                month_year="Jan-2026",
                district="Accra Metropolitan Assembly",
                basic_salary=employee.monthly_salary,
                allowances=Decimal("0"),
                gross_salary=gross,
                ssnit_deduction=ssnit,
                tier2_deduction=tier2,
                income_tax=tax,
                other_deductions=Decimal("0"),
                net_salary=net,
                payment_mode="Ghana Commercial Bank, Ministries",
                approval_status="pending",
                generated_by=admin,
            )
            self.stdout.write(self.style.SUCCESS(f"Created sample payslip for {employee.name}"))
        else:
            self.stdout.write(self.style.WARNING("Sample payslip already exists"))

        self.stdout.write(self.style.SUCCESS("Sample data creation complete"))
        self.stdout.write("Login credentials:")
        self.stdout.write("  Admin - username: admin")
        self.stdout.write("  Staff - username: staff")
        self.stdout.write("  Password is loaded from DEFAULT_USER_PASSWORD")
