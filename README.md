# National Ambulance Service - Payslip Management System

Django application for employee management, payslip generation, approval workflow, and PDF distribution.

## Tech Stack
- Python 3.14 (project venv currently present in repo)
- Django 5.0.x
- SQLite (default local database)
- ReportLab (PDF generation)
- Pandas/OpenPyXL (bulk import)

## Project Structure (Current)

```text
payslip/
|- accounts/                 # Auth, dashboards, user management, custom auth backend
|  |- management/commands/   # User/data bootstrap and import helpers
|  |- migrations/
|  `- templates/accounts/
|- core_config/              # Dynamic system configuration models/commands
|  |- management/commands/
|  `- migrations/
|- payroll/                  # Payslip generation, approval, PDF preview/download
|  |- migrations/
|  `- templates/payroll/
|- staff/                    # Employee CRUD and employee import flow
|  |- management/commands/
|  |- migrations/
|  `- templates/staff/
|- payslip/                  # Django project package (settings/urls/asgi/wsgi)
|- static/                   # Source static assets
|- staticfiles/              # collectstatic output
|- media/                    # Uploaded/generated media (logos, payslip PDFs)
|- manage.py
|- requirements.txt
|- README.md
`- SECURITY.md
```

## URL Layout (Current)
- `accounts`: `/login/`, `/logout/`, `/dashboard/`, `/users/...`
- `staff`: `/employees/...`
- `payroll`: `/payslip/...`, `/settings/`
- root `/` redirects to `accounts:login`

## Setup (Local)
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure environment variables in `.env`:
   ```env
   SECRET_KEY=change-me
   DEBUG=True
   ALLOWED_HOSTS=127.0.0.1,localhost
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Create admin user:
   ```bash
   python manage.py createsuperuser
   ```
5. Start server:
   ```bash
   python manage.py runserver
   ```

## Notes
- Custom user model: `accounts.CustomUser`.
- Session timeout is configured to 30 minutes (`SESSION_COOKIE_AGE = 1800`).
- `staticfiles/` and `media/` can contain generated/runtime files; do not treat them as source code.
