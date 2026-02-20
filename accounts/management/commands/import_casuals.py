import random
import string

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

from staff.models import Employee


class Command(BaseCommand):
    help = "Import casual employees from two Excel files and merge data"

    HRMIS_FILE = "HRMIS CASUALS DETAILS .xlsx"
    COMP_FILE = "Conputation Allowance Adjustment 2025.xlsx"
    COMP_DEFAULT_SALARY_COL = "PROPOSED BASIC SALARY"

    def read_excel_smart(self, filepath):
        """Read excel and find the header row containing NAME."""
        df = pd.read_excel(filepath, header=None)
        header_index = -1
        for i, row in df.iterrows():
            values = [str(val).strip().upper() for val in row.values if pd.notnull(val)]
            if "NAME" in values:
                header_index = i
                break

        if header_index == -1:
            raise ValueError(f"Could not find 'NAME' column in {filepath}")

        df = pd.read_excel(filepath, header=header_index)
        df.columns = [str(c).strip() for c in df.columns]
        return df

    @staticmethod
    def clean_name(name):
        if pd.isna(name):
            return ""
        normalized = str(name).strip().upper()
        normalized = normalized.translate(str.maketrans("", "", ".,"))
        return " ".join(normalized.split())

    @staticmethod
    def _sanitize_name_rows(df, remove_total=False):
        filtered = df[df["NAME"].notna()]
        filtered = filtered[filtered["NAME"].astype(str).str.upper() != "NAME"]
        if remove_total:
            filtered = filtered[filtered["NAME"].astype(str).str.upper() != "TOTAL"]
        return filtered

    def _load_hrmis(self):
        self.stdout.write(f"Reading {self.HRMIS_FILE}...")
        try:
            df_hrmis = self.read_excel_smart(self.HRMIS_FILE)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            self.stdout.write(self.style.ERROR(f"Error reading {self.HRMIS_FILE}: {exc}"))
            return None

        df_hrmis = self._sanitize_name_rows(df_hrmis)
        self.stdout.write(f"Found {len(df_hrmis)} records in HRMIS.")
        return df_hrmis

    def _load_computation(self):
        self.stdout.write(f"Reading {self.COMP_FILE}...")
        try:
            df_comp = self.read_excel_smart(self.COMP_FILE)
        except (FileNotFoundError, ValueError, KeyError) as exc:
            self.stdout.write(self.style.ERROR(f"Error reading {self.COMP_FILE}: {exc}"))
            return None

        df_comp = self._sanitize_name_rows(df_comp, remove_total=True)
        self.stdout.write(f"Found {len(df_comp)} records in Computation.")
        return df_comp

    def _resolve_salary_column(self, df_comp):
        salary_col = self.COMP_DEFAULT_SALARY_COL
        if salary_col in df_comp.columns:
            return salary_col

        for column in df_comp.columns:
            name = str(column).upper()
            if "PROPOSED" in name and "SALARY" in name:
                return column
        return salary_col

    def _prepare_merged_data(self, df_hrmis, df_comp):
        df_hrmis["clean_name"] = df_hrmis["NAME"].apply(self.clean_name)
        df_comp["clean_name"] = df_comp["NAME"].apply(self.clean_name)

        salary_col = self._resolve_salary_column(df_comp)
        self.stdout.write("Merging data...")
        merged = pd.merge(
            df_hrmis,
            df_comp[["clean_name", salary_col]],
            on="clean_name",
            how="left",
            validate="m:m",
        )
        return merged, salary_col

    @staticmethod
    def _build_salary(row, salary_col):
        if pd.notnull(row.get(salary_col)):
            return row[salary_col]
        if pd.notnull(row.get("MONTHLY BASIC SALARY")):
            return row["MONTHLY BASIC SALARY"]
        return 0

    @staticmethod
    def _generate_unique_staff_id():
        staff_id = "CAS" + "".join(random.choices(string.digits, k=5))
        while Employee.objects.filter(staff_id=staff_id).exists():
            staff_id = "CAS" + "".join(random.choices(string.digits, k=5))
        return staff_id

    def _create_employee(self, row, salary_col):
        name = str(row["NAME_x"]).strip() if "NAME_x" in row else str(row["NAME"]).strip()
        staff_id = self._generate_unique_staff_id()
        salary = self._build_salary(row, salary_col)

        Employee.objects.create(
            staff_id=staff_id,
            name=name,
            status=str(row.get("STATUS", "OTHER")).strip(),
            ssnit_number=str(row.get("SSNIT #", "")).strip(),
            ghana_card=str(row.get("GHANA CARD", "")).strip(),
            bank_name=str(row.get("BANK", "")).strip(),
            bank_account=str(row.get("NUMBER", "")).strip(),
            bank_branch=str(row.get("BRANCH", "")).strip(),
            contact=str(row.get("CONTACT", "")).strip(),
            monthly_salary=salary if salary else 0,
        )

    def handle(self, *args, **options):
        df_hrmis = self._load_hrmis()
        if df_hrmis is None:
            return

        df_comp = self._load_computation()
        if df_comp is None:
            return

        df_merged, salary_col = self._prepare_merged_data(df_hrmis, df_comp)

        success_count = 0
        error_count = 0
        with transaction.atomic():
            self.stdout.write("Clearing existing casual employee records...")
            Employee.objects.filter(staff_id__startswith="CAS").delete()

            for _, row in df_merged.iterrows():
                try:
                    self._create_employee(row, salary_col)
                    success_count += 1
                except (ValueError, TypeError, KeyError) as exc:
                    self.stdout.write(self.style.ERROR(f"Error processing {row.get('NAME')}: {exc}"))
                    error_count += 1

        self.stdout.write(self.style.SUCCESS(f"Import complete: {success_count} success, {error_count} errors."))
