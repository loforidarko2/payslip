from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import FileResponse
from django.conf import settings
from django.db import DatabaseError
from django.core.paginator import Paginator
from django.views.decorators.clickjacking import xframe_options_sameorigin
from decimal import Decimal, DecimalException
from datetime import datetime, date
from django.utils import timezone
import os

from .models import Payslip, PayslipAudit, SystemConfiguration
from .forms import PayslipGenerateForm, BulkPayslipGenerateForm, SystemConfigurationForm
from .utils import calculate_ssnit, calculate_tier2, calculate_income_tax, generate_payslip_pdf
from payslip.date_utils import parse_month_year, build_month_year_filters

from staff.models import Employee
from accounts.decorators import admin_required, finance_required, staff_or_admin_required


def _resolved_snapshot(payslip):
    """Resolve snapshot values with fallback to current employee record."""
    employee = payslip.employee

    birth_date = employee.date_of_birth
    is_above_ssnit_age = False
    if birth_date:
        today = date.today()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        is_above_ssnit_age = age >= 60

    # SSNIT is preferred unless employee is above SSNIT age.
    if not is_above_ssnit_age and employee.ssnit_number:
        id_value = employee.ssnit_number
    elif employee.ghana_card:
        id_value = employee.ghana_card
    else:
        id_value = employee.ssnit_number or ''

    return {
        'department': payslip.department or employee.department or '',
        'unit': payslip.unit or employee.unit or '',
        'grade': payslip.grade or employee.grade or '',
        'level': payslip.level or employee.level or '',
        'staff_identifier': id_value,
    }


@finance_required(allow_admin=False)
def payslip_generate(request):
    """Generate a new payslip"""
    if request.method == 'POST':
        form = PayslipGenerateForm(request.POST)
        if form.is_valid():
            try:
                employee = form.cleaned_data['employee']
                month_year = form.cleaned_data['month_year']
                config = SystemConfiguration.get_settings()
                ssnit_rate = form.cleaned_data.get('ssnit_rate', config.ssnit_rate)
                tier2_rate = form.cleaned_data.get('tier2_rate', config.tier2_rate)
                
                # Use default district from config if empty
                district = form.cleaned_data.get('district') or config.default_district
                
                # Calculate financials
                basic_salary = employee.monthly_salary
                allowances = Decimal(0)
                other_deductions = Decimal(0)
                gross_salary = basic_salary + allowances
                
                ssnit = calculate_ssnit(gross_salary, ssnit_rate)
                tier2 = calculate_tier2(gross_salary, tier2_rate)
                income_tax = calculate_income_tax(gross_salary)
                
                net_salary = gross_salary - ssnit - tier2 - income_tax - other_deductions
                
                payslip = Payslip.objects.create(
                    employee=employee,
                    month_year=month_year,
                    agency=config.agency_name,
                    district=district,
                    department=employee.department,
                    unit=employee.unit,
                    grade=employee.grade,
                    level=employee.level,
                    basic_salary=basic_salary,
                    allowances=allowances,
                    gross_salary=gross_salary,
                    ssnit_deduction=ssnit,
                    tier2_deduction=tier2,
                    income_tax=income_tax,
                    other_deductions=other_deductions,
                    net_salary=net_salary,
                    payment_mode=f"{employee.bank_name}, {employee.bank_branch}" if employee.bank_name else "",
                    approval_status='pending',
                    generated_by=request.user
                )
                
                messages.success(request, f'Payslip generated successfully for {employee.name}')
                return redirect(settings.LOGIN_REDIRECT_URL)
            except (ValueError, TypeError, DecimalException, DatabaseError) as e:
                messages.error(request, f'Error generating payslip: {str(e)}')
    else:
        form = PayslipGenerateForm()
    
    # Prepare employee data for auto-fill
    import json
    employees = Employee.objects.filter(staff_id__startswith='CA', is_active=True)
    
    employee_details = {}
    employee_salaries = {}
    
    for emp in employees:
        employee_details[str(emp.staff_id)] = {
            'department': emp.department or '',
            'unit': emp.unit or '',
            'grade': emp.grade or '',
            'level': emp.level or ''
        }
        employee_salaries[str(emp.staff_id)] = float(emp.monthly_salary)
    
    context = {
        'form': form,
        'employee_details_json': json.dumps(employee_details),
        'employee_salaries_json': json.dumps(employee_salaries)
    }
    
    return render(request, 'payroll/payslip_generate.html', context)

