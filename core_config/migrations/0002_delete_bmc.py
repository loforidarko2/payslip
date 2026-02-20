from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core_config", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(
            name="BMC",
        ),
    ]
