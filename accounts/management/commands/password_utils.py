from django.conf import settings
from django.core.management.base import CommandError


def resolve_default_password(option_password=None):
    password = option_password or settings.DEFAULT_USER_PASSWORD
    if not password:
        raise CommandError(
            "No default password provided. Set DEFAULT_USER_PASSWORD or pass --default-password."
        )
    return password
