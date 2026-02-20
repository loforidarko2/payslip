from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    """Extended user creation form to include role and staff_id"""
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('role', 'staff_id', 'first_name', 'last_name', 'email', 
                                              'department', 'unit', 'grade', 'level', 'is_active')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        
        # Make some fields optional for form validation if model allows blank, 
        # but stylistically we handle them in template
        self.fields['email'].required = True
        self.fields['role'].required = True

class StaffIdPasswordResetForm(forms.Form):
    """Form to handle password reset request via Staff ID"""
    staff_id = forms.CharField(
        label="Staff ID",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your Staff ID'})
    )
    
    def clean_staff_id(self):
        staff_id = self.cleaned_data['staff_id']
        if not CustomUser.objects.filter(staff_id=staff_id, is_active=True).exists():
            # For security, we might want to not reveal if ID exists, but for internal app usability:
            raise ValidationError("No active account found with this Staff ID.")
        return staff_id
    
    def get_user(self):
        staff_id = self.cleaned_data.get('staff_id')
        return CustomUser.objects.filter(staff_id=staff_id).first()
