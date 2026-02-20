from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_remove_banking_defaults"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="customuser",
            name="bmc",
        ),
    ]
