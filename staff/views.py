from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator
from django.core.files.storage import FileSystemStorage
from django.utils import timezone
from .models import Employee
from .forms import EmployeeForm, ImportEmployeeForm
from accounts.models import CustomUser
from accounts.decorators import hr_admin_required, employee_record_access_required
# import pandas as pd (Moved to import_employees to debug startup)

from accounts.forms import CustomUserCreationForm # For User Management View but that's in accounts?
# Actually User Management is admin stuff, might fit in accounts too. 
# But Employee Management fits here.

EMPLOYEE_LIST_URL_NAME = 'staff:employee_list'


@employee_record_access_required
def employee_list(request):
    """List all employees with search functionality"""
    search_query = request.GET.get('search', '')
    
    employees = Employee.objects.all()
    
    if search_query:
        employees = employees.filter(
            Q(name__icontains=search_query) |
            Q(staff_id__icontains=search_query) |
            Q(department__icontains=search_query)
        )
    
    employees = Paginator(employees.order_by('name'), 20).get_page(request.GET.get('page'))

    context = {
        'employees': employees,
        'search_query': search_query,
        'can_add_employee': request.user.is_admin() or request.user.is_hr_admin(),
        'can_edit_employee': request.user.is_admin() or request.user.is_hr_admin() or request.user.is_finance(),
        'can_remove_employee': request.user.is_admin() or request.user.is_hr_admin(),
    }
    
    return render(request, 'staff/employee_list.html', context) # Template path needs update later

@hr_admin_required
def employee_create(request):
    """Add a new employee"""
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Employee {employee.name} added successfully!')
            return redirect(EMPLOYEE_LIST_URL_NAME)
    else:
        form = EmployeeForm()
    
    context = {
        'form': form,
        'action': 'Add'
    }
    
    return render(request, 'staff/employee_form.html', context)

@employee_record_access_required
def employee_edit(request, staff_id):
    """Edit an existing employee"""
    employee = get_object_or_404(Employee, staff_id=staff_id)
    
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            employee = form.save()
            messages.success(request, f'Employee {employee.name} updated successfully!')
            return redirect(EMPLOYEE_LIST_URL_NAME)
    else:
        form = EmployeeForm(instance=employee)
    
    context = {
        'form': form,
        'action': 'Edit',
        'employee': employee,
        'can_remove_employee': request.user.is_admin() or request.user.is_hr_admin(),
    }
    
    return render(request, 'staff/employee_form.html', context)

@hr_admin_required
def employee_delete(request, staff_id):
    """Separate (remove) an employee and store reason"""
    employee = get_object_or_404(Employee, staff_id=staff_id)
    
    if request.method == 'POST':
        separation_reason = request.POST.get('separation_reason', '').strip()
        if not separation_reason:
            messages.error(request, "Removal reason is required.")
            return render(request, 'staff/employee_confirm_delete.html', {'employee': employee})

        employee.is_active = False
        employee.separation_reason = separation_reason
        employee.separated_at = timezone.now()
        employee.separated_by = request.user
        employee.save(update_fields=['is_active', 'separation_reason', 'separated_at', 'separated_by', 'updated_at'])
        messages.success(request, f'Employee {employee.name} separated successfully.')
        return redirect(EMPLOYEE_LIST_URL_NAME)
    
    return render(request, 'staff/employee_confirm_delete.html', {'employee': employee})

