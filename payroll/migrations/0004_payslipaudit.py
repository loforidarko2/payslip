from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('payroll', '0003_remove_banking_defaults'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PayslipAudit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('edit', 'Edit'), ('revert', 'Revert')], max_length=20)),
                ('old_status', models.CharField(blank=True, max_length=10, null=True)),
                ('new_status', models.CharField(blank=True, max_length=10, null=True)),
                ('reason', models.TextField(blank=True)),
                ('performed_at', models.DateTimeField(auto_now_add=True)),
                ('payslip', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audit_entries', to='payroll.payslip')),
                ('performed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payslip_audits', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Payslip Audit Entry',
                'verbose_name_plural': 'Payslip Audit Entries',
                'ordering': ['-performed_at'],
            },
        ),
    ]

