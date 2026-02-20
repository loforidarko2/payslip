"""
Custom authentication backends for the payslip system.

NOTE: Both system users and casual employees can log into the system.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class UsernameAuthBackend(ModelBackend):
    """
    Standard username/email authentication for system users.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        # Try by username (case-insensitive)
        user = User.objects.filter(username__iexact=username).first()
        
        if not user:
            # Try by email (case-insensitive)
            user = User.objects.filter(email__iexact=username).first()
            
        if not user:
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