@finance_required(allow_admin=False)
def payslip_bulk_generate(request):
    """Generate payslips for all active employees"""
    if request.method == 'POST':
        form = BulkPayslipGenerateForm(request.POST)
        if form.is_valid():
            config = SystemConfiguration.get_settings()
            month_year = form.cleaned_data['month_year']
            district = form.cleaned_data.get('district') or config.default_district
            ssnit_rate = form.cleaned_data.get('ssnit_rate', config.ssnit_rate)
            tier2_rate = form.cleaned_data.get('tier2_rate', config.tier2_rate)
            
            active_employees = Employee.objects.filter(is_active=True)
            created_count = 0
            skipped_count = 0
            
            for employee in active_employees:
                if Payslip.objects.filter(employee=employee, month_year=month_year).exists():
                    skipped_count += 1
                    continue
                
                # Calculate financials (simplified for bulk)
                basic_salary = employee.monthly_salary
                allowances = Decimal(0) 
                other_deductions = Decimal(0)
                gross_salary = basic_salary + allowances
                
                ssnit = calculate_ssnit(gross_salary, ssnit_rate)
                tier2 = calculate_tier2(gross_salary, tier2_rate)
                income_tax = calculate_income_tax(gross_salary)
                net_salary = gross_salary - ssnit - tier2 - income_tax - other_deductions
                
                Payslip.objects.create(
                    employee=employee,
                    month_year=month_year,
                    agency=config.agency_name,
                    district=district,
                    department=employee.department,
                    unit=employee.unit,
                    grade=employee.grade,
                    level=employee.level,
                    basic_salary=basic_salary,
                    allowances=allowances,
                    gross_salary=gross_salary,
                    ssnit_deduction=ssnit,
                    tier2_deduction=tier2,
                    income_tax=income_tax,
                    other_deductions=other_deductions,
                    net_salary=net_salary,
                    payment_mode=("" if not employee.bank_name else f"{employee.bank_name}, {employee.bank_branch}"),
                    approval_status='pending',
                    generated_by=request.user
                )
                created_count += 1
            
            if created_count > 0:
                messages.success(request, f'Successfully generated {created_count} payslips for {month_year}.')
            if skipped_count > 0:
                messages.warning(request, f'Skipped {skipped_count} employees (payslips already exist).')
                
            return redirect(settings.LOGIN_REDIRECT_URL)
    else:
        form = BulkPayslipGenerateForm()
    
    return render(request, 'payroll/payslip_bulk_generate.html', {
        'form': form,
        'active_count': Employee.objects.filter(is_active=True).count()
    })

@finance_required(allow_admin=True)
def payslip_approve_list(request):
    """List all pending payslips for approval"""
    selected_month = request.GET.get('month', '').strip()
    selected_year = request.GET.get('year', '').strip()

    pending_payslips = Payslip.objects.filter(approval_status='pending').select_related('employee', 'generated_by')
    all_payslips = Payslip.objects.select_related('employee', 'approved_by').order_by('-generated_at')

    if selected_month:
        pending_payslips = pending_payslips.filter(month_year__startswith=selected_month)
        all_payslips = all_payslips.filter(month_year__startswith=selected_month)
    if selected_year:
        pending_payslips = pending_payslips.filter(month_year__endswith=selected_year)
        all_payslips = all_payslips.filter(month_year__endswith=selected_year)

    _, month_options, year_options = build_month_year_filters(
        Payslip.objects.values_list('month_year', flat=True).distinct()
    )
    
    pending_payslips = Paginator(pending_payslips.order_by('-generated_at'), 15).get_page(request.GET.get('pending_page'))
    all_payslips = Paginator(all_payslips.order_by('-generated_at'), 15).get_page(request.GET.get('recent_page'))

    context = {
        'pending_payslips': pending_payslips,
        'all_payslips': all_payslips,
        'month_options': month_options,
        'year_options': year_options,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'can_act_on_approvals': request.user.is_finance(),
    }
    return render(request, 'payroll/payslip_approve_list.html', context)

@finance_required(allow_admin=False)
def payslip_approve(request, payslip_id):
    """Approve a specific payslip"""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    payslip.approval_status = 'approved'
    payslip.approved_by = request.user
    payslip.approved_at = timezone.now()
    payslip.save()
    
    messages.success(request, f'Payslip for {payslip.employee.name} approved.')
    return redirect('payroll:payslip_approve_list')

@finance_required(allow_admin=False)
def payslip_reject(request, payslip_id):
    """Reject a specific payslip"""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    payslip.approval_status = 'rejected'
    payslip.save()
    
    messages.warning(request, f'Payslip for {payslip.employee.name} rejected.')
    return redirect('payroll:payslip_approve_list')

