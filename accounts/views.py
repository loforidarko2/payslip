from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, PasswordResetForm
from django.contrib import messages
from django.conf import settings
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime
from .models import CustomUser
from .forms import CustomUserCreationForm, StaffIdPasswordResetForm
from staff.models import Employee
from payroll.models import Payslip
from .decorators import admin_required, hr_admin_required, finance_required

def login_view(request):
    """Custom login view"""
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
        
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            # Check if user has a staff profile linked and sync details if needed
            # (Synchronization logic could go here)
            return redirect(settings.LOGIN_REDIRECT_URL)
        else:
            messages.error(request, "Invalid username/staff ID or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')

@login_required
def change_password(request):
    """Allow users to change their own password"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

def forgot_password(request):
    """Handle password reset request via Staff ID"""
    if request.method == 'POST':
        form = StaffIdPasswordResetForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and user.email:
                # Create a PasswordResetForm with the user's email
                reset_form = PasswordResetForm({'email': user.email})
                if reset_form.is_valid():
                    reset_form.save(
                        request=request,
                        use_https=request.is_secure(),
                        email_template_name='registration/password_reset_email.html',
                        subject_template_name='registration/password_reset_subject.txt',
                    )
            
            # Show success message regardless to prevent enumeration
            return render(request, 'accounts/password_reset_sent.html', {'staff_id': form.cleaned_data['staff_id']})
    else:
        form = StaffIdPasswordResetForm()
    
    return render(request, 'accounts/forgot_password.html', {'form': form})

@login_required
def profile(request):
    """User profile view"""
    if request.method == 'POST':
        user = request.user
        
        # All users can update email
        user.email = request.POST.get('email', '')
        
        # Only admins and hr_admins can update name fields
        if user.is_admin() or user.is_hr_admin():
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def dashboard(request):
    """Dashboard view - redirects to appropriate dashboard based on role"""
    user = request.user
    if user.is_admin():
        return admin_dashboard(request)
    elif user.is_finance():
        return finance_dashboard(request)
    elif user.is_hr_admin():
        return hr_admin_dashboard(request)
    else:
        return staff_dashboard(request)

# Role-specific dashboards (Keep them here or move? Here is fine for central routing)

@admin_required
def admin_dashboard(request):
    """Admin dashboard with system statistics (User Management view)"""
    total_employees = Employee.objects.count()
    active_employees = Employee.objects.filter(is_active=True).count()
    total_users = CustomUser.objects.count()
    total_payslips = Payslip.objects.count()
    
    context = {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'total_users': total_users,
        'total_payslips': total_payslips,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)

@hr_admin_required
def hr_admin_dashboard(request):
    """HR Admin dashboard - View approved payslips only"""
    selected_month = request.GET.get('month', '').strip()
    selected_year = request.GET.get('year', '').strip()
    selected_employee = request.GET.get('employee', '').strip()
    search_query = request.GET.get('q', '').strip()

    approved_qs = Payslip.objects.filter(approval_status='approved').select_related(
        'employee', 'generated_by', 'approved_by'
    )

    if selected_employee:
        approved_qs = approved_qs.filter(employee__staff_id=selected_employee)
    if selected_month:
        approved_qs = approved_qs.filter(month_year__startswith=selected_month)
    if selected_year:
        approved_qs = approved_qs.filter(month_year__endswith=selected_year)
    if search_query:
        approved_qs = approved_qs.filter(
            Q(employee__name__icontains=search_query) |
            Q(employee__staff_id__icontains=search_query) |
            Q(month_year__icontains=search_query)
        )

    def parse_month_year(value):
        try:
            return datetime.strptime(value, '%b-%Y')
        except (TypeError, ValueError):
            return None

    available_periods = []
    for period in Payslip.objects.filter(approval_status='approved').values_list('month_year', flat=True).distinct():
        period_dt = parse_month_year(period)
        if period_dt:
            available_periods.append(period_dt)
    available_periods = sorted(set(available_periods), reverse=True)

    month_options = []
    seen_months = set()
    for dt in available_periods:
        month_name = dt.strftime('%b')
        if month_name not in seen_months:
            seen_months.add(month_name)
            month_options.append(month_name)
    year_options = sorted({str(dt.year) for dt in available_periods}, reverse=True)
    employee_options = Employee.objects.filter(
        payslips__approval_status='approved'
    ).distinct().order_by('name')

    approved_payslips = approved_qs.count()
    paginator = Paginator(approved_qs.order_by('-approved_at', '-generated_at'), 15)
    recent_approved = paginator.get_page(request.GET.get('page'))
    
    context = {
        'approved_payslips': approved_payslips,
        'recent_approved': recent_approved,
        'month_options': month_options,
        'year_options': year_options,
        'employee_options': employee_options,
        'selected_employee': selected_employee,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'search_query': search_query,
    }
    return render(request, 'accounts/hr_admin_dashboard.html', context)

@finance_required
def finance_dashboard(request):
    """Finance dashboard - generation and approval work queue"""
    selected_month = request.GET.get('month', '').strip()
    selected_year = request.GET.get('year', '').strip()
    selected_employee = request.GET.get('employee', '').strip()

    recent_generated_qs = Payslip.objects.select_related('employee', 'generated_by', 'approved_by')
    if selected_employee:
        recent_generated_qs = recent_generated_qs.filter(employee__staff_id=selected_employee)
    if selected_month:
        recent_generated_qs = recent_generated_qs.filter(month_year__startswith=selected_month)
    if selected_year:
        recent_generated_qs = recent_generated_qs.filter(month_year__endswith=selected_year)

    def parse_month_year(value):
        try:
            return datetime.strptime(value, '%b-%Y')
        except (TypeError, ValueError):
            return None

    available_periods = set()
    for period in Payslip.objects.values_list('month_year', flat=True).distinct():
        period_dt = parse_month_year(period)
        if period_dt:
            available_periods.add(period_dt)
    sorted_periods = sorted(available_periods, reverse=True)
    month_options = []
    seen_months = set()
    for period in sorted_periods:
        month_name = period.strftime('%b')
        if month_name not in seen_months:
            seen_months.add(month_name)
            month_options.append(month_name)
    year_options = sorted({str(period.year) for period in sorted_periods}, reverse=True)
    employee_options = Employee.objects.filter(payslips__isnull=False).distinct().order_by('name')

    recent_generated_qs = recent_generated_qs.order_by('-generated_at')
    recent_generated = Paginator(recent_generated_qs, 10).get_page(request.GET.get('page'))
    pending_approvals = Payslip.objects.filter(approval_status='pending').count()
    
    context = {
        'recent_generated': recent_generated,
        'pending_approvals': pending_approvals,
        'month_options': month_options,
        'year_options': year_options,
        'employee_options': employee_options,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'selected_employee': selected_employee,
    }
    return render(request, 'accounts/finance_dashboard.html', context)

@login_required
def staff_dashboard(request):
    """Standard staff dashboard - View own payslips"""
    current_month = datetime.now().strftime('%b')
    current_year = str(datetime.now().year)
    month_param = request.GET.get('month')
    year_param = request.GET.get('year')

    # Default dashboard view: show current month's payslip only.
    if month_param is None and year_param is None:
        selected_month = current_month
        selected_year = current_year
    else:
        selected_month = (month_param or '').strip()
        selected_year = (year_param or '').strip()

    month_options = []
    year_options = []

    def parse_month_year(value):
        try:
            return datetime.strptime(value, '%b-%Y')
        except (TypeError, ValueError):
            return None

    # Try to find employee record linked to user
    try:
        if request.user.staff_id:
            employee = Employee.objects.get(staff_id=request.user.staff_id)
            payslips_qs = Payslip.objects.filter(employee=employee, approval_status='approved')

            available_periods = []
            for period in payslips_qs.values_list('month_year', flat=True).distinct():
                period_dt = parse_month_year(period)
                if period_dt:
                    available_periods.append(period_dt)

            available_periods = sorted(set(available_periods), reverse=True)
            month_options = []
            seen_months = set()
            for dt in available_periods:
                month_name = dt.strftime('%b')
                if month_name not in seen_months:
                    seen_months.add(month_name)
                    month_options.append(month_name)
            year_options = sorted({str(dt.year) for dt in available_periods}, reverse=True)

            # Keep current month/year visible in filters even when no current payslip exists yet.
            if current_month not in month_options:
                month_options.insert(0, current_month)
            if current_year not in year_options:
                year_options.insert(0, current_year)

            if selected_month:
                payslips_qs = payslips_qs.filter(month_year__startswith=selected_month)
            if selected_year:
                payslips_qs = payslips_qs.filter(month_year__endswith=selected_year)

            payslips_qs = payslips_qs.order_by('-generated_at')
            payslips = Paginator(payslips_qs, 10).get_page(request.GET.get('page'))
            selected_payslip = payslips_qs.first()
        else:
            employee = None
            payslips = []
            selected_payslip = None
            
    except Employee.DoesNotExist:
        employee = None
        payslips = []
        selected_payslip = None
        
    context = {
        'employee': employee,
        'payslips': payslips,
        'selected_payslip': selected_payslip,
        'month_options': month_options,
        'year_options': year_options,
        'selected_month': selected_month,
        'selected_year': selected_year,
    }
    return render(request, 'accounts/staff_dashboard.html', context)

# User Management Views

@admin_required
def user_list(request):
    """List all users"""
    query = request.GET.get('q', '').strip()
    users = CustomUser.objects.all()
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(staff_id__icontains=query) |
            Q(role__icontains=query)
        )
    users = Paginator(users.order_by('username'), 15).get_page(request.GET.get('page'))
    return render(request, 'accounts/user_list.html', {'users': users, 'query': query})

@admin_required
def user_create(request):
    """Create a new user"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('accounts:user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/user_form.html', {'form': form, 'action': 'Create'})

@admin_required
def user_edit(request, user_id):
    """Edit an existing user"""
    user_obj = get_object_or_404(CustomUser, id=user_id)
    # Generic update logic or Form... 
    # For now, just handling simple updates manually or needing a form
    # To keep this complete, I'll direct to the template which handles POST manually based on previous code
    
    if request.method == 'POST':
        # Handling manual update matching previous user_edit template logic
        user_obj.first_name = request.POST.get('first_name', '')
        user_obj.last_name = request.POST.get('last_name', '')
        user_obj.email = request.POST.get('email', '')
        user_obj.role = request.POST.get('role', 'staff')
        user_obj.staff_id = request.POST.get('staff_id', '')
        user_obj.is_active = request.POST.get('is_active') == 'on'
        # ... other fields
        user_obj.save()
        messages.success(request, f'User {user_obj.username} updated.')
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_edit.html', {'user_obj': user_obj})

@admin_required
def user_delete(request, user_id):
    """Delete a user"""
    user_obj = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f'User {username} deleted.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'user_obj': user_obj})
