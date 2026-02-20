from django import forms
from django.core.exceptions import ValidationError
from datetime import date
from .models import Payslip, SystemConfiguration
from staff.models import Employee
from accounts.models import CustomUser


def build_month_year_choices(months_back=24, months_forward=12):
    """Build month-year choices in Mon-YYYY format."""
    today = date.today()
    current_month_index = today.year * 12 + (today.month - 1)
    start_index = current_month_index - months_back
    end_index = current_month_index + months_forward

    choices = []
    for month_index in range(end_index, start_index - 1, -1):
        year = month_index // 12
        month = (month_index % 12) + 1
        value = date(year, month, 1).strftime('%b-%Y')
        choices.append((value, value))
    return choices


class PayslipGenerateForm(forms.Form):
    """Form for generating a single payslip"""
    employee = forms.ModelChoiceField(
        queryset=Employee.objects.filter(staff_id__startswith='CA', is_active=True).order_by('name'),
        label="Select Employee",
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_employee'
        }),
        empty_label="-- Choose an employee --",
        help_text="Select the casual employee to generate payslip for"
    )
    month_year = forms.ChoiceField(
        label="Month/Year",
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    district = forms.CharField(
        max_length=200, 
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="District"
    )
    
    # Employee details (auto-filled, read-only)
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    unit = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    grade = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    level = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'})
    )
    
    # Financials
    basic_salary = forms.DecimalField(
        label="Basic Salary",
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'readonly': 'readonly'
        }),
        help_text="Auto-filled from employee record"
    )
    ssnit_rate = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        help_text="SSNIT Rate (%)"
    )
    tier2_rate = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        help_text="Tier 2 Rate (%)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = SystemConfiguration.get_settings()
        month_year_choices = build_month_year_choices()
        self.fields['month_year'].choices = month_year_choices
        self.fields['month_year'].initial = date.today().strftime('%b-%Y')
        self.fields['district'].initial = config.default_district
        self.fields['ssnit_rate'].initial = config.ssnit_rate
        self.fields['tier2_rate'].initial = config.tier2_rate

class BulkPayslipGenerateForm(forms.Form):
    """Form for bulk generating payslips for all active employees"""
    month_year = forms.ChoiceField(
        choices=[],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Month/Year"
    )
    district = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label="District"
    )
    ssnit_rate = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        label="SSNIT Rate (%)"
    )
    tier2_rate = forms.DecimalField(
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        label="Tier 2 Rate (%)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        config = SystemConfiguration.get_settings()
        month_year_choices = build_month_year_choices()
        self.fields['month_year'].choices = month_year_choices
        self.fields['month_year'].initial = date.today().strftime('%b-%Y')
        self.fields['district'].initial = config.default_district
        self.fields['ssnit_rate'].initial = config.ssnit_rate
        self.fields['tier2_rate'].initial = config.tier2_rate
    
    def clean_month_year(self):
        month_year = self.cleaned_data['month_year']
        return month_year


class SystemConfigurationForm(forms.ModelForm):
    """Form for updating system settings"""
    class Meta:
        model = SystemConfiguration
        fields = [
            'agency_name', 'default_district', 'ssnit_rate', 'tier2_rate',
            'agency_logo', 'address', 'phone', 'email'
        ]
        widgets = {
            'agency_name': forms.TextInput(attrs={'class': 'form-control'}),
            'default_district': forms.TextInput(attrs={'class': 'form-control'}),
            'ssnit_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'tier2_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'agency_logo': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
