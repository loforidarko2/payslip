from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("staff", "0003_employee_separation_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="employee",
            name="bmc",
        ),
    ]
