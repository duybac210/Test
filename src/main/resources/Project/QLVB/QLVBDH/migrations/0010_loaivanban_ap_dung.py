from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("QLVBDH", "0009_giaovien_multiple_roles"),
    ]

    operations = [
        migrations.AddField(
            model_name="loaivanban",
            name="ap_dung",
            field=models.IntegerField(
                choices=[(0, "Van ban di"), (1, "Van ban den"), (2, "Ca hai")],
                default=2,
            ),
        ),
    ]
