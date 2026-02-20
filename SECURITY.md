# Security Guide

This document reflects the current Django project layout and runtime settings.

## Security-Relevant Project Structure

```text
payslip/
|- payslip/settings.py       # Core security configuration
|- accounts/                 # Authentication, role logic, custom auth backend
|- payroll/                  # Payslip access control and approval workflow
|- staff/                    # Employee data management
|- core_config/              # Dynamic configuration model/commands
|- media/                    # Generated PDFs and uploads (sensitive)
|- staticfiles/              # Collected static output
|- .env                      # Secrets and environment-specific config (do not commit)
`- db.sqlite3                # Local database (do not commit in production workflows)
```

## Environment Variables
Set in `.env`:

```env
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
```

## Current Security Settings (from `payslip/settings.py`)
- `SECRET_KEY` is loaded from environment (`python-decouple`).
- `DEBUG` defaults to `False`.
- `ALLOWED_HOSTS` is loaded from environment as CSV.
- CSRF middleware is enabled (`django.middleware.csrf.CsrfViewMiddleware`).
- Clickjacking protection is enabled (`XFrameOptionsMiddleware`).
- Custom user model is enabled: `accounts.CustomUser`.
- Custom auth backend is active: `accounts.auth_backends.UsernameAuthBackend`.
- Session timeout is 30 minutes: `SESSION_COOKIE_AGE = 1800`.

## Production Checklist
1. Keep `.env`, database files, and generated payslips out of version control.
2. Use a strong, unique `SECRET_KEY` in production.
3. Keep `DEBUG=False` in production at all times.
4. Set explicit production hostnames in `ALLOWED_HOSTS`.
5. Serve traffic over HTTPS and terminate TLS at the edge/proxy.
6. Store `media/` on secured storage with backup and access controls.
7. Restrict admin account creation and rotate credentials regularly.
8. Run dependency updates and apply Django security patches promptly.

## Recommended Hardening (Not Yet Explicitly Set)
- Set secure cookie flags (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`).
- Configure HSTS (`SECURE_HSTS_SECONDS`, include subdomains if applicable).
- Enable `SECURE_SSL_REDIRECT` when TLS is available.
- Use a managed production database (for example PostgreSQL) with least-privilege credentials.

## Vulnerability Reporting
Report security issues privately to the maintainers/IT team. Do not open public issues for undisclosed vulnerabilities.
