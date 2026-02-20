from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from staff.models import Employee
from payroll.models import Payslip
from django.db import transaction

class Command(BaseCommand):
    help = 'Safely clear users, employees, or all data from the system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            action='store_true',
            help='Delete all non-superuser accounts',
        )
        parser.add_argument(
            '--employees',
            action='store_true',
            help='Delete all employee records',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Delete all users (except superusers), employees, and payslips',
        )

    def handle(self, *args, **options):
        clear_users = options['users'] or options['all']
        clear_employees = options['employees'] or options['all']
        clear_all = options['all']

        if not any([clear_users, clear_employees, clear_all]):
            self.stdout.write(self.style.ERROR('Please specify what to clear: --users, --employees, or --all'))
            return

        self.stdout.write(self.style.WARNING('CAUTION: This action is destructive and cannot be undone.'))
        confirm = input('Are you sure you want to proceed? (yes/no): ')
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.SUCCESS('Operation cancelled.'))
            return

        with transaction.atomic():
            if clear_all:
                self.stdout.write('Clearing Payslips...')
                Payslip.objects.all().delete()
                
            if clear_employees:
                self.stdout.write('Clearing Employee records...')
                Employee.objects.all().delete()
                
            if clear_users:
                self.stdout.write('Clearing User accounts (excluding superusers and admins)...')
                # Never delete superusers or those with 'admin' role to prevent lockout
                # Using Case-insensitive exclude for 'admin' role
                users_to_delete = CustomUser.objects.filter(is_superuser=False).exclude(role__iexact='admin')
                users_deleted = users_to_delete.delete()
                self.stdout.write(self.style.SUCCESS(f'Deleted {users_deleted[0]} users.'))

        self.stdout.write(self.style.SUCCESS('Data cleanup complete!'))
