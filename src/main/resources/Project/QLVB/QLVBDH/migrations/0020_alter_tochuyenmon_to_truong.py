from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("QLVBDH", "0019_tochuyenmon_to_truong"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tochuyenmon",
            name="to_truong",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="to_chuyen_mon_phu_trach",
                to="QLVBDH.giaovien",
            ),
        ),
    ]
