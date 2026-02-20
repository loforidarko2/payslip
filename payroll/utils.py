"""
Utility functions for tax calculations and PDF generation
"""
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime, date
import calendar
import os
from django.conf import settings
from .models import SystemConfiguration


def calculate_ssnit(gross_salary, rate=None):
    """Calculate SSNIT contribution (uses database default if rate not provided)"""
    if rate is None:
        config = SystemConfiguration.get_settings()
        rate = config.ssnit_rate
    return round(Decimal(gross_salary) * Decimal(rate) / Decimal(100), 2)


def calculate_tier2(gross_salary, rate=None):
    """Calculate Tier 2 pension contribution (uses database default if rate not provided)"""
    if rate is None:
        config = SystemConfiguration.get_settings()
        rate = config.tier2_rate
    return round(Decimal(gross_salary) * Decimal(rate) / Decimal(100), 2)


def calculate_income_tax(monthly_gross):
    """
    Calculate Ghana income tax based on 2024/2025 tax brackets
    Progressive tax calculation on annual income
    """
    annual_gross = Decimal(monthly_gross) * Decimal(12)
    
    # Tax brackets (annual amounts in GHS)
    brackets = [
        (Decimal('4380'), Decimal('0')),      # First 4,380: 0%
        (Decimal('1320'), Decimal('5')),      # Next 1,320: 5%
        (Decimal('1320'), Decimal('10')),     # Next 1,320: 10%
        (Decimal('33120'), Decimal('17.5')),  # Next 33,120: 17.5%
        (Decimal('199860'), Decimal('25')),   # Next 199,860: 25%
        (Decimal('999999999'), Decimal('30')) # Above 240,000: 30%
    ]
    
    total_tax = Decimal('0')
    remaining = annual_gross
    
    for bracket_amount, rate in brackets:
        if remaining <= 0:
            break
        
        taxable_in_bracket = min(remaining, bracket_amount)
        tax_in_bracket = taxable_in_bracket * rate / Decimal('100')
        total_tax += tax_in_bracket
        remaining -= taxable_in_bracket
    
    # Return monthly tax
    monthly_tax = total_tax / Decimal('12')
    return round(monthly_tax, 2)


