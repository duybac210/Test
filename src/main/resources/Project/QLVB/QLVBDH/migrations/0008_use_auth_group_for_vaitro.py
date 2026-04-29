import django.db.models.deletion
from django.db import migrations, models


OLD_NHOM_PREFIX = "NHOM_"
OLD_ROLE_PREFIX = "ROLE_"


def forwards(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    VaiTro = apps.get_model("QLVBDH", "VaiTro")
    NhomVaiTro = apps.get_model("QLVBDH", "NhomVaiTro")
    GiaoVien = apps.get_model("QLVBDH", "GiaoVien")

    for vai_tro in VaiTro.objects.select_related("nhom_vai_tro"):
        nhom = vai_tro.nhom_vai_tro
        if nhom is None:
            continue

        auth_group, _ = Group.objects.get_or_create(name=nhom.ten_nhom_vai_tro)

        old_prefixed_group = Group.objects.filter(name=f"{OLD_NHOM_PREFIX}{nhom.ma_nhom_vai_tro}").first()
        if old_prefixed_group is not None:
            combined_ids = set(auth_group.permissions.values_list("id", flat=True))
            combined_ids.update(old_prefixed_group.permissions.values_list("id", flat=True))
            auth_group.permissions.set(Permission.objects.filter(id__in=combined_ids))

        VaiTro.objects.filter(pk=vai_tro.pk).update(nhom_quyen_id=auth_group.pk)

    for giao_vien in GiaoVien.objects.select_related("ma_vai_tro__nhom_quyen", "user"):
        if not giao_vien.user_id or not giao_vien.ma_vai_tro_id or not giao_vien.ma_vai_tro.nhom_quyen_id:
            continue

        target_group = giao_vien.ma_vai_tro.nhom_quyen
        giao_vien.user.groups.clear()
        giao_vien.user.groups.add(target_group)

    Group.objects.filter(name__startswith=OLD_NHOM_PREFIX).delete()
    Group.objects.filter(name__startswith=OLD_ROLE_PREFIX).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("QLVBDH", "0007_populate_nhom_vai_tro"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="vaitro",
            name="nhom_quyen",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vai_tros",
                to="auth.group",
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name="vaitro",
            name="nhom_vai_tro",
        ),
        migrations.DeleteModel(
            name="NhomVaiTro",
        ),
        migrations.AlterField(
            model_name="vaitro",
            name="nhom_quyen",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vai_tros",
                to="auth.group",
            ),
        ),
    ]
