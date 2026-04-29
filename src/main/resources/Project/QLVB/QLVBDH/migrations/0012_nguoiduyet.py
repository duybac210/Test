import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("QLVBDH", "0011_tochuyenmon_giaovien_ma_to"),
    ]

    operations = [
        migrations.CreateModel(
            name="XuLy",
            fields=[
                ("ma_xu_ly", models.CharField(blank=True, max_length=10, primary_key=True, serialize=False)),
                ("thoi_gian_ky", models.DateTimeField(blank=True, null=True)),
                ("trang_thai_ky", models.CharField(max_length=100)),
                (
                    "ma_gv",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="xu_ly_ky_van_bans",
                        to="QLVBDH.giaovien",
                    ),
                ),
                (
                    "ma_vb_di",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="xu_lys",
                        to="QLVBDH.vanbandi",
                    ),
                ),
                (
                    "vai_tro_ky",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="xu_lys",
                        to="QLVBDH.vaitro",
                    ),
                ),
            ],
            options={
                "verbose_name": "Xử lý",
                "verbose_name_plural": "Xử lý",
                "db_table": "XuLy",
                "ordering": ["ma_vb_di_id", "thoi_gian_ky", "ma_xu_ly"],
            },
        ),
    ]
