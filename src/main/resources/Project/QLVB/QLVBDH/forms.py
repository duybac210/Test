from django import forms
from django.contrib.auth.models import Group

from .models import (
    GiaoVien,
    LoaiVanBan,
    MauVanBan,
    MucDoUuTien,
    TepDinhKemVanBanDen,
    TepDinhKemVanBanDi,
    ToChuyenMon,
    VanBanDen,
    VanBanDi,
)


INCOMING_AP_DUNG_VALUES = [1, 2]
OUTGOING_AP_DUNG_VALUES = [0, 2]


class LoaiVanBanChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.ten_loai_vb


class MucDoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.muc_do


class GiaoVienChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.ho_ten


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if not data:
            return []
        if isinstance(data, (list, tuple)):
            return [single_file_clean(item, initial) for item in data]
        return [single_file_clean(data, initial)]


class VanBanDenForm(forms.ModelForm):
    ma_loai_vb = LoaiVanBanChoiceField(queryset=LoaiVanBan.objects.none(), label="Loại văn bản")
    ma_muc_do = MucDoChoiceField(queryset=MucDoUuTien.objects.none(), label="Mức độ ưu tiên")
    file_van_ban = forms.FileField(required=False)
    tep_dinh_kem_uploads = MultipleFileField(required=False)

    class Meta:
        model = VanBanDen
        fields = [
            "ngay_nhan",
            "ngay_ky",
            "so_ky_hieu",
            "ma_loai_vb",
            "ma_muc_do",
            "co_quan_ban_hanh",
            "trich_yeu",
        ]
        labels = {
            "ngay_nhan": "Ngày nhận văn bản",
            "ngay_ky": "Ngày ký",
            "so_ky_hieu": "Số ký hiệu",
            "ma_loai_vb": "Loại văn bản",
            "ma_muc_do": "Mức độ ưu tiên",
            "co_quan_ban_hanh": "Cơ quan ban hành",
            "trich_yeu": "Trích yếu văn bản",
        }
        widgets = {
            "ngay_nhan": forms.DateInput(
                attrs={"type": "date", "class": "form-control", "placeholder": "Chọn ngày nhận văn bản"}
            ),
            "ngay_ky": forms.DateInput(
                attrs={"type": "date", "class": "form-control", "placeholder": "Chọn ngày ký"}
            ),
            "so_ky_hieu": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nhập số ký hiệu văn bản"}
            ),
            "ma_loai_vb": forms.Select(attrs={"class": "form-control"}),
            "ma_muc_do": forms.Select(attrs={"class": "form-control"}),
            "co_quan_ban_hanh": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nhập cơ quan ban hành"}
            ),
            "trich_yeu": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Nhập trích yếu văn bản"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ma_loai_vb"].queryset = LoaiVanBan.objects.filter(ap_dung__in=INCOMING_AP_DUNG_VALUES).order_by(
            "ma_loai_vb"
        )
        self.fields["ma_muc_do"].queryset = MucDoUuTien.objects.order_by("ma_muc_do")
        self.fields["ma_loai_vb"].empty_label = "Chọn mã loại văn bản"
        self.fields["ma_muc_do"].empty_label = "Chọn mã mức độ"
        self.fields["ngay_nhan"].required = True
        self.fields["file_van_ban"].label = "File văn bản"
        self.fields["file_van_ban"].widget = forms.FileInput(
            attrs={"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "id": "id_file_van_ban"}
        )
        self.fields["tep_dinh_kem_uploads"].label = "Thêm tệp đính kèm"
        self.fields["tep_dinh_kem_uploads"].widget.attrs.update(
            {"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "multiple": True, "id": "id_tep_dinh_kem"}
        )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("file_van_ban"):
            raise forms.ValidationError("Vui lòng tải lên file văn bản.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.trang_thai_vb_den = VanBanDen.TrangThai.CHO_PHAN_CONG
        if commit:
            instance.file_van_ban = self.cleaned_data.get("file_van_ban")
            instance.save()
            attachments = self.cleaned_data.get("tep_dinh_kem_uploads") or []
            for index, uploaded_file in enumerate(attachments):
                TepDinhKemVanBanDen.objects.create(
                    so_vb_den=instance,
                    tep_tin=uploaded_file,
                    thu_tu=index,
                )
        return instance


class VanBanDenUpdateForm(forms.ModelForm):
    ma_loai_vb = LoaiVanBanChoiceField(queryset=LoaiVanBan.objects.none())
    ma_muc_do = MucDoChoiceField(queryset=MucDoUuTien.objects.none())
    file_van_ban_uploads = MultipleFileField(required=False)
    tep_dinh_kem_uploads = MultipleFileField(required=False)
    tep_dinh_kem_xoa_ids = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = VanBanDen
        fields = [
            "trang_thai_vb_den",
            "ngay_nhan",
            "ngay_ky",
            "so_ky_hieu",
            "ma_loai_vb",
            "ma_muc_do",
            "co_quan_ban_hanh",
            "trich_yeu",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ma_loai_vb"].queryset = LoaiVanBan.objects.filter(ap_dung__in=INCOMING_AP_DUNG_VALUES).order_by(
            "ten_loai_vb"
        )
        self.fields["ma_muc_do"].queryset = MucDoUuTien.objects.order_by("muc_do")
        self.fields["ma_loai_vb"].empty_label = "Chọn loại văn bản"
        self.fields["ma_muc_do"].empty_label = "Chọn mức độ ưu tiên"
        self.fields["ngay_nhan"].widget.attrs.update({"placeholder": "Chọn ngày nhận văn bản"})
        self.fields["ngay_ky"].widget.attrs.update({"placeholder": "Chọn ngày ký văn bản"})
        self.fields["so_ky_hieu"].widget.attrs.update({"placeholder": "Nhập số ký hiệu văn bản"})
        self.fields["co_quan_ban_hanh"].widget.attrs.update({"placeholder": "Nhập cơ quan ban hành văn bản"})
        self.fields["trich_yeu"].widget.attrs.update({"placeholder": "Nhập trích yếu văn bản"})
        self.fields["file_van_ban_uploads"].label = "Tải thêm tệp văn bản"
        self.fields["file_van_ban_uploads"].widget.attrs.update(
            {"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "multiple": True, "id": "m-file-upload"}
        )
        self.fields["tep_dinh_kem_uploads"].widget.attrs.update(
            {"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "multiple": True, "id": "m-attachment-upload"}
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            uploads = self.cleaned_data.get("file_van_ban_uploads") or []
            if uploads:
                instance.file_van_ban = uploads[0]
            instance.save()
            deleted_ids = [item.strip() for item in (self.cleaned_data.get("tep_dinh_kem_xoa_ids") or "").split(",") if item.strip()]
            if deleted_ids:
                instance.tep_dinh_kems.filter(ma_tep__in=deleted_ids).delete()
            attachment_uploads = self.cleaned_data.get("tep_dinh_kem_uploads") or []
            start_index = instance.tep_dinh_kems.count()
            for offset, uploaded_file in enumerate(attachment_uploads, start=start_index):
                TepDinhKemVanBanDen.objects.create(
                    so_vb_den=instance,
                    tep_tin=uploaded_file,
                    thu_tu=offset,
                )
        return instance


class VanBanDiUpdateForm(forms.ModelForm):
    ma_loai_vb = LoaiVanBanChoiceField(queryset=LoaiVanBan.objects.none())
    ma_muc_do = MucDoChoiceField(queryset=MucDoUuTien.objects.none())
    nguoi_tao = GiaoVienChoiceField(queryset=GiaoVien.objects.none())
    ban_du_thao_uploads = MultipleFileField(required=False)
    ban_chinh_thuc_uploads = MultipleFileField(required=False)
    tep_dinh_kem_du_thao_uploads = MultipleFileField(required=False)
    tep_dinh_kem_chinh_thuc_uploads = MultipleFileField(required=False)
    tep_dinh_kem_xoa_ids = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = VanBanDi
        fields = [
            "ngay_ban_hanh",
            "ngay_ky",
            "ma_loai_vb",
            "ma_muc_do",
            "nguoi_tao",
            "noi_nhan",
            "trich_yeu",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ma_loai_vb"].queryset = LoaiVanBan.objects.filter(ap_dung__in=OUTGOING_AP_DUNG_VALUES).order_by(
            "ten_loai_vb"
        )
        self.fields["ma_muc_do"].queryset = MucDoUuTien.objects.order_by("muc_do")
        self.fields["nguoi_tao"].queryset = GiaoVien.objects.order_by("ho_ten")
        self.fields["nguoi_tao"].disabled = True
        self.fields["ban_du_thao_uploads"].label = "Tai them file du thao"
        self.fields["ban_chinh_thuc_uploads"].label = "Tai them file chinh thuc"
        self.fields["ban_du_thao_uploads"].widget.attrs.update(
            {"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "multiple": True, "id": "m-ban-du-thao-upload"}
        )
        self.fields["ban_chinh_thuc_uploads"].widget.attrs.update(
            {"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "multiple": True, "id": "m-ban-chinh-thuc-upload"}
        )
        self.fields["tep_dinh_kem_du_thao_uploads"].widget.attrs.update(
            {"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "multiple": True, "id": "m-draft-attachment-upload"}
        )
        self.fields["tep_dinh_kem_chinh_thuc_uploads"].widget.attrs.update(
            {"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "multiple": True, "id": "m-official-attachment-upload"}
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            deleted_ids = [item.strip() for item in (self.cleaned_data.get("tep_dinh_kem_xoa_ids") or "").split(",") if item.strip()]
            if deleted_ids:
                instance.tep_dinh_kem_dis.filter(ma_tep__in=deleted_ids).delete()
            self._append_attachments(instance, "ban_du_thao_uploads", TepDinhKemVanBanDi.LoaiTep.DU_THAO, "ban_du_thao")
            self._append_attachments(
                instance,
                "ban_chinh_thuc_uploads",
                TepDinhKemVanBanDi.LoaiTep.CHINH_THUC,
                "ban_chinh_thuc",
            )
            self._append_supporting_attachments(instance, "tep_dinh_kem_du_thao_uploads", TepDinhKemVanBanDi.LoaiTep.DU_THAO)
            self._append_supporting_attachments(instance, "tep_dinh_kem_chinh_thuc_uploads", TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
        return instance

    def _append_attachments(self, instance, field_name, loai_tep, legacy_field_name):
        uploads = self.cleaned_data.get(field_name) or []
        if not uploads:
            return
        setattr(instance, legacy_field_name, uploads[0])
        instance.save(update_fields=[legacy_field_name])
        start_index = len(instance.get_file_attachments(loai_tep))
        for offset, uploaded_file in enumerate(uploads[1:], start=start_index):
            TepDinhKemVanBanDi.objects.create(
                so_vb_di=instance,
                loai_tep=loai_tep,
                tep_tin=uploaded_file,
                thu_tu=offset,
            )

    def _append_supporting_attachments(self, instance, field_name, loai_tep):
        uploads = self.cleaned_data.get(field_name) or []
        if not uploads:
            return
        start_index = len(instance.get_file_attachments(loai_tep))
        for offset, uploaded_file in enumerate(uploads, start=start_index):
            TepDinhKemVanBanDi.objects.create(
                so_vb_di=instance,
                loai_tep=loai_tep,
                tep_tin=uploaded_file,
                thu_tu=offset,
            )


class VanBanDiDangKyForm(forms.ModelForm):
    ma_loai_vb = LoaiVanBanChoiceField(queryset=LoaiVanBan.objects.none())
    ma_muc_do = MucDoChoiceField(queryset=MucDoUuTien.objects.none())
    nguoi_tao = GiaoVienChoiceField(queryset=GiaoVien.objects.none())
    nguoi_ky = GiaoVienChoiceField(queryset=GiaoVien.objects.none())
    ban_chinh_thuc = forms.FileField(required=False)
    tep_dinh_kem_uploads = MultipleFileField(required=False)

    class Meta:
        model = VanBanDi
        fields = [
            "ngay_ky",
            "so_ky_hieu",
            "ma_loai_vb",
            "ma_muc_do",
            "nguoi_tao",
            "nguoi_ky",
            "noi_nhan",
            "trich_yeu",
        ]
        widgets = {
            "ngay_ky": forms.DateInput(
                attrs={"type": "date", "class": "form-control", "placeholder": "Chon ngay ky van ban"}
            ),
            "so_ky_hieu": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "So ky hieu duoc cap tu dong khi luu dang ky",
                    "readonly": "readonly",
                }
            ),
            "ma_loai_vb": forms.Select(attrs={"class": "form-control"}),
            "ma_muc_do": forms.Select(attrs={"class": "form-control"}),
            "nguoi_tao": forms.Select(attrs={"class": "form-control"}),
            "nguoi_ky": forms.Select(attrs={"class": "form-control"}),
            "noi_nhan": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nhap noi nhan"}),
            "trich_yeu": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": "Nhap trich yeu van ban"}
            ),
        }

    def __init__(self, *args, **kwargs):
        editable = kwargs.pop("editable", True)
        create_mode = kwargs.pop("create_mode", False)
        kwargs.pop("giao_vien", None)
        super().__init__(*args, **kwargs)
        self.create_mode = create_mode
        self.fields["ma_loai_vb"].queryset = LoaiVanBan.objects.filter(ap_dung__in=OUTGOING_AP_DUNG_VALUES).order_by(
            "ten_loai_vb"
        )
        self.fields["ma_muc_do"].queryset = MucDoUuTien.objects.order_by("muc_do")
        self.fields["nguoi_tao"].queryset = GiaoVien.objects.order_by("ho_ten")
        self.fields["nguoi_ky"].queryset = GiaoVien.objects.order_by("ho_ten")
        self.fields["ma_loai_vb"].empty_label = "Chon loai van ban"
        self.fields["ma_muc_do"].empty_label = "Chon muc do uu tien"
        self.fields["nguoi_tao"].empty_label = "Chon nguoi soan thao"
        self.fields["nguoi_ky"].empty_label = "Chon nguoi ky"
        self.fields["ma_loai_vb"].widget.attrs.update({"class": "form-control"})
        self.fields["ma_muc_do"].widget.attrs.update({"class": "form-control"})
        self.fields["nguoi_tao"].widget.attrs.update({"class": "form-control"})
        self.fields["nguoi_ky"].widget.attrs.update({"class": "form-control"})
        self.fields["ngay_ky"].required = False
        self.fields["so_ky_hieu"].required = False
        self.fields["ban_chinh_thuc"].required = False
        self.fields["ban_chinh_thuc"].label = "File chinh thuc"
        self.fields["ban_chinh_thuc"].widget = forms.FileInput(
            attrs={"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "id": "id_ban_chinh_thuc"}
        )
        self.fields["tep_dinh_kem_uploads"].required = False
        self.fields["tep_dinh_kem_uploads"].label = "Them tep dinh kem"
        self.fields["tep_dinh_kem_uploads"].widget.attrs.update(
            {"class": "sr-only", "accept": ".pdf,.doc,.docx,image/*", "multiple": True, "id": "id_tep_dinh_kem"}
        )
        self.fields["ma_muc_do"].required = False
        self.fields["noi_nhan"].required = False
        self.fields["trich_yeu"].required = False
        self.fields["so_ky_hieu"].disabled = True

        if not create_mode:
            self.fields["ma_loai_vb"].disabled = True
            self.fields["nguoi_tao"].disabled = True
            self.fields["nguoi_ky"].disabled = True
            self.fields["ma_loai_vb"].required = False
            self.fields["nguoi_tao"].required = False
            self.fields["nguoi_ky"].required = False

        if not editable:
            for field in self.fields.values():
                field.disabled = True

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            return cleaned_data

        if not cleaned_data.get("ban_chinh_thuc") and not self.instance.ban_chinh_thuc:
            raise forms.ValidationError("Vui long tai len file chinh thuc.")

        fallback_fields = ["ngay_ky", "ma_muc_do", "noi_nhan", "trich_yeu", "so_ky_hieu"]
        for field_name in fallback_fields:
            value = cleaned_data.get(field_name)
            if value in (None, ""):
                cleaned_data[field_name] = getattr(self.instance, field_name)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            self.save_uploaded_files(instance)
        return instance

    def save_uploaded_files(self, instance):
        primary_file = self.cleaned_data.get("ban_chinh_thuc")
        attachments = self.cleaned_data.get("tep_dinh_kem_uploads") or []
        if not primary_file and not attachments:
            return
        if primary_file:
            instance.ban_chinh_thuc = primary_file
            instance.save(update_fields=["ban_chinh_thuc"])
        start_index = len(instance.get_official_attachments())
        for offset, uploaded_file in enumerate(attachments, start=start_index):
            TepDinhKemVanBanDi.objects.create(
                so_vb_di=instance,
                loai_tep=TepDinhKemVanBanDi.LoaiTep.CHINH_THUC,
                tep_tin=uploaded_file,
                thu_tu=offset,
            )


class TaoVanBanDiForm(forms.ModelForm):
    ma_loai_vb = LoaiVanBanChoiceField(queryset=LoaiVanBan.objects.none())
    ma_muc_do = MucDoChoiceField(queryset=MucDoUuTien.objects.none())
    ban_du_thao_uploads = MultipleFileField(required=False)

    class Meta:
        model = VanBanDi
        fields = ["ma_loai_vb", "ma_muc_do", "noi_nhan", "trich_yeu"]
        widgets = {
            "ma_loai_vb": forms.Select(attrs={"class": "form-control"}),
            "ma_muc_do": forms.Select(attrs={"class": "form-control"}),
            "noi_nhan": forms.TextInput(attrs={"class": "form-control"}),
            "trich_yeu": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.giao_vien = kwargs.pop("giao_vien", None)
        super().__init__(*args, **kwargs)
        self.fields["ma_loai_vb"].queryset = LoaiVanBan.objects.filter(ap_dung__in=OUTGOING_AP_DUNG_VALUES).order_by(
            "ten_loai_vb"
        )
        self.fields["ma_muc_do"].queryset = MucDoUuTien.objects.order_by("muc_do")
        self.fields["ma_loai_vb"].empty_label = "Chon loai van ban"
        self.fields["ma_muc_do"].empty_label = "Chon muc do uu tien"
        self.fields["ma_loai_vb"].widget.attrs.update({"class": "form-control", "id": "loai-van-ban"})
        self.fields["ma_muc_do"].widget.attrs.update({"class": "form-control", "id": "muc-do-uu-tien"})
        self.fields["noi_nhan"].widget.attrs.update({"class": "form-control", "id": "noi-nhan"})
        self.fields["trich_yeu"].widget.attrs.update({"class": "form-control", "id": "trich-yeu", "rows": 4})
        self.fields["ban_du_thao_uploads"].widget.attrs.update(
            {"class": "sr-only", "id": "id_ban_du_thao", "accept": ".pdf,.doc,.docx,image/*", "multiple": True}
        )
        self.fields["ban_du_thao_uploads"].label = "Tai file du thao"

    def clean(self):
        cleaned_data = super().clean()
        if self.giao_vien is None:
            raise forms.ValidationError("Tai khoan hien tai chua duoc lien ket voi giao vien.")
        if not (cleaned_data.get("ban_du_thao_uploads") or []):
            raise forms.ValidationError("Vui long tai len it nhat mot file du thao.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.nguoi_tao = self.giao_vien
        instance.nguoi_ky = self.giao_vien
        instance.trang_thai_vb_di = VanBanDi.TrangThai.CHO_DUYET
        instance.so_ky_hieu = ""
        if commit:
            instance.save()
            self.save_uploaded_files(instance)
        return instance

    def save_uploaded_files(self, instance):
        uploads = self.cleaned_data.get("ban_du_thao_uploads") or []
        if not uploads:
            return
        instance.ban_du_thao = uploads[0]
        instance.save(update_fields=["ban_du_thao"])
        start_index = len(instance.get_draft_attachments())
        for index, uploaded_file in enumerate(uploads[1:], start=start_index):
            TepDinhKemVanBanDi.objects.create(
                so_vb_di=instance,
                loai_tep=TepDinhKemVanBanDi.LoaiTep.DU_THAO,
                tep_tin=uploaded_file,
                thu_tu=index,
            )


class ThemMauVanBanForm(forms.ModelForm):
    ma_loai_vb = LoaiVanBanChoiceField(queryset=LoaiVanBan.objects.none())

    class Meta:
        model = MauVanBan
        fields = ["ngay_tao", "ten_mau", "ma_loai_vb", "trang_thai", "muc_dich", "file_mau"]
        widgets = {
            "ngay_tao": forms.DateInput(attrs={"type": "date", "class": "form-control", "id": "ngay-tao"}),
            "ten_mau": forms.TextInput(attrs={"class": "form-control", "id": "ten-mau"}),
            "ma_loai_vb": forms.Select(attrs={"class": "form-control", "id": "loai-van-ban-mau"}),
            "trang_thai": forms.Select(attrs={"class": "form-control", "id": "trang-thai-mau"}),
            "muc_dich": forms.Textarea(attrs={"class": "form-control", "id": "muc-dich", "rows": 4}),
            "file_mau": forms.FileInput(
                attrs={"class": "sr-only", "id": "id_file_mau", "accept": ".pdf,.doc,.docx,image/*"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ma_loai_vb"].queryset = LoaiVanBan.objects.filter(ap_dung__in=OUTGOING_AP_DUNG_VALUES).order_by(
            "ten_loai_vb"
        )
        self.fields["ma_loai_vb"].empty_label = "Chon loai van ban"
        self.fields["ma_loai_vb"].widget.attrs.update({"class": "form-control", "id": "loai-van-ban-mau"})


class CapNhatMauVanBanForm(forms.ModelForm):
    ma_loai_vb = LoaiVanBanChoiceField(queryset=LoaiVanBan.objects.none())

    class Meta:
        model = MauVanBan
        fields = ["ngay_tao", "ten_mau", "ma_loai_vb", "trang_thai", "muc_dich", "file_mau"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ma_loai_vb"].queryset = LoaiVanBan.objects.filter(ap_dung__in=OUTGOING_AP_DUNG_VALUES).order_by(
            "ten_loai_vb"
        )
        self.fields["file_mau"].required = False


class GiaoVienTaiKhoanForm(forms.ModelForm):
    ma_to = forms.ModelChoiceField(queryset=ToChuyenMon.objects.none(), required=False)

    class Meta:
        model = GiaoVien
        fields = ["ho_ten", "chuc_vu", "ma_to", "trang_thai_tk"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ma_to"].queryset = ToChuyenMon.objects.order_by("ten_to")
        self.fields["trang_thai_tk"].widget = forms.Select(
            choices=[
                (GiaoVien.TrangThaiTaiKhoan.HOAT_DONG, "Hoat dong"),
                (GiaoVien.TrangThaiTaiKhoan.NGUNG_HOAT_DONG, "Ngung hoat dong"),
            ]
        )

    def clean_trang_thai_tk(self):
        trang_thai = self.cleaned_data["trang_thai_tk"]
        allowed_statuses = {
            GiaoVien.TrangThaiTaiKhoan.HOAT_DONG,
            GiaoVien.TrangThaiTaiKhoan.NGUNG_HOAT_DONG,
        }
        if trang_thai not in allowed_statuses:
            raise forms.ValidationError("Trang thai tai khoan khong hop le.")
        return trang_thai


class ThemGiaoVienForm(GiaoVienTaiKhoanForm):
    ma_gv = forms.CharField(max_length=10)

    class Meta(GiaoVienTaiKhoanForm.Meta):
        fields = ["ma_gv", "ho_ten", "chuc_vu", "ma_to", "trang_thai_tk"]

    def clean_ma_gv(self):
        ma_gv = (self.cleaned_data["ma_gv"] or "").strip()
        if not ma_gv:
            raise forms.ValidationError("Vui long nhap ma giao vien.")
        if GiaoVien.objects.filter(ma_gv=ma_gv).exists():
            raise forms.ValidationError("Ma giao vien da ton tai.")
        return ma_gv


class PhanQuyenNguoiDungForm(forms.Form):
    nhom_quyen = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["nhom_quyen"].queryset = Group.objects.order_by("name")


class HoSoCaNhanForm(forms.ModelForm):
    class Meta:
        model = GiaoVien
        fields = ["ho_ten"]


class DoiMatKhauCaNhanForm(forms.Form):
    mat_khau_cu = forms.CharField()
    mat_khau_moi = forms.CharField(min_length=8)
    nhap_lai_mat_khau_moi = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean_mat_khau_cu(self):
        mat_khau_cu = self.cleaned_data["mat_khau_cu"]
        if not self.user.check_password(mat_khau_cu):
            raise forms.ValidationError("Mat khau cu khong dung.")
        return mat_khau_cu

    def clean(self):
        cleaned_data = super().clean()
        mat_khau_moi = cleaned_data.get("mat_khau_moi")
        nhap_lai_mat_khau_moi = cleaned_data.get("nhap_lai_mat_khau_moi")

        if mat_khau_moi and nhap_lai_mat_khau_moi and mat_khau_moi != nhap_lai_mat_khau_moi:
            raise forms.ValidationError("Mat khau moi va nhap lai mat khau moi khong khop.")

        return cleaned_data
