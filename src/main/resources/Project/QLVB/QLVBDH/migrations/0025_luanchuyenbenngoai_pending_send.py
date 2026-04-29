from django.db import migrations, models


def set_pending_for_unspecified_sends(apps, schema_editor):
    LuanChuyenBenNgoai = apps.get_model("QLVBDH", "LuanChuyenBenNgoai")
    for item in LuanChuyenBenNgoai.objects.all():
        if item.trang_thai_gui != "Da gui":
            item.trang_thai_gui = "Cho gui"
            item.thoi_gian_gui = None
            item.save(update_fields=["trang_thai_gui", "thoi_gian_gui"])


class Migration(migrations.Migration):
    dependencies = [
        ("QLVBDH", "0024_alter_vanbanden_file_van_ban_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="luanchuyenbenngoai",
            name="thoi_gian_gui",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="luanchuyenbenngoai",
            name="trang_thai_gui",
            field=models.CharField(
                choices=[("Da gui", "Da gui"), ("Gui loi", "Gui loi"), ("Cho gui", "Cho gui")],
                default="Cho gui",
                max_length=50,
            ),
        ),
        migrations.RunPython(set_pending_for_unspecified_sends, migrations.RunPython.noop),
    ]
