from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("QLVBDH", "0017_phancongxuly_nguoi_phan_cong_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="giaovien",
            name="ma_gv",
            field=models.CharField(blank=True, max_length=10, primary_key=True, serialize=False),
        ),
    ]
