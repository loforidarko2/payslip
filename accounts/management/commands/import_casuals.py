import pandas as pd
import random
import string
from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import CustomUser
from staff.models import Employee

class Command(BaseCommand):
    help = 'Import casual employees from two Excel files and merge data'

    def read_excel_smart(self, filepath):
        """Read excel and find the header row containing 'NAME'"""
        df = pd.read_excel(filepath, header=None)
        header_index = -1
        for i, row in df.iterrows():
            if 'NAME' in [str(val).strip().upper() for val in row.values if pd.notnull(val)]:
                header_index = i
                break
        
        if header_index == -1:
            raise ValueError(f"Could not find 'NAME' column in {filepath}")
            
        # Re-read with correct header
        df = pd.read_excel(filepath, header=header_index)
        # Clean columns: strip and normalize
        df.columns = [str(c).strip() for c in df.columns]
        return df

    def handle(self, *args, **options):
        hrmis_file = 'HRMIS CASUALS DETAILS .xlsx'
        comp_file = 'Conputation Allowance Adjustment 2025.xlsx'

        self.stdout.write(f"Reading {hrmis_file}...")
        try:
            df_hrmis = self.read_excel_smart(hrmis_file)
            # Remove rows where NAME is NaN or 'NAME'
            df_hrmis = df_hrmis[df_hrmis['NAME'].notna()]
            df_hrmis = df_hrmis[df_hrmis['NAME'].astype(str).str.upper() != 'NAME']
            self.stdout.write(f"Found {len(df_hrmis)} records in HRMIS.")
        except (FileNotFoundError, ValueError, KeyError) as e:
            self.stdout.write(self.style.ERROR(f"Error reading {hrmis_file}: {e}"))
            return

        self.stdout.write(f"Reading {comp_file}...")
        try:
            df_comp = self.read_excel_smart(comp_file)
            # Remove rows where NAME is NaN, 'TOTAL', or 'NAME'
            df_comp_filtered = df_comp[df_comp['NAME'].notna()]
            df_comp_filtered = df_comp_filtered[df_comp_filtered['NAME'].astype(str).str.upper() != 'TOTAL']
            df_comp_filtered = df_comp_filtered[df_comp_filtered['NAME'].astype(str).str.upper() != 'NAME']
            self.stdout.write(f"Found {len(df_comp_filtered)} records in Computation.")
            df_comp = df_comp_filtered
        except (FileNotFoundError, ValueError, KeyError) as e:
            self.stdout.write(self.style.ERROR(f"Error reading {comp_file}: {e}"))
            return

        # Prepare for merging - clean names robustly
        def clean_name(name):
            if pd.isna(name): return ""
            s = str(name).strip().upper()
            s = s.translate(str.maketrans('', '', '.,'))
            return " ".join(s.split())

        df_hrmis['clean_name'] = df_hrmis['NAME'].apply(clean_name)
        df_comp['clean_name'] = df_comp['NAME'].apply(clean_name)

        # Merge data
        self.stdout.write("Merging data...")
        # Prioritize 'PROPOSED BASIC SALARY' column
        comp_salary_col = 'PROPOSED BASIC SALARY'
        if comp_salary_col not in df_comp.columns:
            # Try to find a header containing 'PROPOSED' and 'SALARY'
            for c in df_comp.columns:
                if 'PROPOSED' in str(c).upper() and 'SALARY' in str(c).upper():
                    comp_salary_col = c
                    break
        
        df_merged = pd.merge(df_hrmis, df_comp[['clean_name', comp_salary_col]], on='clean_name', how='left')

        success_count = 0
        error_count = 0

        with transaction.atomic():
            # Clear existing casual employee records (not users, since they shouldn't exist)
            self.stdout.write("Clearing existing casual employee records...")
            Employee.objects.filter(staff_id__startswith='CAS').delete()

            for _, row in df_merged.iterrows():
                try:
                    name = str(row['NAME_x']).strip() if 'NAME_x' in row else str(row['NAME']).strip()
                    
                    # Generate random Staff ID
                    staff_id = "CAS" + "".join(random.choices(string.digits, k=5))
                    while Employee.objects.filter(staff_id=staff_id).exists():
                        staff_id = "CAS" + "".join(random.choices(string.digits, k=5))

                    # Salary prioritization: Proposed > Basic in HRMIS
                    # row[comp_salary_col] is the proposed salary from computation sheet
                    salary = 0
                    if pd.notnull(row.get(comp_salary_col)):
                        salary = row[comp_salary_col]
                    elif pd.notnull(row.get('MONTHLY BASIC SALARY')):
                        salary = row['MONTHLY BASIC SALARY']

                    # Create Employee ONLY (no user account for casuals)
                    Employee.objects.create(
                        staff_id=staff_id,
                        name=name,
                        status=str(row.get('STATUS', 'OTHER')).strip(),
                        ssnit_number=str(row.get('SSNIT #', '')).strip(),
                        ghana_card=str(row.get('GHANA CARD', '')).strip(),
                        bank_name=str(row.get('BANK', '')).strip(),
                        bank_account=str(row.get('NUMBER', '')).strip(),
                        bank_branch=str(row.get('BRANCH', '')).strip(),
                        contact=str(row.get('CONTACT', '')).strip(),
                        monthly_salary=salary if salary else 0,
                    )

                    success_count += 1
                except (ValueError, TypeError, KeyError) as e:
                    self.stdout.write(self.style.ERROR(f"Error processing {row.get('NAME')}: {e}"))
                    error_count += 1

        self.stdout.write(self.style.SUCCESS(f"Import complete: {success_count} success, {error_count} errors."))
