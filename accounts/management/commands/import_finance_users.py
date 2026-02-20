import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from accounts.models import CustomUser
from .password_utils import resolve_default_password


class Command(BaseCommand):
    help = "Import/update finance users from CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            default="stafff (3).csv",
            help="Path to CSV file (default: stafff (3).csv)",
        )
        parser.add_argument(
            "--default-password",
            default="",
            help="Default password for newly created users",
        )

    @staticmethod
    def _pick(row, *keys):
        lowered = {k.strip().lower(): v for k, v in row.items()}
        for key in keys:
            value = lowered.get(key.lower())
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    @staticmethod
    def _is_finance_row(row):
        role = Command._pick(row, "role")
        station = Command._pick(row, "station_name", "station")
        region = Command._pick(row, "region")
        blob = " ".join([role, station, region]).lower()
        return "finance" in blob

    def handle(self, *args, **options):
        default_password = resolve_default_password(options["default_password"])

        csv_path = Path(options["file"])
        if not csv_path.exists():
            raise CommandError(f"CSV file not found: {csv_path}")

        created = 0
        updated = 0
        skipped = 0
        imported_rows = []

        with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            self._validate_headers(reader.fieldnames)

            with transaction.atomic():
                for row in reader:
                    if not self._is_finance_row(row):
                        continue

                    parsed = self._parse_row(row)
                    if parsed is None:
                        skipped += 1
                        continue

                    staff_id, full_name, email, user_defaults = parsed
                    was_created = self._upsert_finance_user(
                        staff_id=staff_id,
                        user_defaults=user_defaults,
                        default_password=default_password,
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

                    imported_rows.append({
                        "staff_id": staff_id,
                        "role": "finance",
                        "full_name": full_name,
                        "email": email,
                    })

        self.stdout.write(self.style.SUCCESS(f"Created: {created}, Updated: {updated}, Skipped: {skipped}"))
        if imported_rows:
            self.stdout.write("\nImported finance users (staff id, role, full name, email):")
            for row in imported_rows:
                self.stdout.write(
                    f"- {row['staff_id']}, {row['role']}, {row['full_name']}, {row['email']}"
                )
        else:
            self.stdout.write("No finance users found in CSV.")

    @staticmethod
    def _validate_headers(fieldnames):
        csv_headers = {h.strip().lower() for h in (fieldnames or [])}
        has_staff_id = "staff_id" in csv_headers
        has_role = "role" in csv_headers
        has_name = "full_name" in csv_headers or "fullname" in csv_headers or "name" in csv_headers
        has_email = "email" in csv_headers or "email:" in csv_headers
        if not (has_staff_id and has_role and has_name and has_email):
            raise CommandError(
                "CSV must include staff_id, role, name/full_name, and email/email: headers"
            )

    def _parse_row(self, row):
        staff_id = self._pick(row, "staff_id")
        full_name = self._pick(row, "full_name", "fullname", "name")
        email = self._pick(row, "email", "email:")

        if not staff_id or staff_id.lower() in {"bulk", "staff"}:
            return None
        if staff_id.upper().startswith("CA") or staff_id.upper().startswith("CAS"):
            return None

        names = full_name.split()
        first_name = names[0] if names else ""
        last_name = " ".join(names[1:]) if len(names) > 1 else ""
        user_defaults = {
            "role": "finance",
            "staff_id": staff_id,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "is_active": True,
        }
        return staff_id, full_name, email, user_defaults

    @staticmethod
    def _upsert_finance_user(staff_id, user_defaults, default_password):
        user = CustomUser.objects.filter(username=staff_id).first()
        if user is None:
            CustomUser.objects.create_user(
                username=staff_id,
                password=default_password,
                **user_defaults,
            )
            return True

        for key, value in user_defaults.items():
            setattr(user, key, value)
        user.save()
        return False
