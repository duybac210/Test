from django.db import migrations, models
import django.db.models.deletion


def _next_teacher_code(giao_vien_model):
    max_number = 0
    for ma_gv in giao_vien_model.objects.filter(ma_gv__startswith="GV").values_list("ma_gv", flat=True):
        try:
            max_number = max(max_number, int(str(ma_gv).replace("GV", "")))
        except ValueError:
            continue

    while True:
        max_number += 1
        candidate = f"GV{max_number:06d}"
        if not giao_vien_model.objects.filter(ma_gv=candidate).exists():
            return candidate


def populate_to_truong(apps, schema_editor):
    ToChuyenMon = apps.get_model("QLVBDH", "ToChuyenMon")
    GiaoVien = apps.get_model("QLVBDH", "GiaoVien")
    VaiTro = apps.get_model("QLVBDH", "VaiTro")

    truong_bo_mon_role_ids = list(
        VaiTro.objects.filter(ten_vai_tro__iregex=r"^(To truong|Truong bo mon)$").values_list("pk", flat=True)
    )

    for to_chuyen_mon in ToChuyenMon.objects.filter(to_truong__isnull=True):
        candidate = None
        if truong_bo_mon_role_ids:
            candidate = (
                GiaoVien.objects.filter(ma_to=to_chuyen_mon, vai_tros__in=truong_bo_mon_role_ids)
                .order_by("ho_ten")
                .distinct()
                .first()
            )
        if candidate is None:
            candidate = GiaoVien.objects.filter(ma_to=to_chuyen_mon).order_by("ho_ten").first()
        if candidate is None:
            candidate = GiaoVien.objects.create(
                ma_gv=_next_teacher_code(GiaoVien),
                ho_ten=f"To truong {to_chuyen_mon.ten_to}",
                ma_to=to_chuyen_mon,
            )
        to_chuyen_mon.to_truong_id = candidate.pk
        to_chuyen_mon.save(update_fields=["to_truong"])


class Migration(migrations.Migration):
    dependencies = [
        ("QLVBDH", "0018_alter_giaovien_ma_gv"),
    ]

    operations = [
        migrations.AddField(
            model_name="tochuyenmon",
            name="to_truong",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="to_chuyen_mon_phu_trach",
                to="QLVBDH.giaovien",
            ),
        ),
        migrations.RunPython(populate_to_truong, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="tochuyenmon",
            name="to_truong",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="to_chuyen_mon_phu_trach",
                to="QLVBDH.giaovien",
            ),
        ),
    ]
