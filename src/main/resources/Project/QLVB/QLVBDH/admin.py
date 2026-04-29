from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group

from .models import (
    GiaoVien,
    LuanChuyenBenNgoai,
    LoaiVanBan,
    MauVanBan,
    MucDoUuTien,
    NhatKyVanBan,
    NoiNhan,
    PhanCongXuLy,
    TepDinhKemVanBanDen,
    TepDinhKemVanBanDi,
    ToChuyenMon,
    VanBanDen,
    VanBanDi,
    XuLy,
)


class FullFieldsAdmin(admin.ModelAdmin):
    def get_fields(self, request, obj=None):
        concrete_fields = [field.name for field in self.model._meta.fields]
        many_to_many_fields = [field.name for field in self.model._meta.many_to_many]
        return concrete_fields + many_to_many_fields


class GiaoVienAdminForm(forms.ModelForm):
    nhom_quyen = forms.ModelMultipleChoiceField(
        queryset=Group.objects.order_by("name"),
        required=False,
        label="Nhom quyen",
    )

    class Meta:
        model = GiaoVien
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.user_id:
            self.fields["nhom_quyen"].initial = self.instance.user.groups.all()

    def save(self, commit=True):
        giao_vien = super().save(commit=commit)
        if giao_vien.user_id:
            giao_vien.user.groups.set(self.cleaned_data["nhom_quyen"])
        return giao_vien


@admin.register(GiaoVien)
class GiaoVienAdmin(admin.ModelAdmin):
    form = GiaoVienAdminForm
    readonly_fields = ("ma_gv", "user")
    fields = ("ma_gv", "user", "ho_ten", "chuc_vu", "ma_to", "trang_thai_tk", "nhom_quyen")
    list_display = ("ma_gv", "ho_ten", "chuc_vu", "ma_to", "danh_sach_nhom_quyen", "trang_thai_tk", "user")
    list_filter = ("ma_to", "chuc_vu", "trang_thai_tk", "user__groups")
    search_fields = ("ma_gv", "ho_ten", "chuc_vu", "ma_to__ten_to", "user__username", "user__groups__name")
    def danh_sach_nhom_quyen(self, obj):
        return obj.ten_nhom_quyen_hien_thi

    danh_sach_nhom_quyen.short_description = "Nhom quyen"


@admin.register(ToChuyenMon)
class ToChuyenMonAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_to",)
    list_display = ("ma_to", "ten_to", "to_truong")
    search_fields = ("ma_to", "ten_to", "to_truong__ma_gv", "to_truong__ho_ten")


@admin.register(LoaiVanBan)
class LoaiVanBanAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_loai_vb",)
    list_display = ("ma_loai_vb", "ten_loai_vb", "ten_viet_tat", "ap_dung", "hien_thi_ap_dung", "twocap", "hien_thi_twocap")
    list_filter = ("ap_dung", "twocap")
    search_fields = ("ma_loai_vb", "ten_loai_vb", "ten_viet_tat")

    def hien_thi_ap_dung(self, obj):
        return obj.get_ap_dung_display()

    hien_thi_ap_dung.short_description = "Ap dung"

    def hien_thi_twocap(self, obj):
        return obj.get_twocap_display()

    hien_thi_twocap.short_description = "So cap duyet"


@admin.register(MauVanBan)
class MauVanBanAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_mau_vb",)
    list_display = ("ma_mau_vb", "ngay_tao", "ten_mau", "ma_loai_vb", "trang_thai")
    list_filter = ("ma_loai_vb", "trang_thai")
    search_fields = ("ma_mau_vb", "ten_mau", "muc_dich")


@admin.register(MucDoUuTien)
class MucDoUuTienAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_muc_do",)
    list_display = ("ma_muc_do", "muc_do")
    search_fields = ("ma_muc_do", "muc_do")


@admin.register(VanBanDen)
class VanBanDenAdmin(FullFieldsAdmin):
    readonly_fields = ("so_vb_den",)
    list_display = (
        "so_vb_den",
        "so_ky_hieu",
        "ma_loai_vb",
        "co_quan_ban_hanh",
        "ma_muc_do",
        "trang_thai_vb_den",
        "ngay_nhan",
    )
    list_filter = ("ma_loai_vb", "ma_muc_do", "trang_thai_vb_den")
    search_fields = ("so_vb_den", "so_ky_hieu", "trich_yeu", "co_quan_ban_hanh")


