from django.db import migrations


def create_admin_group_and_role(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    VaiTro = apps.get_model("QLVBDH", "VaiTro")

    group, _ = Group.objects.get_or_create(name="QuanTri")
    group.permissions.set(Permission.objects.all())

    VaiTro.objects.get_or_create(
        ma_vai_tro="ADMIN",
        defaults={"ten_vai_tro": "Quan tri he thong"},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("QLVBDH", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(
            create_admin_group_and_role,
            migrations.RunPython.noop,
        ),
    ]