@hr_admin_required
def import_employees(request):
    """Import employees from Excel file"""
    import pandas as pd
    if request.method == 'POST':
        form = ImportEmployeeForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            fs = FileSystemStorage()
            filename = fs.save(excel_file.name, excel_file)
            uploaded_file_url = fs.path(filename)
            
            try:
                # Read Excel/CSV
                if filename.endswith('.csv'):
                    df = pd.read_csv(uploaded_file_url)
                else:
                    df = pd.read_excel(uploaded_file_url)
                
                # Process data
                success_count = 0
                error_count = 0
                
                # Normalize headers for robustness (only strip whitespace)
                df.columns = [c.strip() for c in df.columns]
                default_user_password = settings.DEFAULT_USER_PASSWORD or None
                if default_user_password is None:
                    messages.warning(
                        request,
                        "DEFAULT_USER_PASSWORD is not set. New users will be created with unusable passwords.",
                    )
                
                def get_row_value(row, possibilities):
                    """Helper to get value from row checking multiple possible header names"""
                    for p in possibilities:
                        if p in row and pd.notnull(row[p]):
                            return str(row[p]).strip()
                    # Also try case-insensitive match if direct match fails
                    row_keys_lower = {k.lower(): k for k in row.keys()}
                    for p in possibilities:
                        p_lower = p.lower()
                        if p_lower in row_keys_lower:
                            k = row_keys_lower[p_lower]
                            if pd.notnull(row[k]):
                                return str(row[k]).strip()
                    return ''

                for _, row in df.iterrows():
                    try:
                        # Extract basic info using flexible header mapping
                        staff_id = get_row_value(row, ['STAFF ID', 'staff_id', 'ID'])
                        
                        if not staff_id or staff_id.lower() == 'nan' or staff_id.lower() == 'bulk':
                            continue
                            
                        # Extract and Map Role
                        csv_role = get_row_value(row, ['ROLE', 'role']).lower()
                        role = 'staff'
                        station_name = get_row_value(row, ['STATION:', 'station_name', 'station']).lower()
                        region_name = get_row_value(row, ['REGION:', 'region']).lower()

                        if 'hr-admin' in csv_role or 'hr admin' in csv_role: 
                            role = 'hr_admin'
                        elif 'finance' in csv_role or 'finance' in station_name or 'finance' in region_name:
                            role = 'finance'
                        elif 'admin' in csv_role: 
                            role = 'admin'
                        
                        # Full name
                        full_name = get_row_value(row, ['Fullname', 'full_name', 'Name'])
                        name_parts = full_name.split(' ')
                        first_name = name_parts[0] if name_parts else ""
                        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
                        
                        # Create/Update Employee
                        employee, _ = Employee.objects.update_or_create(
                            staff_id=staff_id,
                            defaults={
                                'name': full_name,
                                'contact': get_row_value(row, ['PHONE:', 'contact_number:', 'phone', 'contact']),
                                'email': get_row_value(row, ['EMAIL:', 'email']),
                                'gender': get_row_value(row, ['Gender', 'gender']),
                                'unit': get_row_value(row, ['STATION:', 'station_name', 'station']),
                                'department': get_row_value(row, ['REGION:', 'region']),
                                'monthly_salary': row.get('salary', 0) if pd.notnull(row.get('salary')) else 0,
                                'grade': get_row_value(row, ['grade', 'Grade']),
                                'level': get_row_value(row, ['level', 'Level']),
                            }
                        )
                        
                        # Only create User Account for non-casual employees
                        # Casual employees (staff IDs starting with 'CA') should NOT have login access
                        if not staff_id.startswith('CA'):
                            user_defaults = {
                                'role': role,
                                'first_name': first_name,
                                'last_name': last_name,
                                'email': employee.email,
                                'staff_id': staff_id,
                                'department': employee.department,
                                'unit': employee.unit,
                            }
                            
                            user_obj = CustomUser.objects.filter(username=staff_id).first()
                            if not user_obj:
                                CustomUser.objects.create_user(
                                    username=staff_id,
                                    password=default_user_password,
                                    **user_defaults
                                )
                            else:
                                # Update existing user role and details
                                for attr, value in user_defaults.items():
                                    setattr(user_obj, attr, value)
                                user_obj.save()
                        
                        success_count += 1
                    except (ValueError, TypeError, KeyError) as e:
                        print(f"Error importing row: {e}")
                        error_count += 1
                
                messages.success(request, f'Successfully imported/updated {success_count} employees. {error_count} errors.')
                
                # Clean up file
                fs.delete(filename)
                
                return redirect(EMPLOYEE_LIST_URL_NAME)
                
            except (ValueError, OSError, KeyError, pd.errors.ParserError) as e:
                messages.error(request, f'Error reading file: {str(e)}')
    else:
        form = ImportEmployeeForm()
        
    return render(request, 'staff/import_employees.html', {'form': form})
