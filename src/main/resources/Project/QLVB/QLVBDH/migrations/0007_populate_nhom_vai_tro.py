import django.db.models.deletion
from django.db import migrations, models


NHOM_VAI_TRO_GROUP_PREFIX = "NHOM_"
OLD_ROLE_GROUP_PREFIX = "ROLE_"


def populate_nhom_vai_tro(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    VaiTro = apps.get_model("QLVBDH", "VaiTro")
    NhomVaiTro = apps.get_model("QLVBDH", "NhomVaiTro")
    GiaoVien = apps.get_model("QLVBDH", "GiaoVien")

    for vai_tro in VaiTro.objects.all():
        nhom, _ = NhomVaiTro.objects.get_or_create(
            ma_nhom_vai_tro=vai_tro.ma_vai_tro,
            defaults={"ten_nhom_vai_tro": vai_tro.ten_vai_tro},
        )
        VaiTro.objects.filter(pk=vai_tro.pk).update(nhom_vai_tro=nhom)

        old_group = Group.objects.filter(name=f"{OLD_ROLE_GROUP_PREFIX}{vai_tro.ma_vai_tro}").first()
        new_group, _ = Group.objects.get_or_create(name=f"{NHOM_VAI_TRO_GROUP_PREFIX}{nhom.ma_nhom_vai_tro}")
        if old_group is not None:
            new_group.permissions.set(old_group.permissions.all())

    for giao_vien in GiaoVien.objects.select_related("ma_vai_tro__nhom_vai_tro", "user"):
        if giao_vien.user_id and giao_vien.ma_vai_tro_id and giao_vien.ma_vai_tro.nhom_vai_tro_id:
            target_group, _ = Group.objects.get_or_create(
                name=f"{NHOM_VAI_TRO_GROUP_PREFIX}{giao_vien.ma_vai_tro.nhom_vai_tro_id}"
            )
            old_groups = Group.objects.filter(name__startswith=OLD_ROLE_GROUP_PREFIX)
            new_groups = Group.objects.filter(name__startswith=NHOM_VAI_TRO_GROUP_PREFIX)
            giao_vien.user.groups.remove(*old_groups)
            giao_vien.user.groups.remove(*new_groups.exclude(pk=target_group.pk))
            giao_vien.user.groups.add(target_group)


class Migration(migrations.Migration):

    dependencies = [
        ("QLVBDH", "0006_nhomvaitro_vaitro_nhom_vai_tro"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(
            populate_nhom_vai_tro,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="vaitro",
            name="nhom_vai_tro",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="vai_tros",
                to="QLVBDH.nhomvaitro",
            ),
        ),
    ]
