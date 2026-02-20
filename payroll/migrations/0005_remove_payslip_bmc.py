from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("payroll", "0004_payslipaudit"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="payslip",
            name="bmc",
        ),
    ]
