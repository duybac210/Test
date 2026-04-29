from django.conf import settings
from django.db import migrations


DEFAULT_GIAO_VIEN_PASSWORD = "giaovien123"
VAI_TRO_GROUP_PREFIX = "ROLE_"


def sync_role_groups_and_teacher_users(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))
    VaiTro = apps.get_model("QLVBDH", "VaiTro")
    GiaoVien = apps.get_model("QLVBDH", "GiaoVien")

    for vai_tro in VaiTro.objects.all():
        group, _ = Group.objects.get_or_create(name=f"{VAI_TRO_GROUP_PREFIX}{vai_tro.ma_vai_tro}")
        if vai_tro.ma_vai_tro == "ADMIN":
            group.permissions.set(Permission.objects.all())

    for giao_vien in GiaoVien.objects.select_related("ma_vai_tro", "user"):
        if giao_vien.user_id:
            user = giao_vien.user
            user.username = giao_vien.ma_gv
        else:
            user, created = User.objects.get_or_create(
                username=giao_vien.ma_gv,
                defaults={"is_staff": True, "is_active": True},
            )
            if created:
                user.set_password(DEFAULT_GIAO_VIEN_PASSWORD)

        user.is_staff = True
        user.is_active = True
        user.first_name = giao_vien.ho_ten
        user.save()

        giao_vien.user = user
        giao_vien.save(update_fields=["user"])

        role_groups = Group.objects.filter(name__startswith=VAI_TRO_GROUP_PREFIX)
        target_group, _ = Group.objects.get_or_create(name=f"{VAI_TRO_GROUP_PREFIX}{giao_vien.ma_vai_tro_id}")
        user.groups.remove(*role_groups.exclude(pk=target_group.pk))
        user.groups.add(target_group)


class Migration(migrations.Migration):

    dependencies = [
        ("QLVBDH", "0004_alter_loaivanban_ma_loai_vb_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(
            sync_role_groups_and_teacher_users,
            migrations.RunPython.noop,
        ),
    ]