def generate_payslip_pdf(payslip):
    """
    Generate an Excel-style payslip PDF optimized for black and white printing
    Uses simple borders, no colors, landscape orientation
    """
    # Create PDF filename
    filename = f"payslip_{payslip.employee.staff_id}_{payslip.month_year.replace('-', '_')}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'payslips', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create PDF document (landscape orientation, standard margins)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=landscape(A4),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.25*inch,
        bottomMargin=0.25*inch
    )
    
    # Container for elements
    elements = []
    styles = getSampleStyleSheet()
    
    # Get system configuration
    config = SystemConfiguration.get_settings()
    
    # Simple text styles (no colors)
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=14,
        alignment=TA_CENTER,
        spaceAfter=2,
        fontName='Helvetica-Bold'
    )
    
    normal_center_style = ParagraphStyle(
        'NormalCenter',
        parent=styles['Normal'],
        fontSize=9,
        alignment=TA_CENTER,
        spaceAfter=2
    )
    
    footer_style = ParagraphStyle(
        'FooterStyle',
        parent=styles['Normal'],
        fontSize=7,
        alignment=TA_CENTER
    )
    
    # Parse month_year for period display
    try:
        month_dt = datetime.strptime(payslip.month_year, '%b-%Y')
        last_day = calendar.monthrange(month_dt.year, month_dt.month)[1]
        period_display = f"01-{month_dt.strftime('%b-%Y').upper()} TO {last_day}-{month_dt.strftime('%b-%Y').upper()}"
    except:
        period_display = payslip.month_year
    
    # Add logo with fallback to static default logo
    logo_path = None
    if config.agency_logo and os.path.exists(config.agency_logo.path):
        logo_path = config.agency_logo.path
    else:
        static_logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
        if os.path.exists(static_logo_path):
            logo_path = static_logo_path

    if logo_path:
        try:
            logo = Image(logo_path, width=1.2*inch, height=0.6*inch, kind='proportional')
            logo.hAlign = 'CENTER'
            elements.append(logo)
            elements.append(Spacer(1, 0.03*inch))
        except Exception:
            pass  # If logo fails to load, continue without it
    
    # Header
    elements.append(Paragraph("NATIONAL AMBULANCE SERVICE", header_style))
    elements.append(Spacer(1, 0.04*inch))

    # Snapshot fallbacks to current employee record when payslip snapshot is empty.
    department = payslip.department or payslip.employee.department or ''
    unit = payslip.unit or payslip.employee.unit or ''
    grade = payslip.grade or payslip.employee.grade or ''
    level = payslip.level or payslip.employee.level or ''
    birth_date = payslip.employee.date_of_birth
    is_above_ssnit_age = False
    if birth_date:
        today = date.today()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        is_above_ssnit_age = age >= 60

    # SSNIT is preferred unless employee is above SSNIT age.
    if not is_above_ssnit_age and payslip.employee.ssnit_number:
        staff_identifier = payslip.employee.ssnit_number
    elif payslip.employee.ghana_card:
        staff_identifier = payslip.employee.ghana_card
    else:
        staff_identifier = payslip.employee.ssnit_number or ''
    
    # Employee and Organization Information Table
    info_data = [
        # Header row
        [Paragraph("<b>EMPLOYEE INFORMATION</b>", normal_center_style), '', 
         Paragraph("<b>ORGANIZATION INFORMATION</b>", normal_center_style), ''],
        # Data rows
        [Paragraph("<b>Name:</b>", styles['Normal']), payslip.employee.name or '', 
         Paragraph("<b>Agency:</b>", styles['Normal']), payslip.agency or config.agency_name],
        [Paragraph("<b>Staff ID:</b>", styles['Normal']), payslip.employee.staff_id or '', 
         Paragraph("<b>District:</b>", styles['Normal']), payslip.district or config.default_district],
        [Paragraph("<b>SSNIT/Ghana Card #:</b>", styles['Normal']), staff_identifier, 
         Paragraph("<b>Department:</b>", styles['Normal']), department],
        [Paragraph("<b>Unit:</b>", styles['Normal']), unit,
         Paragraph("<b>Grade:</b>", styles['Normal']), grade],
        [Paragraph("<b>Level:</b>", styles['Normal']), level, '', ''],
        [Paragraph("<b>Period:</b>", styles['Normal']), period_display, '', ''],
    ]
    
    info_table = Table(info_data, colWidths=[1.1*inch, 2.5*inch, 1.3*inch, 2.6*inch])
    info_table.setStyle(TableStyle([
        # Outer border - thick
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        # Inner borders - thin
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        # Header row - merge and center
        ('SPAN', (0, 0), (1, 0)),
        ('SPAN', (2, 0), (3, 0)),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        # Label cells background gray
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#f5f5f5')),
        ('BACKGROUND', (2, 1), (2, -1), colors.HexColor('#f5f5f5')),
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        # Alignment
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.04*inch))
    
    # Financial Breakdown Table
    total_deductions = float(payslip.ssnit_deduction + payslip.tier2_deduction + 
                           payslip.income_tax + payslip.other_deductions)
    
    financial_data = [
        # Header
        [Paragraph("<b>DESCRIPTION</b>", normal_center_style), 
         Paragraph("<b>AMOUNT (GHS)</b>", normal_center_style)],
        # Earnings section header
        [Paragraph("<b>EARNINGS</b>", normal_center_style), ''],
        # Earnings items
        ['    Basic Salary', f'{payslip.basic_salary:.2f}'],
    ]
    
    if payslip.allowances > 0:
        financial_data.append(['    Allowances', f'{payslip.allowances:.2f} '])
    
    # Gross Salary
    financial_data.extend([
        [Paragraph("<b>GROSS SALARY</b>", styles['Normal']), 
         Paragraph(f"<b>{payslip.gross_salary:.2f}</b>", styles['Normal'])],
        # Deductions section header
        [Paragraph("<b>DEDUCTIONS</b>", normal_center_style), ''],
        # Deductions items
        ['    SSNIT Contribution (5.5%)', f'({payslip.ssnit_deduction:.2f})'],
        ['    Tier 2 Pension Contribution', f'({payslip.tier2_deduction:.2f})'],
        ['    Income Tax (PAYE)', f'({payslip.income_tax:.2f})'],
    ])
    
    if payslip.other_deductions > 0:
        financial_data.append(['    Other Deductions', f'({payslip.other_deductions:.2f})'])
    
    # Total Deductions
    financial_data.append([Paragraph("<b>TOTAL DEDUCTIONS</b>", styles['Normal']), 
                          Paragraph(f"<b>({total_deductions:.2f})</b>", styles['Normal'])])
    
    # Net Salary
    financial_data.append([Paragraph("<b>NET SALARY PAYABLE</b>", styles['Normal']), 
                          Paragraph(f"<b>{payslip.net_salary:.2f}</b>", styles['Normal'])])
    
    financial_table = Table(financial_data, colWidths=[5.5*inch, 2*inch])
    financial_table.setStyle(TableStyle([
        # Outer border - thick
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        # Inner borders - thin
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        # Header row
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        # Section headers (EARNINGS, DEDUCTIONS) - merge cells and center
        ('SPAN', (0, 1), (1, 1)),  # EARNINGS row
        ('ALIGN', (0, 1), (0, 1), 'CENTER'),
        ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#e0e0e0')),
        # Find and style DEDUCTIONS header row (dynamic position)
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        # Amount column - right align
        ('ALIGN', (1, 2), (1, -1), 'RIGHT'),
        ('FONTNAME', (1, 2), (1, -1), 'Courier'),
        # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        # Gross salary row - gray background
        ('BACKGROUND', (0, 3 if payslip.allowances > 0 else 3), 
         (-1, 3 if payslip.allowances > 0 else 3), colors.HexColor('#f0f0f0')),
        # Total deductions row - gray background
        ('BACKGROUND', (0, -2), (-1, -2), colors.HexColor('#f0f0f0')),
        # Net salary row - darker gray 
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
        ('FONTSIZE', (0, -1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    #  Need to add DEDUCTIONS header styling dynamically
    deductions_row = 4 if payslip.allowances > 0 else 4
    financial_table.setStyle(TableStyle([
        ('SPAN', (0, deductions_row), (1, deductions_row)),
        ('ALIGN', (0, deductions_row), (0, deductions_row), 'CENTER'),
        ('BACKGROUND', (0, deductions_row), (0, deductions_row), colors.HexColor('#e0e0e0')),
    ]))
    
    elements.append(financial_table)
    elements.append(Spacer(1, 0.04*inch))
    
    # Payment Mode Table 
    payment_mode_text = payslip.payment_mode or "Bank Transfer"
    payment_data = [[Paragraph("<b>Payment Mode:</b>", styles['Normal']), payment_mode_text]]
    payment_table = Table(payment_data, colWidths=[1.3*inch, 6.2*inch])
    payment_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 2, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f5f5f5')),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(payment_table)
    
    # Footer
    elements.append(Spacer(1, 0.05*inch))
    if payslip.generated_by:
        generated_by_name = payslip.generated_by.get_full_name() or payslip.generated_by.username
    else:
        generated_by_name = "Deleted user"

    footer_text = f"""<b>This is a computer-generated payslip</b><br/>
        Generated on {payslip.generated_at.strftime('%d %b %Y at %H:%M')} by {generated_by_name} | Payslip ID: #{payslip.id}"""
    
    footer_para = Paragraph(footer_text, footer_style)
    elements.append(footer_para)
    
    # Build PDF
    doc.build(elements)
    
    return filepath, filename
