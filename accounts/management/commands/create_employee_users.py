from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import IntegrityError
from staff.models import Employee

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates user accounts for all employees who do not have one'

    def handle(self, *args, **options):
        default_password = settings.DEFAULT_USER_PASSWORD
        if not default_password:
            raise CommandError("DEFAULT_USER_PASSWORD is not set. Add it to your environment or .env file.")

        employees = Employee.objects.all()
        created_count = 0
        skipped_count = 0

        self.stdout.write("Starting bulk user creation...")

        for emp in employees:
            # Check if user already exists with this staff_id
            if User.objects.filter(staff_id=emp.staff_id).exists():
                skipped_count += 1
                continue
                
            # Create new staff user
            try:
                # Username = Staff ID
                user = User.objects.create_user(
                    username=emp.staff_id,
                    email=f"{emp.staff_id.lower()}@nas.gov.gh",  # Dummy email
                    password=default_password,
                    role='staff',
                    staff_id=emp.staff_id,
                    first_name=emp.name.split()[0] if emp.name else "",
                    last_name=" ".join(emp.name.split()[1:]) if emp.name else "",
                    must_change_password=True  # Flag to prompt change
                )
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created user for {emp.staff_id} ({emp.name})"))
            except (ValueError, TypeError, IntegrityError) as e:
                self.stdout.write(self.style.ERROR(f"Failed to create user for {emp.staff_id}: {str(e)}"))

        self.stdout.write(self.style.SUCCESS(f"\nCompleted! Created: {created_count}, Skipped: {skipped_count}"))
