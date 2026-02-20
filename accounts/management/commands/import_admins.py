from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.conf import settings
from accounts.models import CustomUser
from staff.models import Employee

HR_DEPARTMENT = 'HR DPT.'


class Command(BaseCommand):
    help = 'Import specific HR-Admin users from provided list'

    def handle(self, *args, **options):
        default_password = settings.DEFAULT_USER_PASSWORD
        if not default_password:
            raise CommandError("DEFAULT_USER_PASSWORD is not set. Add it to your environment or .env file.")

        admins_data = [
            {'staff_id': '1287339', 'role': 'hr_admin', 'contact': '262718659', 'email': 'anumasiedu@gmail.com', 'name': 'Anum Asiedu', 'dept': HR_DEPARTMENT, 'station': 'HEADQUARTERS', 'gender': 'MALE'},
            {'staff_id': '839016', 'role': 'hr_admin', 'contact': '242604184', 'email': '', 'name': 'Wilson Laudina', 'dept': HR_DEPARTMENT, 'station': 'HEADQUARTERS', 'gender': 'FEMALE'},
            {'staff_id': '926143', 'role': 'hr_admin', 'contact': '206150426', 'email': '', 'name': 'Gasu Helen', 'dept': HR_DEPARTMENT, 'station': 'HEADQUARTERS', 'gender': 'FEMALE'},
            {'staff_id': '926175', 'role': 'hr_admin', 'contact': '242129812', 'email': 'ama.frimpong@nas.gov.gh', 'name': 'Frimpong Ama', 'dept': HR_DEPARTMENT, 'station': 'HEADQUARTERS', 'gender': 'FEMALE'},
            {'staff_id': '926553', 'role': 'hr_admin', 'contact': '274354017', 'email': 'Sethokai37@gmail.com', 'name': 'Asare Seth', 'dept': HR_DEPARTMENT, 'station': 'HEADQUARTERS', 'gender': 'MALE'},
            {'staff_id': '934620', 'role': 'hr_admin', 'contact': '242785662', 'email': 'Fred.atsu@nas.gov.gh', 'name': 'Amedi Frederick', 'dept': HR_DEPARTMENT, 'station': 'HEADQUARTERS', 'gender': 'MALE'},
            {'staff_id': '934621', 'role': 'hr_admin', 'contact': '575122013', 'email': '', 'name': 'Kwasitsu Felix', 'dept': HR_DEPARTMENT, 'station': 'HEADQUARTERS', 'gender': 'MALE'},
            {'staff_id': 'hr', 'role': 'hr_admin', 'contact': '', 'email': 'edboatend@gmail.com', 'name': 'HR Admin hr', 'dept': 'ADMIN DPT.', 'station': 'HEADQUARTERS', 'gender': ''},
            {'staff_id': 'qa', 'role': 'hr_admin', 'contact': '', 'email': '', 'name': 'qa qa', 'dept': 'GAR DISPATCH CENTRE', 'station': 'GREATER ACCRA', 'gender': ''},
        ]

        success_count = 0
        with transaction.atomic():
            for data in admins_data:
                # Create/Update Employee
                employee, created = Employee.objects.update_or_create(
                    staff_id=data['staff_id'],
                    defaults={
                        'name': data['name'],
                        'contact': data['contact'],
                        'email': data['email'],
                        'gender': data['gender'],
                        'department': data['dept'],
                        'unit': data['station'],
                        'monthly_salary': 0, # Not specified
                    }
                )

                # Create/Update User
                name_parts = data['name'].split()
                first_name = name_parts[0] if name_parts else ""
                last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

                user, u_created = CustomUser.objects.update_or_create(
                    username=data['staff_id'],
                    defaults={
                        'role': data['role'],
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': data['email'],
                        'staff_id': data['staff_id'],
                    }
                )
                if u_created:
                    user.set_password(default_password)
                    user.save()

                action = "Created" if u_created else "Updated"
                self.stdout.write(self.style.SUCCESS(f"{action} HR-Admin: {data['name']} ({data['staff_id']})"))
                success_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {success_count} HR-Admins."))
