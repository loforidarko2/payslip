from django.core.management.base import BaseCommand
from staff.models import Employee
from django.db.models import Count

class Command(BaseCommand):
    help = 'Remove duplicate casual employee records, keeping only one per name'

    def handle(self, *args, **options):
        # Find all names that appear more than once
        duplicates = (
            Employee.objects
            .filter(staff_id__startswith='CA')
            .values('name')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )

        self.stdout.write(f"Found {len(duplicates)} duplicate names")

        total_deleted = 0
        for dup in duplicates:
            name = dup['name']
            # Get all records with this name, ordered by ID
            all_records = Employee.objects.filter(
                name=name, 
                staff_id__startswith='CA'
            ).order_by('id')
            
            # Keep the first one, delete the rest
            first_record = all_records.first()
            duplicates_to_delete = all_records.exclude(id=first_record.id)
            
            count = duplicates_to_delete.count()
            self.stdout.write(f"  {name}: keeping {first_record.staff_id}, deleting {count} duplicate(s)")
            
            duplicates_to_delete.delete()
            total_deleted += count

        self.stdout.write(self.style.SUCCESS(f"\nTotal deleted: {total_deleted}"))
        
        remaining = Employee.objects.filter(staff_id__startswith='CA').count()
        unique_names = Employee.objects.filter(staff_id__startswith='CA').values('name').distinct().count()
        
        self.stdout.write(self.style.SUCCESS(f"Remaining casual employees: {remaining}"))
        self.stdout.write(self.style.SUCCESS(f"Unique names: {unique_names}"))
        
        if remaining == unique_names:
            self.stdout.write(self.style.SUCCESS("\n✓ All duplicates removed successfully!"))
        else:
            self.stdout.write(self.style.WARNING(f"\n⚠ Warning: Still {remaining - unique_names} duplicates remaining"))