@admin.register(VanBanDi)
class VanBanDiAdmin(FullFieldsAdmin):
    readonly_fields = ("so_vb_di",)
    list_display = (
        "so_vb_di",
        "so_thu_tu",
        "so_ky_hieu",
        "ma_loai_vb",
        "nguoi_tao",
        "nguoi_ky",
        "ma_muc_do",
        "trang_thai_vb_di",
        "ngay_ban_hanh",
    )
    list_filter = ("ma_loai_vb", "ma_muc_do", "trang_thai_vb_di")
    search_fields = ("so_vb_di", "so_ky_hieu", "trich_yeu", "noi_nhan", "so_thu_tu")


@admin.register(NhatKyVanBan)
class NhatKyVanBanAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_nhat_ky", "thoi_gian_tao")
    list_display = ("ma_nhat_ky", "ma_nguoi_tao", "ma_vb_den", "ma_vb_di", "trang_thai", "thoi_gian_tao")
    list_filter = ("trang_thai",)
    search_fields = ("ma_nhat_ky", "yc_chinh_sua")


@admin.register(PhanCongXuLy)
class PhanCongXuLyAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_xu_ly",)
    list_display = ("ma_xu_ly", "so_vb_den", "so_vb_di", "nguoi_xu_ly", "thoi_han", "trang_thai_xl")
    list_filter = ("trang_thai_xl",)
    search_fields = ("ma_xu_ly", "noi_dung_cd")


@admin.register(XuLy)
class XuLyAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_xu_ly",)
    list_display = ("ma_xu_ly", "ma_vb_di", "ma_gv", "vai_tro_ky", "thoi_gian_ky", "trang_thai_ky")
    list_filter = ("vai_tro_ky", "trang_thai_ky")
    search_fields = ("ma_xu_ly", "ma_vb_di__so_vb_di", "ma_vb_di__so_ky_hieu", "ma_gv__ma_gv", "ma_gv__ho_ten")


@admin.register(NoiNhan)
class NoiNhanAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_noi_nhan",)
    list_display = ("ma_noi_nhan", "ten_noi_nhan", "dia_chi", "so_dien_thoai", "gmail")
    search_fields = ("ma_noi_nhan", "ten_noi_nhan", "dia_chi", "so_dien_thoai", "gmail", "thong_tin_khac")


@admin.register(TepDinhKemVanBanDen)
class TepDinhKemVanBanDenAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_tep", "ngay_tao")
    list_display = ("ma_tep", "so_vb_den", "tep_tin", "thu_tu", "ngay_tao")
    list_filter = ("ngay_tao",)
    search_fields = ("ma_tep", "so_vb_den__so_vb_den", "so_vb_den__so_ky_hieu", "tep_tin")


@admin.register(TepDinhKemVanBanDi)
class TepDinhKemVanBanDiAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_tep", "ngay_tao")
    list_display = ("ma_tep", "so_vb_di", "loai_tep", "tep_tin", "thu_tu", "ngay_tao")
    list_filter = ("loai_tep", "ngay_tao")
    search_fields = ("ma_tep", "so_vb_di__so_vb_di", "so_vb_di__so_ky_hieu", "tep_tin")


@admin.register(LuanChuyenBenNgoai)
class LuanChuyenBenNgoaiAdmin(FullFieldsAdmin):
    readonly_fields = ("ma_luan_chuyen", "thoi_gian_gui")
    list_display = (
        "ma_luan_chuyen",
        "ma_vb_di",
        "ma_noi_nhan",
        "nguoi_thuc_hien",
        "trang_thai_gui",
        "thoi_gian_gui",
    )
    list_filter = ("trang_thai_gui", "thoi_gian_gui")
    search_fields = (
        "ma_luan_chuyen",
        "ma_vb_di__so_vb_di",
        "ma_vb_di__so_ky_hieu",
        "ma_noi_nhan__ma_noi_nhan",
        "ma_noi_nhan__ten_noi_nhan",
        "nguoi_thuc_hien__ma_gv",
        "nguoi_thuc_hien__ho_ten",
    )
