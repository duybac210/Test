from django.db import migrations, models


def copy_existing_roles(apps, schema_editor):
    GiaoVien = apps.get_model("QLVBDH", "GiaoVien")

    for giao_vien in GiaoVien.objects.exclude(ma_vai_tro__isnull=True):
        giao_vien.vai_tros.add(giao_vien.ma_vai_tro)


class Migration(migrations.Migration):
    dependencies = [
        ("QLVBDH", "0008_use_auth_group_for_vaitro"),
    ]

    operations = [
        migrations.AddField(
            model_name="giaovien",
            name="vai_tros",
            field=models.ManyToManyField(blank=True, related_name="giao_viens", to="QLVBDH.vaitro"),
        ),
        migrations.RunPython(copy_existing_roles, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="giaovien",
            name="ma_vai_tro",
        ),
    ]
