from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    """Form for creating and editing employees"""
    class Meta:
        model = Employee
        exclude = ['separation_reason', 'separated_at', 'separated_by']
        widgets = {
            'date_of_hire': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'monthly_salary': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if 'class' not in self.fields[field].widget.attrs:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

class ImportEmployeeForm(forms.Form):
    """Form to import employees from Excel"""
    file = forms.FileField(
        label="Select Excel File",
        help_text="Upload an Excel file (.xlsx) with employee data",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx, .xls'})
    )
    
    def clean_file(self):
        file = self.cleaned_data['file']
        ext = file.name.split('.')[-1].lower()
        if ext not in ['xlsx', 'xls', 'csv']:
            raise forms.ValidationError("Unsupported file extension. Please upload an Excel or CSV file.")
        return file