@finance_required(allow_admin=False)
def payslip_revert_to_pending(request, payslip_id):
    """Revert an approved or rejected payslip back to pending"""
    payslip = get_object_or_404(Payslip, id=payslip_id)

    if request.method != 'POST':
        messages.error(request, "Invalid request.")
        return redirect('payroll:payslip_view', payslip_id=payslip.id)

    if payslip.approval_status == 'pending':
        messages.info(request, f'Payslip for {payslip.employee.name} is already pending.')
        return redirect('payroll:payslip_view', payslip_id=payslip.id)

    reason_choice = (request.POST.get('reason_choice') or '').strip()
    reason_details = (request.POST.get('reason_details') or '').strip()
    reason = reason_choice
    if reason_details:
        reason = f"{reason_choice} - {reason_details}"
    if not reason:
        messages.error(request, "Revert reason is required.")
        return redirect('payroll:payslip_view', payslip_id=payslip.id)

    old_status = payslip.approval_status
    payslip.approval_status = 'pending'
    payslip.approved_by = None
    payslip.approved_at = None
    payslip.last_modified_by = request.user
    payslip.save()

    PayslipAudit.objects.create(
        payslip=payslip,
        action='revert',
        old_status=old_status,
        new_status='pending',
        reason=reason,
        performed_by=request.user,
    )

    messages.success(request, f'Payslip for {payslip.employee.name} reverted to pending.')
    return redirect('payroll:payslip_view', payslip_id=payslip.id)

@finance_required(allow_admin=False)
def payslip_bulk_approve(request):
    """Approve multiple payslips at once"""
    if request.method == 'POST':
        payslip_ids = request.POST.getlist('payslip_ids')
        if payslip_ids:
            approved_at = timezone.now()
            Payslip.objects.filter(id__in=payslip_ids).update(
                approval_status='approved',
                approved_by=request.user,
                approved_at=approved_at
            )
            messages.success(request, f'{len(payslip_ids)} payslips approved successfully.')
        else:
            messages.info(request, 'No payslips selected.')
    return redirect('payroll:payslip_approve_list')

@staff_or_admin_required
def payslip_view(request, payslip_id):
    """View details of a payslip"""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    # Check permissions
    if not request.user.is_admin() and not request.user.is_finance() and not request.user.is_hr_admin():
        # Regular staff can only view own
        if payslip.employee.staff_id != request.user.staff_id:
            messages.error(request, "You can only view your own payslips.")
            return redirect(settings.LOGIN_REDIRECT_URL)
        if payslip.approval_status != 'approved':
            messages.info(request, "This payslip is currently pending review and is not available.")
            return redirect(settings.LOGIN_REDIRECT_URL)

    if request.user.is_admin() or request.user.is_finance() or request.user.is_hr_admin():
        accessible_qs = Payslip.objects.select_related('employee')
    else:
        accessible_qs = Payslip.objects.select_related('employee').filter(
            employee__staff_id=request.user.staff_id,
            approval_status='approved'
        )

    selected_employee = request.GET.get('employee', '').strip()
    selected_month = request.GET.get('month', '').strip()
    selected_year = request.GET.get('year', '').strip()
    apply_filter = request.GET.get('apply_filter') == '1'

    if apply_filter:
        target_qs = accessible_qs
        if selected_employee:
            target_qs = target_qs.filter(employee__staff_id=selected_employee)
        if selected_month:
            target_qs = target_qs.filter(month_year__startswith=selected_month)
        if selected_year:
            target_qs = target_qs.filter(month_year__endswith=selected_year)

        target = target_qs.order_by('-generated_at').first()
        if target:
            if target.id != payslip.id:
                return redirect('payroll:payslip_view', payslip_id=target.id)
        else:
            messages.info(request, "No payslip found for the selected filter.")

    periods, month_options, year_options = build_month_year_filters(
        accessible_qs.values_list('month_year', flat=True).distinct()
    )

    employee_options = accessible_qs.values('employee__staff_id', 'employee__name').distinct().order_by('employee__name')
    if not selected_employee:
        selected_employee = payslip.employee.staff_id
    if not selected_month or not selected_year:
        parsed_current = parse_month_year(payslip.month_year)
        if parsed_current:
            selected_month = selected_month or parsed_current.strftime('%b')
            selected_year = selected_year or str(parsed_current.year)

    config = SystemConfiguration.get_settings()
    snapshot = _resolved_snapshot(payslip)
    return render(request, 'payroll/payslip_view.html', {
        'payslip': payslip,
        'config': config,
        'snapshot': snapshot,
        'employee_options': employee_options,
        'month_options': month_options,
        'year_options': year_options,
        'selected_employee': selected_employee,
        'selected_month': selected_month,
        'selected_year': selected_year,
    })

@staff_or_admin_required
@xframe_options_sameorigin
def payslip_preview_pdf(request, payslip_id):
    """Preview payslip PDF in browser"""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    # Check permissions
    if not request.user.is_admin() and not request.user.is_finance() and not request.user.is_hr_admin():
         if payslip.employee.staff_id != request.user.staff_id:
            messages.error(request, "Access denied.")
            return redirect(settings.LOGIN_REDIRECT_URL)
         if payslip.approval_status != 'approved':
            messages.error(request, "Access denied.")
            return redirect(settings.LOGIN_REDIRECT_URL)
            
    try:
        filepath, filename = generate_payslip_pdf(payslip)
        
        response = FileResponse(open(filepath, 'rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    except (OSError, ValueError, TypeError) as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('payroll:payslip_view', payslip_id=payslip_id)

@staff_or_admin_required
def payslip_download_pdf(request, payslip_id):
    """Download payslip PDF"""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    # Same permissions check...
    if not request.user.is_admin() and not request.user.is_finance() and not request.user.is_hr_admin():
         if payslip.employee.staff_id != request.user.staff_id:
            return redirect(settings.LOGIN_REDIRECT_URL)
         if payslip.approval_status != 'approved':
            return redirect(settings.LOGIN_REDIRECT_URL)

    try:
        filepath, filename = generate_payslip_pdf(payslip)
        return FileResponse(open(filepath, 'rb'), as_attachment=True, filename=filename)
    except (OSError, ValueError, TypeError) as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('payroll:payslip_view', payslip_id=payslip_id)

@finance_required(allow_admin=False)
def payslip_edit(request, payslip_id):
    """Edit a payslip"""
    payslip = get_object_or_404(Payslip, id=payslip_id)
    
    # Only pending allowed for non-finance/admin
    if payslip.approval_status != 'pending' and not (request.user.is_admin() or request.user.is_finance()):
        messages.error(request, "Cannot edit processed payslips.")
        return redirect('payroll:payslip_approve_list')
        
    if request.method == 'POST':
        reason_choice = (request.POST.get('edit_reason_choice') or '').strip()
        reason_details = (request.POST.get('edit_reason_details') or '').strip()
        reason = reason_choice
        if reason_details:
            reason = f"{reason_choice} - {reason_details}"
        if not reason:
            messages.error(request, "Edit reason is required.")
            return render(request, 'payroll/payslip_edit.html', {'payslip': payslip})

        old_status = payslip.approval_status
        # Simple update logic matching the template's fields
        payslip.department = request.POST.get('department', payslip.department)
        payslip.unit = request.POST.get('unit', payslip.unit)
        payslip.basic_salary = Decimal(request.POST.get('basic_salary', payslip.basic_salary))
        payslip.allowances = Decimal(request.POST.get('allowances', payslip.allowances))
        payslip.ssnit_deduction = Decimal(request.POST.get('ssnit_deduction', payslip.ssnit_deduction))
        payslip.tier2_deduction = Decimal(request.POST.get('tier2_deduction', payslip.tier2_deduction))
        payslip.income_tax = Decimal(request.POST.get('income_tax', payslip.income_tax))
        payslip.other_deductions = Decimal(request.POST.get('other_deductions', payslip.other_deductions))
        
        # Recalculate Net
        payslip.gross_salary = payslip.basic_salary + payslip.allowances
        payslip.net_salary = payslip.gross_salary - (payslip.ssnit_deduction + payslip.tier2_deduction + payslip.income_tax + payslip.other_deductions)
        
        # If it was approved/rejected, revert to pending after changes
        if payslip.approval_status in ['approved', 'rejected']:
            payslip.approval_status = 'pending'
            payslip.approved_by = None
            payslip.approved_at = None

        payslip.last_modified_by = request.user
        payslip.save()

        PayslipAudit.objects.create(
            payslip=payslip,
            action='edit',
            old_status=old_status,
            new_status=payslip.approval_status,
            reason=reason,
            performed_by=request.user,
        )
        messages.success(request, f"Payslip for {payslip.employee.name} updated.")
        return redirect('payroll:payslip_view', payslip_id=payslip.id)

    snapshot = _resolved_snapshot(payslip)
    return render(request, 'payroll/payslip_edit.html', {'payslip': payslip, 'snapshot': snapshot})

@admin_required
def payslip_delete(request, payslip_id):
    payslip = get_object_or_404(Payslip, id=payslip_id)
    payslip.delete()
    messages.success(request, 'Payslip deleted.')
    return redirect('payroll:payslip_approve_list')

@admin_required
def system_settings(request):
    """View to manage global system configuration"""
    config = SystemConfiguration.get_settings()
    
    if request.method == 'POST':
        form = SystemConfigurationForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "System settings updated successfully.")
            return redirect('payroll:system_settings')
    else:
        form = SystemConfigurationForm(instance=config)
    
    return render(request, 'payroll/system_settings.html', {'form': form, 'config': config})
