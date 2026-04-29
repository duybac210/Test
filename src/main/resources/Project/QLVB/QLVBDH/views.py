import json
from urllib.parse import urlencode
import unicodedata
from types import SimpleNamespace

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    CapNhatMauVanBanForm,
    DoiMatKhauCaNhanForm,
    GiaoVienTaiKhoanForm,
    HoSoCaNhanForm,
    PhanQuyenNguoiDungForm,
    TaoVanBanDiForm,
    ThemGiaoVienForm,
    ThemMauVanBanForm,
    VanBanDenForm,
    VanBanDenUpdateForm,
    VanBanDiDangKyForm,
    VanBanDiUpdateForm,
)
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
    generate_registration_number,
    generate_so_ky_hieu,
)

ASSIGNMENT_PLACEHOLDER_NOTE = "Cho phan cong van ban"


# Nhom ham tien ich chung de sinh ma, chuan hoa du lieu va sap xep muc uu tien.
def predict_next_prefixed_code(model_class, field_name, prefix, width):
    last_object = model_class.objects.order_by(f"-{field_name}").first()
    last_value = getattr(last_object, field_name, "") if last_object else ""

    try:
        last_number = int(last_value.replace(prefix, ""))
    except ValueError:
        last_number = 0

    return f"{prefix}{last_number + 1:0{width}d}"


def normalize_text(value):
    normalized = unicodedata.normalize("NFD", value or "")
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    compact = " ".join(without_marks.strip().lower().split())
    return compact.replace(" /", "/").replace("/ ", "/")


def get_priority_rank(priority_label):
    normalized = normalize_text(priority_label)
    if normalized == "hoa toc":
        return 0
    if normalized == "thuong khan":
        return 1
    if normalized == "khan":
        return 2
    return 3


def annotate_priority_order(queryset, field_name="ma_muc_do__muc_do"):
    return queryset.annotate(
        priority_rank=models.Case(
            models.When(**{f"{field_name}__iexact": "Hoa toc"}, then=models.Value(0)),
            models.When(**{f"{field_name}__iexact": "Thuong khan"}, then=models.Value(1)),
            models.When(**{f"{field_name}__iexact": "Khan"}, then=models.Value(2)),
            default=models.Value(3),
            output_field=models.IntegerField(),
        )
    )


def get_van_ban_den_status_class(trang_thai):
    normalized = normalize_text(trang_thai)
    if "hoan thanh" in normalized or "ban hanh" in normalized:
        return "status-done"
    if "phan cong" in normalized or "xu ly" in normalized:
        return "status-processing"
    return "status-pending"


def get_van_ban_di_status_class(trang_thai):
    normalized = normalize_text(trang_thai)
    if "hoan thanh" in normalized or "ban hanh" in normalized:
        return "status-done"
    if "duyet" in normalized or "dang ky" in normalized or "phan cong" in normalized or "luan chuyen" in normalized:
        return "status-processing"
    return "status-pending"


def get_real_assignments_queryset(document):
    return document.phan_congs.exclude(noi_dung_cd=ASSIGNMENT_PLACEHOLDER_NOTE)


def is_outgoing_post_registration_status(trang_thai):
    normalized = normalize_text(trang_thai)
    allowed_statuses = {
        normalize_text(VanBanDi.TrangThai.DA_DANG_KY),
        normalize_text(VanBanDi.TrangThai.CHO_LUAN_CHUYEN),
        normalize_text(VanBanDi.TrangThai.CHO_PHAN_CONG),
    }
    return normalized in allowed_statuses


def get_choice_label(choice_class, value):
    for choice in choice_class:
        if choice.value == value:
            return choice.label
    return (value or "").strip()


def build_choice_options(choice_class, values):
    return [{"value": value, "label": get_choice_label(choice_class, value)} for value in values]


def get_van_ban_den_status_label(trang_thai):
    return get_choice_label(VanBanDen.TrangThai, trang_thai)


def get_van_ban_di_status_label(trang_thai):
    return get_choice_label(VanBanDi.TrangThai, trang_thai)


def get_progress_status_info(trang_thai):
    normalized = normalize_text(trang_thai)
    if normalized == normalize_text(PhanCongXuLy.TrangThaiXuLy.DA_HOAN_THANH):
        return {
            "label": "Đã hoàn thành",
            "css_class": "status-complete",
            "rank": 3,
        }
    if normalized == normalize_text(PhanCongXuLy.TrangThaiXuLy.DANG_XU_LY):
        return {
            "label": "Đang xử lý",
            "css_class": "status-processing",
            "rank": 2,
        }
    if normalized in {
        normalize_text(PhanCongXuLy.TrangThaiXuLy.CHO_XU_LY),
        "chua xu ly",
    }:
        return {
            "label": "Chờ xử lý",
            "css_class": "status-received",
            "rank": 1,
        }
    return {
        "label": (trang_thai or "Chờ xử lý").strip() or "Chờ xử lý",
        "css_class": "status-received",
        "rank": 1,
    }


# Nhom ham dong bo va tong hop tien do xu ly tu cac ban ghi phan cong.
def sync_document_processing_status_from_assignments(document, *, is_incoming):
    assignments = list(get_real_assignments_queryset(document))
    if is_incoming:
        if not assignments:
            target_status = VanBanDen.TrangThai.CHO_PHAN_CONG
        elif all(
            normalize_text(item.trang_thai_xl) == normalize_text(PhanCongXuLy.TrangThaiXuLy.DA_HOAN_THANH)
            for item in assignments
        ):
            target_status = VanBanDen.TrangThai.DA_HOAN_THANH
        else:
            target_status = VanBanDen.TrangThai.CHO_XU_LY
    else:
        if not assignments:
            target_status = VanBanDi.TrangThai.DA_DANG_KY
        elif all(
            normalize_text(item.trang_thai_xl) == normalize_text(PhanCongXuLy.TrangThaiXuLy.DA_HOAN_THANH)
            for item in assignments
        ):
            target_status = VanBanDi.TrangThai.DA_HOAN_THANH
        else:
            target_status = VanBanDi.TrangThai.DA_DANG_KY

    field_name = "trang_thai_vb_den" if is_incoming else "trang_thai_vb_di"
    if getattr(document, field_name) != target_status:
        setattr(document, field_name, target_status)
        document.save(update_fields=[field_name])


def build_progress_assignment_details(assignments):
    details = []
    for assignment in assignments:
        status_info = get_progress_status_info(assignment.trang_thai_xl)
        details.append(
            {
                "nguoi_xu_ly": assignment.nguoi_xu_ly.ho_ten,
                "trang_thai": status_info["label"],
                "status_class": status_info["css_class"],
                "noi_dung_cd": assignment.noi_dung_cd,
                "thoi_han": assignment.thoi_han.strftime("%d/%m/%Y") if assignment.thoi_han else "",
                "thoi_gian_phan_cong": (
                    timezone.localtime(assignment.thoi_gian_phan_cong).strftime("%d/%m/%Y %H:%M")
                    if assignment.thoi_gian_phan_cong
                    else ""
                ),
            }
        )
    return details


def build_progress_tracking_documents(giao_vien):
    if giao_vien is None:
        return []

    assignments = (
        PhanCongXuLy.objects.filter(nguoi_phan_cong=giao_vien).exclude(noi_dung_cd=ASSIGNMENT_PLACEHOLDER_NOTE)
        .select_related(
            "nguoi_xu_ly",
            "so_vb_den__ma_loai_vb",
            "so_vb_di__ma_loai_vb",
            "so_vb_di__nguoi_tao",
        )
        .order_by("-thoi_gian_phan_cong", "ma_xu_ly")
    )

    grouped_documents = {}
    for assignment in assignments:
        document_den = assignment.so_vb_den
        document_di = assignment.so_vb_di
        is_incoming = document_den is not None
        document = document_den or document_di
        if document is None:
            continue

        document_key = f"{'den' if is_incoming else 'di'}:{document.pk}"
        if document_key not in grouped_documents:
            ngay_ban_hanh = document.ngay_ky if is_incoming else (document.ngay_ban_hanh or document.ngay_ky)
            grouped_documents[document_key] = {
                "record_id": document.pk,
                "loai": "den" if is_incoming else "di",
                "ngay_ban_hanh": ngay_ban_hanh,
                "so_van_ban": document.so_vb_den if is_incoming else document.so_vb_di,
                "loai_van_ban": document.ma_loai_vb.ten_loai_vb,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "co_quan_ban_hanh": (
                    document.co_quan_ban_hanh
                    if is_incoming
                    else getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND")
                ),
                "nguoi_xu_ly_hien_thi": [],
                "status_ranks": [],
                "details": [],
            }

        row = grouped_documents[document_key]
        status_info = get_progress_status_info(assignment.trang_thai_xl)
        row["nguoi_xu_ly_hien_thi"].append(assignment.nguoi_xu_ly.ho_ten)
        row["status_ranks"].append(status_info["rank"])
        row["details"].append(build_progress_assignment_details([assignment])[0])

    documents = []
    for row in grouped_documents.values():
        if row["status_ranks"] and all(rank == 3 for rank in row["status_ranks"]):
            aggregate_status = get_progress_status_info("Da hoan thanh")
        elif any(rank in {2, 3} for rank in row["status_ranks"]):
            aggregate_status = get_progress_status_info("Dang xu ly")
        else:
            aggregate_status = get_progress_status_info("Da tiep nhan")

        row["nguoi_xu_ly_hien_thi"] = ", ".join(row["nguoi_xu_ly_hien_thi"])
        row["trang_thai_hien_thi"] = aggregate_status["label"]
        row["trang_thai_css_class"] = aggregate_status["css_class"]
        row["ngay_ban_hanh_display"] = row["ngay_ban_hanh"].strftime("%d/%m/%Y") if row["ngay_ban_hanh"] else ""
        row["details_json"] = json.dumps(row["details"], ensure_ascii=True)
        documents.append(row)

    documents.sort(key=lambda item: item["ngay_ban_hanh"] or timezone.datetime.min.date(), reverse=True)
    for index, document in enumerate(documents, start=1):
        document["stt"] = index
    return documents


# Nhom ham xac dinh vai tro, nhom quyen va quyen truy cap theo giao vien.
def get_hieu_truong():
    giao_vien_list = GiaoVien.objects.prefetch_related("user__groups").order_by("ho_ten")
    for giao_vien in giao_vien_list:
        if giao_vien_has_role(giao_vien, "Hieu truong"):
            return giao_vien
    for giao_vien in giao_vien_list:
        if giao_vien_in_group(giao_vien, "Ban giam hieu"):
            return giao_vien
    return None


def giao_vien_has_role(giao_vien, role_name):
    if giao_vien is None:
        return False
    return normalize_text(giao_vien.chuc_vu) == normalize_text(role_name)


def giao_vien_in_group(giao_vien, group_name):
    if giao_vien is None or not giao_vien.user_id:
        return False
    target = normalize_text(group_name)
    return any(target == normalize_text(name) for name in giao_vien.user.groups.values_list("name", flat=True))


def is_hieu_truong(giao_vien):
    return giao_vien_has_role(giao_vien, "Hieu truong")


def is_pho_hieu_truong(giao_vien):
    return giao_vien_has_role(giao_vien, "Pho hieu truong")


def is_truong_bo_mon(giao_vien):
    return (
        giao_vien_in_group(giao_vien, "To chuyen mon")
        or giao_vien_in_group(giao_vien, "To truong")
        or giao_vien_in_group(giao_vien, "To truong chuyen mon")
        or giao_vien_has_role(giao_vien, "To truong")
    )


def is_van_thu(giao_vien):
    return giao_vien_in_group(giao_vien, "Van thu") or giao_vien_has_role(giao_vien, "Van thu")


def is_phong_ban_to_chuc(giao_vien):
    return (
        giao_vien_in_group(giao_vien, "Phong/ ban/ to chuc")
        or giao_vien_in_group(giao_vien, "Phong/ban / to chuc")
        or giao_vien_in_group(giao_vien, "Nguoi dung to chuc trong truong")
    )


def is_ban_giam_hieu(giao_vien):
    return (
        giao_vien_in_group(giao_vien, "Ban giam hieu")
        or giao_vien_has_role(giao_vien, "Hieu truong")
        or giao_vien_has_role(giao_vien, "Pho hieu truong")
    )


def is_nguoi_dung_ban_giam_hieu(giao_vien):
    return is_ban_giam_hieu(giao_vien)


def is_regular_teacher(giao_vien):
    if giao_vien is None:
        return False
    return not any(
        (
            is_ban_giam_hieu(giao_vien),
            is_van_thu(giao_vien),
            is_truong_bo_mon(giao_vien),
        )
    )


def can_view_follow_condition(giao_vien):
    return giao_vien is None or is_van_thu(giao_vien)


def can_view_incoming_outgoing(giao_vien):
    return giao_vien is None or is_van_thu(giao_vien) or is_ban_giam_hieu(giao_vien)


def can_create_document(giao_vien):
    return giao_vien is not None and (
        is_van_thu(giao_vien)
        or is_truong_bo_mon(giao_vien)
        or is_phong_ban_to_chuc(giao_vien)
        or is_regular_teacher(giao_vien)
    )


def can_manage_work(giao_vien):
    return (
        giao_vien is None
        or is_ban_giam_hieu(giao_vien)
        or is_truong_bo_mon(giao_vien)
        or is_phong_ban_to_chuc(giao_vien)
    )


def can_personal_work(giao_vien):
    return giao_vien is not None and (
        is_van_thu(giao_vien)
        or is_truong_bo_mon(giao_vien)
        or is_phong_ban_to_chuc(giao_vien)
        or is_regular_teacher(giao_vien)
    )


def can_view_document_list(giao_vien):
    return (
        giao_vien is None
        or is_van_thu(giao_vien)
        or is_ban_giam_hieu(giao_vien)
        or is_truong_bo_mon(giao_vien)
        or is_phong_ban_to_chuc(giao_vien)
        or is_regular_teacher(giao_vien)
    )


def can_view_created_document_list(giao_vien):
    return giao_vien is not None and can_view_document_list(giao_vien)


def can_manage_templates(giao_vien):
    return giao_vien is None or is_van_thu(giao_vien)


def can_manage_accounts(giao_vien):
    return giao_vien is not None and is_van_thu(giao_vien)


# Nhom ham lay danh sach nguoi dung va chuan hoa du lieu de hien thi tren giao dien.
def get_pho_hieu_truong_list():
    giao_vien_list = GiaoVien.objects.prefetch_related("user__groups").order_by("ho_ten")
    return [giao_vien for giao_vien in giao_vien_list if giao_vien_has_role(giao_vien, "Pho hieu truong")]


def get_truong_bo_mon_for_giao_vien(giao_vien):
    if giao_vien is None or giao_vien.ma_to_id is None:
        return None
    if getattr(giao_vien.ma_to, "to_truong_id", None):
        return giao_vien.ma_to.to_truong
    return (
        GiaoVien.objects.filter(ma_to=giao_vien.ma_to, chuc_vu__iexact="To truong")
        .order_by("ho_ten")
        .distinct()
        .first()
    )


def get_assignable_teachers_for_user(giao_vien):
    queryset = GiaoVien.objects.prefetch_related("user__groups").order_by("ho_ten")
    if is_phong_ban_to_chuc(giao_vien):
        excluded_ids = [item.pk for item in queryset if is_ban_giam_hieu(item)]
        return queryset.exclude(pk__in=excluded_ids)
    if giao_vien is None or not is_truong_bo_mon(giao_vien) or giao_vien.ma_to_id is None:
        return queryset
    return queryset.filter(ma_to=giao_vien.ma_to).exclude(pk=giao_vien.pk)


def serialize_mau_van_ban(template):
    return {
        "ma_mau_vb": template.ma_mau_vb,
        "ngay_tao": template.ngay_tao.strftime("%Y-%m-%d") if template.ngay_tao else "",
        "ngay_tao_display": template.ngay_tao.strftime("%d/%m/%Y") if template.ngay_tao else "",
        "ten_mau": template.ten_mau,
        "ten_loai_vb": template.ma_loai_vb.ten_loai_vb,
        "ma_loai_vb": template.ma_loai_vb_id,
        "trang_thai": template.trang_thai,
        "muc_dich": template.muc_dich,
        "file_name": template.file_mau.name.split("/")[-1] if template.file_mau else "",
        "file_url": template.file_mau.url if template.file_mau else "",
    }


def get_teacher_last_login_display(giao_vien):
    if giao_vien is None or not giao_vien.user_id or not giao_vien.user.last_login:
        return "Chua dang nhap"
    return timezone.localtime(giao_vien.user.last_login).strftime("%d/%m/%Y %H:%M")


def serialize_teacher_account(giao_vien):
    return {
        "ma_gv": giao_vien.ma_gv,
        "ho_ten": giao_vien.ho_ten,
        "chuc_vu": giao_vien.chuc_vu or "",
        "ma_to": giao_vien.ma_to_id or "",
        "to_chuyen_mon": giao_vien.ma_to.ten_to if giao_vien.ma_to_id else "",
        "lan_cuoi_dang_nhap": get_teacher_last_login_display(giao_vien),
        "trang_thai_tk": giao_vien.trang_thai_tk,
        "nhom_quyen": list(giao_vien.user.groups.order_by("name").values_list("name", flat=True)) if giao_vien.user_id else [],
        "nhom_quyen_display": giao_vien.ten_nhom_quyen_hien_thi or "Chua phan quyen",
    }


def serialize_teacher_row_html(request, giao_vien):
    return render(
        request,
        "partials/giao_vien_row.html",
        {
            "teacher": giao_vien,
        },
    ).content.decode("utf-8")


def serialize_recipient(recipient):
    return {
        "ma_noi_nhan": recipient.ma_noi_nhan,
        "ten_noi_nhan": recipient.ten_noi_nhan,
        "dia_chi": recipient.dia_chi,
        "so_dien_thoai": recipient.so_dien_thoai,
        "gmail": recipient.gmail,
        "thong_tin_khac": recipient.thong_tin_khac,
    }


def serialize_recipient_row_html(request, recipient):
    return render(
        request,
        "partials/noi_nhan_row.html",
        {
            "recipient": recipient,
        },
    ).content.decode("utf-8")


def serialize_external_dispatch_record(record):
    document = record.ma_vb_di
    attachments = (
        serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
        or serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
    )
    primary_attachment = (
        build_primary_file_payload(document.ban_chinh_thuc)
        if document.ban_chinh_thuc
        else build_primary_file_payload(document.ban_du_thao)
    )
    return {
        "record_id": record.pk,
        "so_van_ban": document.so_vb_di,
        "ngay_ban_hanh_display": (
            (document.ngay_ban_hanh or document.ngay_ky).strftime("%d/%m/%Y")
            if (document.ngay_ban_hanh or document.ngay_ky)
            else ""
        ),
        "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
        "so_ky_hieu": document.so_ky_hieu,
        "trich_yeu": document.trich_yeu,
        "trang_thai": record.trang_thai_gui,
        "noi_nhan_tong_hop": record.ma_noi_nhan.ten_noi_nhan,
        "nguoi_thuc_hien": record.nguoi_thuc_hien.ho_ten,
        "nguoi_thuc_hien_id": record.nguoi_thuc_hien_id,
        "ghi_chu": record.ghi_chu,
        "ma_noi_nhan": record.ma_noi_nhan_id,
        "thoi_gian_gui": (
            timezone.localtime(record.thoi_gian_gui).strftime("%d/%m/%Y %H:%M")
            if record.thoi_gian_gui
            else ""
        ),
        "file_name": primary_attachment["name"],
        "file_url": primary_attachment["url"],
        "attachments_json": serialize_attachment_json(attachments),
    }


def get_document_signers_display(document):
    signed_records = list(
        document.xu_lys.select_related("ma_gv")
        .filter(trang_thai_ky=XuLy.TRANG_THAI_DA_DUYET)
        .order_by("thoi_gian_ky", "ma_xu_ly")
    )
    if signed_records:
        role_labels = {
            XuLy.VAI_TRO_KY_NHAY: "Ky nhay",
            XuLy.VAI_TRO_KY_CHINH: "Ky chinh",
            XuLy.VAI_TRO_KY_THAY: "Ky thay",
        }
        return ", ".join(
            f"{record.ma_gv.ho_ten} ({role_labels.get(record.vai_tro_ky, record.vai_tro_ky)})"
            for record in signed_records
        )
    return document.nguoi_ky.ho_ten if getattr(document, "nguoi_ky", None) else ""


def build_attachment_payload(name, url, attachment_id="", attachment_type=""):
    return {
        "id": attachment_id,
        "type": attachment_type,
        "name": name.split("/")[-1] if name else "",
        "url": url or "",
    }


def build_primary_file_payload(file_field):
    if not file_field:
        return {"name": "", "url": ""}
    return build_attachment_payload(file_field.name, getattr(file_field, "url", ""))


def serialize_personal_profile(giao_vien):
    if giao_vien is None:
        return {}
    return {
        "ma_gv": giao_vien.ma_gv,
        "ho_ten": giao_vien.ho_ten,
        "lan_cuoi_dang_nhap": get_teacher_last_login_display(giao_vien),
        "nhom_quyen_display": giao_vien.ten_nhom_quyen_hien_thi or "Chua phan quyen",
    }


def serialize_incoming_attachments(document):
    return [
        build_attachment_payload(item.tep_tin.name, item.tep_tin.url if item.tep_tin else "", item.ma_tep, "den")
        for item in document.get_file_attachments()
        if item.tep_tin
    ]


def serialize_outgoing_attachments(document, loai_tep):
    if loai_tep == TepDinhKemVanBanDi.LoaiTep.DU_THAO:
        return [
            build_attachment_payload(item.tep_tin.name, item.tep_tin.url if item.tep_tin else "", item.ma_tep, loai_tep)
            for item in document.get_draft_attachments()
            if item.tep_tin
        ]
    return [
        build_attachment_payload(item.tep_tin.name, item.tep_tin.url if item.tep_tin else "", item.ma_tep, loai_tep)
        for item in document.get_official_attachments()
        if item.tep_tin
    ]


def serialize_outgoing_supporting_attachments(document, loai_tep):
    if loai_tep == TepDinhKemVanBanDi.LoaiTep.DU_THAO:
        return [
            build_attachment_payload(item.tep_tin.name, item.tep_tin.url if item.tep_tin else "")
            for item in document.get_draft_attachments()
            if item.tep_tin
        ]
    return [
        build_attachment_payload(item.tep_tin.name, item.tep_tin.url if item.tep_tin else "")
        for item in document.get_official_attachments()
        if item.tep_tin
    ]


def get_primary_attachment(attachments):
    return attachments[0] if attachments else {"name": "", "url": ""}


def serialize_attachment_json(attachments):
    return json.dumps(attachments, ensure_ascii=True)


def copy_request_files_with_aliases(request, aliases):
    files = request.FILES.copy()
    for target_name, source_name in aliases.items():
        if files.getlist(target_name):
            continue
        source_files = files.getlist(source_name)
        if source_files:
            files.setlist(target_name, source_files)
    return files


def serialize_van_ban_den_list_document(document):
    attachments = serialize_incoming_attachments(document)
    primary_attachment = build_primary_file_payload(document.file_van_ban)
    return {
        "so_vb_den": document.so_vb_den,
        "ngay_nhan": document.ngay_nhan.strftime("%d/%m/%Y"),
        "ngay_ky": document.ngay_ky.strftime("%d/%m/%Y"),
        "so_ky_hieu": document.so_ky_hieu,
        "trich_yeu": document.trich_yeu,
        "co_quan_ban_hanh": document.co_quan_ban_hanh,
        "trang_thai_vb_den": document.trang_thai_vb_den,
        "trang_thai_hien_thi": get_van_ban_den_status_label(document.trang_thai_vb_den),
        "da_ban_hanh_noi_bo": document.da_ban_hanh_noi_bo,
        "status_class": get_van_ban_den_status_class(document.trang_thai_vb_den),
        "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
        "muc_do": document.ma_muc_do.muc_do,
        "file_name": primary_attachment["name"],
        "file_url": primary_attachment["url"],
        "attachments": attachments,
        "attachments_json": serialize_attachment_json(attachments),
    }


def serialize_van_ban_can_duyet(document):
    draft_attachments = serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
    primary_draft_attachment = build_primary_file_payload(document.ban_du_thao)
    assignment_status = "Da phan cong" if get_real_assignments_queryset(document).exists() else "Chua phan cong"
    return {
        "so_vb_di": document.so_vb_di,
        "ngay_ban_hanh": document.ngay_ban_hanh.strftime("%Y-%m-%d") if document.ngay_ban_hanh else "",
        "ngay_ban_hanh_display": document.ngay_ban_hanh.strftime("%d/%m/%Y") if document.ngay_ban_hanh else "",
        "so_ky_hieu": document.so_ky_hieu,
        "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
        "trich_yeu": document.trich_yeu,
        "co_quan_ban_hanh": getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND"),
        "tinh_trang_phan_cong": assignment_status,
        "nguoi_tao": document.nguoi_tao.ho_ten,
        "nguoi_ky": get_document_signers_display(document),
        "noi_nhan": document.noi_nhan,
        "ban_du_thao_name": primary_draft_attachment["name"],
        "ban_du_thao_url": primary_draft_attachment["url"],
        "ban_du_thao_attachments": draft_attachments,
        "ban_du_thao_attachments_json": serialize_attachment_json(draft_attachments),
        "assigned_ids": [assignment.nguoi_xu_ly_id for assignment in get_real_assignments_queryset(document)],
        "assigned_names": [assignment.nguoi_xu_ly.ho_ten for assignment in get_real_assignments_queryset(document)],
        "chi_dao": get_real_assignments_queryset(document).first().noi_dung_cd if get_real_assignments_queryset(document).exists() else "",
    }


def serialize_van_ban_can_phan_cong(item):
    return {
        "loai": item["loai"],
        "badge": "[DEN]" if item["loai"] == "den" else "[DI]",
        "badge_class": "badge-den" if item["loai"] == "den" else "badge-di",
        "so_van_ban": item["so_van_ban"],
        "so_ky_hieu": item["so_ky_hieu"],
        "trich_yeu": item["trich_yeu"],
        "nguoi_gui": item["nguoi_gui"],
        "thoi_gian": item["thoi_gian"],
        "thoi_gian_display": item["thoi_gian"].strftime("%d/%m/%Y") if item["thoi_gian"] else "",
        "trang_thai": item.get("trang_thai", VanBanDen.TrangThai.CHO_PHAN_CONG),
        "file_name": item["file_name"],
        "file_url": item["file_url"],
        "so_van_ban": item["so_van_ban"],
        "record_id": item["record_id"],
        "co_quan_ban_hanh": item["co_quan_ban_hanh"],
        "ten_loai_vb": item["ten_loai_vb"],
        "noi_dung_cd": item.get("noi_dung_cd", ""),
        "thoi_han": item.get("thoi_han", ""),
        "assigned_ids": item.get("assigned_ids", []),
        "assignment_details_json": json.dumps(item.get("assignment_details", []), ensure_ascii=True),
    }


# Nhom ham tong hop danh sach van ban cho cac man hinh phan cong va dang ky.
def build_assignment_documents(*, incoming_status, outgoing_status):
    incoming_documents = (
        annotate_priority_order(VanBanDen.objects.filter(trang_thai_vb_den__iexact=incoming_status))
        .select_related("ma_loai_vb", "ma_muc_do")
        .prefetch_related("phan_congs__nguoi_xu_ly")
        .order_by("priority_rank", "-ngay_nhan", "-so_vb_den")
    )
    outgoing_documents = VanBanDi.objects.none()
    if outgoing_status:
        outgoing_documents = (
            annotate_priority_order(VanBanDi.objects.filter(trang_thai_vb_di__iexact=outgoing_status))
            .select_related("nguoi_tao", "ma_loai_vb", "ma_muc_do")
            .prefetch_related("phan_congs__nguoi_xu_ly")
            .order_by("priority_rank", "-ngay_ky", "-so_vb_di")
        )

    documents = []
    for document in incoming_documents:
        attachments = serialize_incoming_attachments(document)
        primary_attachment = build_primary_file_payload(document.file_van_ban)
        documents.append(
            {
                "loai": "den",
                "record_id": document.so_vb_den,
                "so_van_ban": document.so_vb_den,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "nguoi_gui": document.co_quan_ban_hanh,
                "co_quan_ban_hanh": document.co_quan_ban_hanh,
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "muc_do": document.ma_muc_do.muc_do,
                "priority_rank": get_priority_rank(document.ma_muc_do.muc_do),
                "thoi_gian": document.ngay_nhan,
                "file_name": primary_attachment["name"],
                "file_url": primary_attachment["url"],
                "attachments_json": serialize_attachment_json(attachments),
                "noi_dung_cd": get_real_assignments_queryset(document).first().noi_dung_cd if get_real_assignments_queryset(document).exists() else "",
                "thoi_han": (
                    get_real_assignments_queryset(document).first().thoi_han.strftime("%Y-%m-%d")
                    if get_real_assignments_queryset(document).exists()
                    else ""
                ),
                "assigned_ids": list(get_real_assignments_queryset(document).values_list("nguoi_xu_ly_id", flat=True)),
                "assignment_details": [
                    {
                        "id": assignment.nguoi_xu_ly_id,
                        "name": assignment.nguoi_xu_ly.ho_ten,
                        "instruction": assignment.noi_dung_cd,
                    }
                    for assignment in get_real_assignments_queryset(document)
                ],
                "trang_thai": document.trang_thai_vb_den,
            }
        )

    for document in outgoing_documents:
        attachments = serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
        primary_attachment = build_primary_file_payload(document.ban_chinh_thuc)
        documents.append(
            {
                "loai": "di",
                "record_id": document.so_vb_di,
                "so_van_ban": document.so_vb_di,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "nguoi_gui": document.nguoi_tao.ho_ten,
                "co_quan_ban_hanh": getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND"),
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "muc_do": document.ma_muc_do.muc_do,
                "priority_rank": get_priority_rank(document.ma_muc_do.muc_do),
                "thoi_gian": document.ngay_ky,
                "file_name": primary_attachment["name"],
                "file_url": primary_attachment["url"],
                "attachments_json": serialize_attachment_json(attachments),
                "noi_dung_cd": get_real_assignments_queryset(document).first().noi_dung_cd if get_real_assignments_queryset(document).exists() else "",
                "thoi_han": (
                    get_real_assignments_queryset(document).first().thoi_han.strftime("%Y-%m-%d")
                    if get_real_assignments_queryset(document).exists()
                    else ""
                ),
                "assigned_ids": list(get_real_assignments_queryset(document).values_list("nguoi_xu_ly_id", flat=True)),
                "assignment_details": [
                    {
                        "id": assignment.nguoi_xu_ly_id,
                        "name": assignment.nguoi_xu_ly.ho_ten,
                        "instruction": assignment.noi_dung_cd,
                    }
                    for assignment in get_real_assignments_queryset(document)
                ],
                "trang_thai": document.trang_thai_vb_di,
            }
        )

    documents.sort(
        key=lambda item: (
            item.get("priority_rank", 3),
            -(item["thoi_gian"].toordinal() if item["thoi_gian"] else timezone.datetime.min.date().toordinal()),
        )
    )
    for index, document in enumerate(documents, start=1):
        document["stt"] = index
    return documents


def build_assigned_documents_for_user(giao_vien):
    if giao_vien is None:
        return []

    assignments = (
        PhanCongXuLy.objects.filter(nguoi_phan_cong=giao_vien).exclude(noi_dung_cd=ASSIGNMENT_PLACEHOLDER_NOTE)
        .select_related(
            "so_vb_den__ma_loai_vb",
            "so_vb_di__ma_loai_vb",
            "so_vb_di__nguoi_tao",
        )
        .prefetch_related("so_vb_den__phan_congs__nguoi_xu_ly", "so_vb_di__phan_congs__nguoi_xu_ly")
        .order_by("-thoi_gian_phan_cong", "ma_xu_ly")
    )

    documents = []
    seen_keys = set()
    for assignment in assignments:
        document = assignment.so_vb_den or assignment.so_vb_di
        if document is None:
            continue
        current_status = document.trang_thai_vb_den if assignment.so_vb_den_id else document.trang_thai_vb_di
        if assignment.so_vb_den_id and normalize_text(current_status) == normalize_text(VanBanDen.TrangThai.CHO_PHAN_CONG):
            continue

        loai = "den" if assignment.so_vb_den_id else "di"
        record_id = document.pk
        document_key = (loai, record_id)
        if document_key in seen_keys:
            continue

        phan_congs = get_real_assignments_queryset(document).select_related("nguoi_xu_ly")
        attachments = (
            serialize_incoming_attachments(document)
            if loai == "den"
            else serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
        )
        primary_attachment = (
            build_primary_file_payload(document.file_van_ban)
            if loai == "den"
            else build_primary_file_payload(document.ban_chinh_thuc)
        )
        documents.append(
            {
                "loai": loai,
                "record_id": record_id,
                "so_van_ban": document.so_vb_den if loai == "den" else document.so_vb_di,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "nguoi_gui": document.co_quan_ban_hanh if loai == "den" else document.nguoi_tao.ho_ten,
                "co_quan_ban_hanh": (
                    document.co_quan_ban_hanh
                    if loai == "den"
                    else getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND")
                ),
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "priority_rank": get_priority_rank(document.ma_muc_do.muc_do),
                "thoi_gian": document.ngay_nhan if loai == "den" else document.ngay_ky,
                "file_name": primary_attachment["name"],
                "file_url": primary_attachment["url"],
                "attachments_json": serialize_attachment_json(attachments),
                "noi_dung_cd": assignment.noi_dung_cd,
                "thoi_han": assignment.thoi_han.strftime("%Y-%m-%d") if assignment.thoi_han else "",
                "assigned_ids": list(phan_congs.values_list("nguoi_xu_ly_id", flat=True)),
                "assignment_details": [
                    {"id": phan_cong.nguoi_xu_ly_id, "name": phan_cong.nguoi_xu_ly.ho_ten, "instruction": phan_cong.noi_dung_cd}
                    for phan_cong in phan_congs
                ],
                "trang_thai": current_status,
            }
        )
        seen_keys.add(document_key)

    documents.sort(
        key=lambda item: (
            item.get("priority_rank", 3),
            -(item["thoi_gian"].toordinal() if item["thoi_gian"] else timezone.datetime.min.date().toordinal()),
        )
    )
    for index, document in enumerate(documents, start=1):
        document["stt"] = index
    return documents


def build_manual_outgoing_registration_document(*, so_vb_di, trang_thai):
    empty_teacher = SimpleNamespace(ho_ten="")
    empty_type = SimpleNamespace(ten_loai_vb="")
    return SimpleNamespace(
        so_vb_di=so_vb_di,
        trang_thai_vb_di=trang_thai,
        ngay_ban_hanh=None,
        ngay_ky=None,
        ma_loai_vb=empty_type,
        nguoi_tao=empty_teacher,
        nguoi_ky=empty_teacher,
        ban_du_thao=None,
        ban_chinh_thuc=None,
        draft_attachments=[],
        official_attachments=[],
    )


def deny_if_no_permission(request, *, allowed, message="Ban khong co quyen truy cap chuc nang nay.", redirect_name="home"):
    if allowed:
        return None
    messages.error(request, message)
    return redirect(redirect_name)


def get_default_home_name_for_user(user):
    if not user.is_authenticated:
        return "login"

    giao_vien = getattr(user, "ho_so_giao_vien", None)
    if can_view_follow_condition(giao_vien):
        return "theo_doi_tinh_trang"
    if can_view_incoming_outgoing(giao_vien):
        return "danh_sach_van_ban_den"
    if can_manage_work(giao_vien):
        return "duyet_van_ban"
    if can_personal_work(giao_vien):
        return "van_ban_xu_ly_ca_nhan"
    if can_view_document_list(giao_vien):
        return "van_ban_da_ban_hanh"
    return "login"


def get_initial_approver_for_outgoing_document(giao_vien, loai_van_ban):
    if giao_vien is None:
        return None, None
    hieu_truong = get_hieu_truong()
    if loai_van_ban.twocap == LoaiVanBan.TWO_CAP_HAI_CAP:
        truong_bo_mon = get_truong_bo_mon_for_giao_vien(giao_vien)
        if truong_bo_mon is None:
            return hieu_truong or giao_vien, XuLy.VAI_TRO_KY_CHINH
        return truong_bo_mon, XuLy.VAI_TRO_KY_NHAY
    return hieu_truong or giao_vien, XuLy.VAI_TRO_KY_CHINH


# Nhom ham thong ke du lieu de hien thi dashboard theo doi tinh trang.
def build_status_count_items(queryset, field_name, statuses):
    counts = {}
    for row in queryset.values(field_name).order_by().annotate(total=models.Count("pk")):
        counts[row[field_name]] = row["total"]
    status_labels = {
        VanBanDen.TrangThai.CHO_PHAN_CONG: "Chờ phân công",
        VanBanDen.TrangThai.CHO_XU_LY: "Chờ xử lý",
        VanBanDen.TrangThai.DA_HOAN_THANH: "Đã hoàn thành",
        VanBanDen.TrangThai.DA_BAN_HANH: "Đã ban hành",
        VanBanDi.TrangThai.DU_THAO: "Dự thảo",
        VanBanDi.TrangThai.CHO_DUYET: "Chờ duyệt",
        VanBanDi.TrangThai.DANG_CHINH_SUA: "Đang chỉnh sửa",
        VanBanDi.TrangThai.CHO_DANG_KY: "Chờ đăng ký",
        VanBanDi.TrangThai.CHO_LUAN_CHUYEN: "Chờ luân chuyển",
        VanBanDi.TrangThai.CHO_PHAN_CONG: "Chờ phân công",
        VanBanDi.TrangThai.DA_BAN_HANH: "Đã ban hành",
    }
    return [(f"{status_labels.get(status, status)}:", counts.get(status, 0)) for status in statuses]


def build_document_type_count_items():
    type_counts = {}

    for row in (
        VanBanDen.objects.values("ma_loai_vb__ten_loai_vb")
        .order_by()
        .annotate(total=models.Count("pk"))
    ):
        type_name = row["ma_loai_vb__ten_loai_vb"]
        type_counts[type_name] = type_counts.get(type_name, 0) + row["total"]

    for row in (
        VanBanDi.objects.values("ma_loai_vb__ten_loai_vb")
        .order_by()
        .annotate(total=models.Count("pk"))
    ):
        type_name = row["ma_loai_vb__ten_loai_vb"]
        type_counts[type_name] = type_counts.get(type_name, 0) + row["total"]

    if not type_counts:
        return [("Chua co van ban:", 0)]

    sorted_items = sorted(type_counts.items(), key=lambda item: (-item[1], item[0]))
    return [(f"{name}:", total) for name, total in sorted_items[:6]]


def build_priority_processing_count_items():
    priority_labels = ["Hỏa tốc", "Thượng khẩn", "Khẩn", "Bình thường"]
    counts = {label: 0 for label in priority_labels}
    incoming_processing_statuses = [
        VanBanDen.TrangThai.CHO_PHAN_CONG,
        VanBanDen.TrangThai.CHO_XU_LY,
    ]
    outgoing_processing_statuses = [
        VanBanDi.TrangThai.CHO_DUYET,
        VanBanDi.TrangThai.DANG_CHINH_SUA,
        VanBanDi.TrangThai.CHO_DANG_KY,
        VanBanDi.TrangThai.CHO_LUAN_CHUYEN,
        VanBanDi.TrangThai.CHO_PHAN_CONG,
    ]

    for muc_do in VanBanDen.objects.filter(trang_thai_vb_den__in=incoming_processing_statuses).values_list("ma_muc_do__muc_do", flat=True):
        normalized = normalize_text(muc_do)
        for label in priority_labels:
            if normalize_text(label) == normalized:
                counts[label] += 1
                break

    for muc_do in VanBanDi.objects.filter(trang_thai_vb_di__in=outgoing_processing_statuses).values_list("ma_muc_do__muc_do", flat=True):
        normalized = normalize_text(muc_do)
        for label in priority_labels:
            if normalize_text(label) == normalized:
                counts[label] += 1
                break

    return [(f"{label}:", counts[label]) for label in priority_labels]


def build_status_count_items(queryset, field_name, statuses, choice_class=None):
    counts = {}
    for row in queryset.values(field_name).order_by().annotate(total=models.Count("pk")):
        counts[row[field_name]] = row["total"]
    if choice_class is None:
        choice_class = VanBanDen.TrangThai if field_name == "trang_thai_vb_den" else VanBanDi.TrangThai
    return [(f"{get_choice_label(choice_class, status)}:", counts.get(status, 0)) for status in statuses]


def build_priority_processing_count_items():
    priority_labels = ["Hỏa tốc", "Thượng khẩn", "Khẩn", "Bình thường"]
    counts = {label: 0 for label in priority_labels}
    incoming_processing_statuses = [
        VanBanDen.TrangThai.CHO_PHAN_CONG,
        VanBanDen.TrangThai.CHO_XU_LY,
    ]
    outgoing_processing_statuses = [
        VanBanDi.TrangThai.CHO_DUYET,
        VanBanDi.TrangThai.DANG_CHINH_SUA,
        VanBanDi.TrangThai.CHO_DANG_KY,
        VanBanDi.TrangThai.CHO_LUAN_CHUYEN,
        VanBanDi.TrangThai.CHO_PHAN_CONG,
    ]

    for muc_do in VanBanDen.objects.filter(trang_thai_vb_den__in=incoming_processing_statuses).values_list("ma_muc_do__muc_do", flat=True):
        normalized = normalize_text(muc_do)
        for label in priority_labels:
            if normalize_text(label) == normalized:
                counts[label] += 1
                break

    for muc_do in VanBanDi.objects.filter(trang_thai_vb_di__in=outgoing_processing_statuses).values_list("ma_muc_do__muc_do", flat=True):
        normalized = normalize_text(muc_do)
        for label in priority_labels:
            if normalize_text(label) == normalized:
                counts[label] += 1
                break

    return [(f"{label}:", counts[label]) for label in priority_labels]


# Nhom view dieu huong, dang nhap va cac man hinh tong quan van ban.
def login_view(request):
    next_url = request.GET.get("next") or request.POST.get("next") or ""

    if request.user.is_authenticated:
        return redirect(next_url or get_default_home_name_for_user(request.user))

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect(next_url or get_default_home_name_for_user(user))

        matched_user = get_user_model().objects.filter(username=username).first()
        if matched_user is not None and not matched_user.is_active:
            messages.error(request, "Tai khoan da bi khoa.")
        else:
            messages.error(request, "Ten dang nhap hoac mat khau khong dung.")

    return render(request, "login.html", {"next_url": next_url})


def home_view(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return redirect(get_default_home_name_for_user(request.user))


@login_required
def theo_doi_tinh_trang_view(request):
    denied_response = deny_if_no_permission(
        request,
        allowed=can_view_follow_condition(getattr(request.user, "ho_so_giao_vien", None)),
    )
    if denied_response:
        return denied_response
    incoming_statuses = [
        VanBanDen.TrangThai.CHO_PHAN_CONG,
        VanBanDen.TrangThai.CHO_XU_LY,
        VanBanDen.TrangThai.DA_HOAN_THANH,
        VanBanDen.TrangThai.DA_BAN_HANH,
    ]
    outgoing_statuses = [
        VanBanDi.TrangThai.DU_THAO,
        VanBanDi.TrangThai.CHO_DUYET,
        VanBanDi.TrangThai.DANG_CHINH_SUA,
        VanBanDi.TrangThai.CHO_DANG_KY,
        VanBanDi.TrangThai.CHO_LUAN_CHUYEN,
        VanBanDi.TrangThai.CHO_PHAN_CONG,
        VanBanDi.TrangThai.DA_BAN_HANH,
    ]
    context = {
        "page_title": "Theo dõi tình trạng",
        "active_menu": "follow_condition",
        "dashboard_cards": [
            {
                "title": "Văn bản đến",
                "header_class": "blue-header",
                "items": build_status_count_items(VanBanDen.objects.all(), "trang_thai_vb_den", incoming_statuses),
            },
            {
                "title": "Văn bản đi",
                "header_class": "dark-blue-header",
                "items": build_status_count_items(VanBanDi.objects.all(), "trang_thai_vb_di", outgoing_statuses),
            },
            {
                "title": "Loại văn bản",
                "header_class": "dark-blue-header",
                "items": build_document_type_count_items(),
            },
            {
                "title": "Văn bản ưu tiên",
                "header_class": "blue-header",
                "items": build_priority_processing_count_items(),
            },
        ],
    }
    context["dashboard_cards"][0]["title"] = "Văn bản đến"
    context["dashboard_cards"][0]["items"] = build_status_count_items(
        VanBanDen.objects.all(),
        "trang_thai_vb_den",
        incoming_statuses,
        VanBanDen.TrangThai,
    )
    context["dashboard_cards"][1]["title"] = "Văn bản đi"
    context["dashboard_cards"][1]["items"] = build_status_count_items(
        VanBanDi.objects.all(),
        "trang_thai_vb_di",
        outgoing_statuses,
        VanBanDi.TrangThai,
    )
    context["dashboard_cards"][2]["title"] = "Loại văn bản"
    context["dashboard_cards"][3]["title"] = "Văn bản ưu tiên"
    return render(request, "theo_doi_tinh_trang.html", context)


@login_required
def dang_ky_van_ban_den_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(
        request,
        allowed=(giao_vien is None or is_van_thu(giao_vien)),
    )
    if denied_response:
        return denied_response
    if request.method == "POST":
        form = VanBanDenForm(
            request.POST,
            request.FILES,
        )
        if form.is_valid():
            van_ban_den = form.save()
            nguoi_phan_cong = giao_vien
            hieu_truong = get_hieu_truong()
            if hieu_truong and not PhanCongXuLy.objects.filter(so_vb_den=van_ban_den, nguoi_xu_ly=hieu_truong).exists():
                PhanCongXuLy.objects.create(
                    so_vb_den=van_ban_den,
                    nguoi_xu_ly=hieu_truong,
                    nguoi_phan_cong=nguoi_phan_cong,
                    noi_dung_cd="Cho phan cong van ban den",
                    thoi_han=timezone.localdate(),
                    trang_thai_xl=PhanCongXuLy.TrangThaiXuLy.CHO_XU_LY,
                )
            messages.success(request, f"Da tiep nhan van ban den {van_ban_den.so_vb_den}.")
            return redirect("dang_ky_van_ban_den")
    else:
        form = VanBanDenForm()

    context = {
        "page_title": "Dang ky van ban den",
        "active_menu": "incoming_text",
        "form": form,
        "next_so_vb_den": predict_next_prefixed_code(VanBanDen, "so_vb_den", "VBD", 7),
        "default_trang_thai": VanBanDen.TrangThai.CHO_PHAN_CONG,
    }
    return render(request, "van_ban_den_form.html", context)


@login_required
def danh_sach_van_ban_den_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(
        request,
        allowed=can_view_incoming_outgoing(giao_vien),
    )
    if denied_response:
        return denied_response
    documents = list(
        annotate_priority_order(VanBanDen.objects.select_related("ma_loai_vb", "ma_muc_do"))
        .order_by("priority_rank", "-ngay_nhan", "-ngay_ky", "-so_vb_den")
    )
    for document in documents:
        document.status_css_class = get_van_ban_den_status_class(document.trang_thai_vb_den)
        document.trang_thai_hien_thi = get_van_ban_den_status_label(document.trang_thai_vb_den)
        document.attachments_json = serialize_attachment_json(serialize_incoming_attachments(document))

    context = {
        "page_title": "Danh sach van ban den",
        "active_menu": "incoming_text",
        "documents": documents,
        "document_status_choices": build_choice_options(
            VanBanDen.TrangThai,
            [
                VanBanDen.TrangThai.CHO_PHAN_CONG,
                VanBanDen.TrangThai.CHO_XU_LY,
                VanBanDen.TrangThai.DA_HOAN_THANH,
            ],
        ),
        "loai_van_ban_list": LoaiVanBan.objects.filter(ap_dung__in=[1, 2]).order_by("ten_loai_vb"),
        "muc_do_list": MucDoUuTien.objects.order_by("muc_do"),
        "can_manage_documents": giao_vien is None or is_van_thu(giao_vien),
    }
    return render(request, "van_ban_den_list.html", context)


@login_required
def danh_sach_van_ban_di_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(
        request,
        allowed=can_view_incoming_outgoing(giao_vien),
    )
    if denied_response:
        return denied_response
    documents = list(
        annotate_priority_order(VanBanDi.objects.select_related("ma_loai_vb", "ma_muc_do", "nguoi_tao", "nguoi_ky"))
        .prefetch_related("xu_lys__ma_gv")
        .order_by("priority_rank", "-ngay_ban_hanh", "-ngay_ky", "-so_vb_di")
    )
    for document in documents:
        document.status_css_class = get_van_ban_di_status_class(document.trang_thai_vb_di)
        document.trang_thai_hien_thi = get_van_ban_di_status_label(document.trang_thai_vb_di)
        document.nguoi_ky_hien_thi = get_document_signers_display(document)
        document.ban_du_thao_attachments_json = serialize_attachment_json(
            serialize_outgoing_supporting_attachments(document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
        )
        document.ban_chinh_thuc_attachments_json = serialize_attachment_json(
            serialize_outgoing_supporting_attachments(document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
        )

    context = {
        "page_title": "Danh sach van ban di",
        "active_menu": "outgoing_text",
        "documents": documents,
        "document_status_choices": build_choice_options(
            VanBanDi.TrangThai,
            [
                VanBanDi.TrangThai.DU_THAO,
                VanBanDi.TrangThai.CHO_DUYET,
                VanBanDi.TrangThai.DANG_CHINH_SUA,
                VanBanDi.TrangThai.CHO_DANG_KY,
                VanBanDi.TrangThai.DA_DANG_KY,
                VanBanDi.TrangThai.DA_HOAN_THANH,
            ],
        ),
        "loai_van_ban_list": LoaiVanBan.objects.filter(ap_dung__in=[0, 2]).order_by("ten_loai_vb"),
        "muc_do_list": MucDoUuTien.objects.order_by("muc_do"),
        "giao_vien_list": GiaoVien.objects.order_by("ho_ten"),
        "recipient_list": NoiNhan.objects.order_by("ten_noi_nhan"),
        "can_manage_documents": giao_vien is None or is_van_thu(giao_vien),
    }
    return render(request, "van_ban_di_list.html", context)


# Nhom view tao moi, dang ky va quan ly mau van ban di/den.
@login_required
def dang_ky_van_ban_di_tu_danh_muc_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=(giao_vien is None or is_van_thu(giao_vien)))
    if denied_response:
        return denied_response
    next_so_vb_di = predict_next_prefixed_code(VanBanDi, "so_vb_di", "VBO", 8)
    document = build_manual_outgoing_registration_document(so_vb_di=next_so_vb_di, trang_thai=VanBanDi.TrangThai.CHO_DANG_KY)

    if request.method == "POST":
        form = VanBanDiDangKyForm(
            request.POST,
            copy_request_files_with_aliases(request, {"ban_chinh_thuc_uploads": "ban_chinh_thuc"}),
            create_mode=True,
            giao_vien=giao_vien,
        )
        if form.is_valid():
            registered_document = form.save(commit=False)
            if not registered_document.ngay_ban_hanh:
                registered_document.ngay_ban_hanh = timezone.localdate()
            registered_document.trang_thai_vb_di = VanBanDi.TrangThai.CHO_DANG_KY
            registered_document.ban_du_thao = ""
            so_thu_tu, so_ky_hieu = generate_registration_number(VanBanDi, registered_document)
            registered_document.so_thu_tu = so_thu_tu
            registered_document.so_ky_hieu = so_ky_hieu
            registered_document.trang_thai_vb_di = VanBanDi.TrangThai.DA_DANG_KY
            registered_document.save()
            form.save_uploaded_files(registered_document)
            messages.success(request, f"Da dang ky van ban di {registered_document.so_vb_di}.")
            return redirect("dang_ky_van_ban_di", so_vb_di=registered_document.so_vb_di)
    else:
        form = VanBanDiDangKyForm(create_mode=True, giao_vien=giao_vien)

    context = {
        "page_title": "Dang ky van ban di",
        "active_menu": "outgoing_text",
        "document": document,
        "form": form,
        "can_register": True,
        "can_transfer": False,
        "is_new_registration": True,
        "show_draft_file": False,
        "registration_page_url": reverse("dang_ky_van_ban_di_tu_danh_muc"),
    }
    return render(request, "van_ban_di_form.html", context)


@login_required
def tao_van_ban_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_create_document(giao_vien))
    if denied_response:
        return denied_response
    if request.method == "POST":
        form = TaoVanBanDiForm(
            request.POST,
            copy_request_files_with_aliases(request, {"ban_du_thao_uploads": "ban_du_thao"}),
            giao_vien=giao_vien,
        )
        if form.is_valid():
            van_ban_di = form.save(commit=False)
            hieu_truong = get_hieu_truong()
            nguoi_duyet_dau_tien, vai_tro_ky = get_initial_approver_for_outgoing_document(giao_vien, van_ban_di.ma_loai_vb)
            if nguoi_duyet_dau_tien is None:
                form.add_error(None, "Khong xac dinh duoc nguoi duyet dau tien cho van ban nay.")
            else:
                van_ban_di.nguoi_ky = hieu_truong or nguoi_duyet_dau_tien
                van_ban_di.save()
                form.save_uploaded_files(van_ban_di)
                if (
                    (is_truong_bo_mon(giao_vien) or is_phong_ban_to_chuc(giao_vien))
                    and van_ban_di.ma_loai_vb.twocap == LoaiVanBan.TWO_CAP_HAI_CAP
                    and hieu_truong
                ):
                    XuLy.objects.create(
                        ma_vb_di=van_ban_di,
                        ma_gv=giao_vien,
                        vai_tro_ky=XuLy.VAI_TRO_KY_NHAY,
                        trang_thai_ky=XuLy.TRANG_THAI_DA_DUYET,
                        thoi_gian_ky=timezone.now(),
                    )
                    XuLy.objects.create(
                        ma_vb_di=van_ban_di,
                        ma_gv=hieu_truong,
                        vai_tro_ky=XuLy.VAI_TRO_KY_CHINH,
                        trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
                    )
                else:
                    XuLy.objects.create(
                        ma_vb_di=van_ban_di,
                        ma_gv=nguoi_duyet_dau_tien,
                        vai_tro_ky=vai_tro_ky,
                        trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
                    )
                messages.success(request, f"Da gui duyet van ban di {van_ban_di.so_vb_di}.")
                return redirect("danh_sach_van_ban_di")
    else:
        form = TaoVanBanDiForm(giao_vien=giao_vien)

    context = {
        "page_title": "Tao van ban",
        "active_menu": "create_text",
        "next_so_vb_di": predict_next_prefixed_code(VanBanDi, "so_vb_di", "VBO", 8),
        "loai_van_ban_list": LoaiVanBan.objects.filter(ap_dung__in=[0, 2]).order_by("ten_loai_vb"),
        "template_list": MauVanBan.objects.filter(trang_thai=MauVanBan.TRANG_THAI_DANG_SU_DUNG)
        .select_related("ma_loai_vb")
        .order_by("ten_mau"),
        "form": form,
    }
    return render(request, "tao_van_ban.html", context)


@login_required
def them_mau_van_ban_view(request):
    denied_response = deny_if_no_permission(
        request,
        allowed=can_manage_templates(getattr(request.user, "ho_so_giao_vien", None)),
    )
    if denied_response:
        return denied_response
    if request.method == "POST":
        form = ThemMauVanBanForm(request.POST, request.FILES)
        if form.is_valid():
            mau_van_ban = form.save()
            messages.success(request, f"Da luu mau van ban {mau_van_ban.ma_mau_vb}.")
            return redirect("them_mau_van_ban")
    else:
        form = ThemMauVanBanForm()

    context = {
        "page_title": "Them mau van ban",
        "active_menu": "template_text",
        "next_ma_mau_vb": predict_next_prefixed_code(MauVanBan, "ma_mau_vb", "MVB", 7),
        "form": form,
    }
    return render(request, "them_mau_van_ban.html", context)


# Nhom view duyet, phan cong va theo doi tien do xu ly cong viec.
@login_required
def duyet_van_ban_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_work(giao_vien))
    if denied_response:
        return denied_response
    if giao_vien is None:
        messages.error(request, "Tai khoan hien tai chua lien ket voi giao vien.")
        return redirect("theo_doi_tinh_trang")

    xu_ly_list = (
        XuLy.objects.filter(ma_gv=giao_vien)
        .exclude(
            trang_thai_ky__in=[
                XuLy.TRANG_THAI_DA_DUYET,
                XuLy.TRANG_THAI_DA_UY_QUYEN,
                XuLy.TRANG_THAI_CHO_CHINH_SUA,
            ]
        )
        .select_related("ma_vb_di__ma_loai_vb", "ma_vb_di__nguoi_tao", "ma_vb_di__nguoi_ky", "ma_gv")
        .prefetch_related("ma_vb_di__phan_congs__nguoi_xu_ly", "ma_vb_di__nhat_kys__ma_nguoi_tao", "ma_vb_di__xu_lys__ma_gv")
        .order_by("-ma_vb_di__ngay_ban_hanh", "-ma_vb_di__so_vb_di")
    )
    documents = []
    for index, xu_ly in enumerate(xu_ly_list, start=1):
        document = xu_ly.ma_vb_di
        latest_revision = document.nhat_kys.order_by("-thoi_gian_tao").first()
        document.stt = index
        real_assignments = get_real_assignments_queryset(document)
        document.assignment_status = "Da phan cong" if real_assignments.exists() else "Chua phan cong"
        approval_status_labels = {
            XuLy.TRANG_THAI_CHO_DUYET: "Cho duyet",
            XuLy.TRANG_THAI_DA_DUYET: "Da duyet",
            XuLy.TRANG_THAI_DA_UY_QUYEN: "Da uy quyen",
            XuLy.TRANG_THAI_CHO_CHINH_SUA: "Cho chinh sua",
        }
        document.approval_status = approval_status_labels.get(xu_ly.trang_thai_ky, xu_ly.trang_thai_ky)
        document.assigned_ids_csv = ",".join(real_assignments.values_list("nguoi_xu_ly_id", flat=True))
        document.chi_dao = real_assignments.first().noi_dung_cd if real_assignments.exists() else ""
        document.current_step = xu_ly.vai_tro_ky
        document.current_status = xu_ly.trang_thai_ky
        document.latest_revision_request = latest_revision.yc_chinh_sua if latest_revision else ""
        document.latest_revision_author = latest_revision.ma_nguoi_tao.ho_ten if latest_revision else ""
        document.nguoi_ky_hien_thi = get_document_signers_display(document)
        document.can_delegate = is_hieu_truong(giao_vien)
        document.can_forward = xu_ly.vai_tro_ky == XuLy.VAI_TRO_KY_NHAY
        documents.append(document)

    context = {
        "page_title": "Quan ly cong viec",
        "active_menu": "work_management",
        "documents": documents,
        "giao_vien_list": GiaoVien.objects.order_by("ho_ten"),
        "pho_hieu_truong_list": get_pho_hieu_truong_list(),
        "co_quan_ban_hanh": getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND"),
    }
    return render(request, "duyet_van_ban.html", context)


@login_required
def can_phan_cong_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_work(giao_vien))
    if denied_response:
        return denied_response
    documents = build_assignment_documents(
        incoming_status=VanBanDen.TrangThai.CHO_PHAN_CONG,
        outgoing_status=None,
    )
    pending_assignments = (
        PhanCongXuLy.objects.filter(nguoi_xu_ly=giao_vien)
        .select_related("so_vb_den__ma_loai_vb", "so_vb_di__ma_loai_vb", "so_vb_di__nguoi_tao")
        .prefetch_related("so_vb_den__phan_congs__nguoi_xu_ly", "so_vb_di__phan_congs__nguoi_xu_ly")
    )
    document_keys = {(item["loai"], item["record_id"]) for item in documents}
    for assignment in pending_assignments:
        document = assignment.so_vb_den or assignment.so_vb_di
        if document is None:
            continue
        current_status = document.trang_thai_vb_den if assignment.so_vb_den_id else document.trang_thai_vb_di
        if assignment.so_vb_den_id:
            if normalize_text(current_status) != normalize_text(VanBanDen.TrangThai.CHO_PHAN_CONG):
                continue
        elif not document.da_gui_phan_cong:
            continue
        loai = "den" if assignment.so_vb_den_id else "di"
        record_id = document.pk
        document_key = (loai, record_id)
        if document_key in document_keys:
            continue
        phan_congs = get_real_assignments_queryset(document).select_related("nguoi_xu_ly")
        documents.append(
            {
                "loai": loai,
                "record_id": record_id,
                "so_van_ban": document.so_vb_den if loai == "den" else document.so_vb_di,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "nguoi_gui": document.co_quan_ban_hanh if loai == "den" else document.nguoi_tao.ho_ten,
                "co_quan_ban_hanh": (
                    document.co_quan_ban_hanh
                    if loai == "den"
                    else getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND")
                ),
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "priority_rank": get_priority_rank(document.ma_muc_do.muc_do),
                "thoi_gian": document.ngay_nhan if loai == "den" else document.ngay_ky,
                "file_name": (
                    build_primary_file_payload(document.file_van_ban)["name"]
                    if loai == "den"
                    else build_primary_file_payload(document.ban_chinh_thuc)["name"]
                ),
                "file_url": (
                    build_primary_file_payload(document.file_van_ban)["url"]
                    if loai == "den"
                    else build_primary_file_payload(document.ban_chinh_thuc)["url"]
                ),
                "attachments_json": serialize_attachment_json(
                    serialize_incoming_attachments(document)
                    if loai == "den"
                    else serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
                ),
                "noi_dung_cd": assignment.noi_dung_cd,
                "thoi_han": assignment.thoi_han.strftime("%Y-%m-%d") if assignment.thoi_han else "",
                "assigned_ids": list(phan_congs.values_list("nguoi_xu_ly_id", flat=True)),
                "assignment_details": [
                    {"id": phan_cong.nguoi_xu_ly_id, "name": phan_cong.nguoi_xu_ly.ho_ten, "instruction": phan_cong.noi_dung_cd}
                    for phan_cong in phan_congs
                ],
                "trang_thai": current_status if loai == "den" else "Da gui phan cong",
            }
        )
        document_keys.add(document_key)

    documents.sort(
        key=lambda item: (
            item.get("priority_rank", 3),
            -(item["thoi_gian"].toordinal() if item["thoi_gian"] else timezone.datetime.min.date().toordinal()),
        )
    )
    for index, document in enumerate(documents, start=1):
        document["stt"] = index

    context = {
        "page_title": "Can phan cong",
        "active_menu": "work_management",
        "documents": [serialize_van_ban_can_phan_cong(document) | {"stt": document["stt"]} for document in documents],
        "giao_vien_list": get_assignable_teachers_for_user(giao_vien),
        "assignment_list_mode": "pending",
        "is_pending_assignment_list": True,
        "is_assigned_assignment_list": False,
    }
    return render(request, "can_phan_cong.html", context)


@login_required
def da_phan_cong_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_work(giao_vien))
    if denied_response:
        return denied_response
    documents = build_assigned_documents_for_user(giao_vien)

    context = {
        "page_title": "Da phan cong",
        "active_menu": "work_management",
        "documents": [serialize_van_ban_can_phan_cong(document) | {"stt": document["stt"]} for document in documents],
        "giao_vien_list": get_assignable_teachers_for_user(giao_vien),
        "assignment_list_mode": "assigned",
        "is_pending_assignment_list": False,
        "is_assigned_assignment_list": True,
    }
    return render(request, "can_phan_cong.html", context)


@login_required
def theo_doi_tien_do_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_work(giao_vien))
    if denied_response:
        return denied_response
    documents = build_progress_tracking_documents(giao_vien)

    context = {
        "page_title": "Theo doi tien do",
        "active_menu": "work_management",
        "documents": documents,
        "is_progress_tracking_list": True,
    }
    return render(request, "theo_doi_tien_do.html", context)


@login_required
def chi_tiet_tien_do_view(request):
    loai = request.GET.get("loai", "").strip()
    record_id = request.GET.get("record_id", "").strip()
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_work(giao_vien))
    if denied_response:
        return denied_response

    if loai not in {"den", "di"}:
        return JsonResponse({"success": False, "message": "Loai van ban khong hop le."}, status=400)
    if not record_id:
        return JsonResponse({"success": False, "message": "Thieu ma van ban."}, status=400)
    if giao_vien is None:
        return JsonResponse({"success": False, "message": "Tai khoan hien tai chua lien ket voi giao vien."}, status=400)

    filters = {"nguoi_phan_cong": giao_vien}
    if loai == "den":
        filters["so_vb_den_id"] = record_id
    else:
        filters["so_vb_di_id"] = record_id

    assignments = (
        PhanCongXuLy.objects.filter(**filters)
        .select_related("nguoi_xu_ly")
        .order_by("thoi_han", "thoi_gian_phan_cong", "ma_xu_ly")
    )
    return JsonResponse({"success": True, "details": build_progress_assignment_details(assignments)})


# Nhom ham tong hop cong viec ca nhan, van ban da ban hanh va van ban da tao.
def build_personal_processing_documents(giao_vien):
    assignments = (
        PhanCongXuLy.objects.filter(nguoi_xu_ly=giao_vien).exclude(noi_dung_cd=ASSIGNMENT_PLACEHOLDER_NOTE)
        .select_related("so_vb_den__ma_loai_vb", "so_vb_di__ma_loai_vb", "so_vb_di__nguoi_tao", "nguoi_phan_cong")
        .order_by("-thoi_gian_phan_cong", "ma_xu_ly")
    )
    documents = []
    for index, assignment in enumerate(assignments, start=1):
        document = assignment.so_vb_den or assignment.so_vb_di
        if document is None:
            continue
        current_status = document.trang_thai_vb_den if assignment.so_vb_den_id else document.trang_thai_vb_di
        if normalize_text(current_status) == normalize_text(
            VanBanDen.TrangThai.CHO_PHAN_CONG if assignment.so_vb_den_id else VanBanDi.TrangThai.CHO_PHAN_CONG
        ):
            continue
        is_incoming = assignment.so_vb_den_id is not None
        documents.append(
            {
                "assignment_id": assignment.pk,
                "loai": "den" if is_incoming else "di",
                "record_id": document.pk,
                "so_van_ban": document.so_vb_den if is_incoming else document.so_vb_di,
                "ngay_ban_hanh_display": (
                    (document.ngay_ky if is_incoming else (document.ngay_ban_hanh or document.ngay_ky)).strftime("%d/%m/%Y")
                    if (document.ngay_ky if is_incoming else (document.ngay_ban_hanh or document.ngay_ky))
                    else ""
                ),
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "priority_rank": get_priority_rank(document.ma_muc_do.muc_do),
                "sort_date": document.ngay_ky if is_incoming else (document.ngay_ban_hanh or document.ngay_ky),
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "co_quan_ban_hanh": (
                    document.co_quan_ban_hanh if is_incoming else getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND")
                ),
                "nguoi_phan_cong": assignment.nguoi_phan_cong.ho_ten if assignment.nguoi_phan_cong else "",
                "noi_dung_cd": assignment.noi_dung_cd,
                "thoi_han": assignment.thoi_han.strftime("%Y-%m-%d") if assignment.thoi_han else "",
                "trang_thai_xl": assignment.trang_thai_xl,
                "file_name": (
                    build_primary_file_payload(document.file_van_ban)["name"]
                    if is_incoming
                    else (
                        build_primary_file_payload(document.ban_chinh_thuc or document.ban_du_thao)["name"]
                    )
                ),
                "file_url": (
                    build_primary_file_payload(document.file_van_ban)["url"]
                    if is_incoming
                    else (
                        build_primary_file_payload(document.ban_chinh_thuc or document.ban_du_thao)["url"]
                    )
                ),
                "attachments_json": serialize_attachment_json(
                    serialize_incoming_attachments(document)
                    if is_incoming
                    else (
                        serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
                        or serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
                    )
                ),
            }
        )
    documents.sort(
        key=lambda item: (
            item.get("priority_rank", 3),
            -(item["sort_date"].toordinal() if item.get("sort_date") else timezone.datetime.min.date().toordinal()),
        )
    )
    for index, document in enumerate(documents, start=1):
        document["stt"] = index
    return documents


def build_published_documents():
    documents = []
    incoming_documents = (
        annotate_priority_order(VanBanDen.objects.filter(da_ban_hanh_noi_bo=True))
        .select_related("ma_loai_vb", "ma_muc_do")
        .order_by("priority_rank", "-ngay_nhan", "-so_vb_den")
    )
    outgoing_documents = (
        annotate_priority_order(VanBanDi.objects.filter(da_ban_hanh_noi_bo=True))
        .select_related("ma_loai_vb", "ma_muc_do", "nguoi_tao", "nguoi_ky")
        .order_by("priority_rank", "-ngay_ban_hanh", "-so_vb_di")
    )

    for document in incoming_documents:
        documents.append(
            {
                "loai": "den",
                "record_id": document.pk,
                "so_van_ban": document.so_vb_den,
                "ngay_ban_hanh_display": document.ngay_ky.strftime("%d/%m/%Y") if document.ngay_ky else "",
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "priority_rank": get_priority_rank(document.ma_muc_do.muc_do),
                "sort_date": document.ngay_ky,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "nguon": "Van ban den",
                "co_quan_ban_hanh": document.co_quan_ban_hanh,
                "trang_thai": "Da ban hanh noi bo",
                "file_name": build_primary_file_payload(document.file_van_ban)["name"],
                "file_url": build_primary_file_payload(document.file_van_ban)["url"],
                "attachments_json": serialize_attachment_json(serialize_incoming_attachments(document)),
                "edit_url": reverse("danh_sach_van_ban_den"),
            }
        )

    for document in outgoing_documents:
        documents.append(
            {
                "loai": "di",
                "record_id": document.pk,
                "so_van_ban": document.so_vb_di,
                "ngay_ban_hanh_display": (
                    (document.ngay_ban_hanh or document.ngay_ky).strftime("%d/%m/%Y")
                    if (document.ngay_ban_hanh or document.ngay_ky)
                    else ""
                ),
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "priority_rank": get_priority_rank(document.ma_muc_do.muc_do),
                "sort_date": document.ngay_ban_hanh or document.ngay_ky,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "nguon": "Van ban di",
                "co_quan_ban_hanh": getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND"),
                "trang_thai": "Da ban hanh noi bo",
                "file_name": build_primary_file_payload(document.ban_chinh_thuc or document.ban_du_thao)["name"],
                "file_url": build_primary_file_payload(document.ban_chinh_thuc or document.ban_du_thao)["url"],
                "attachments_json": serialize_attachment_json(
                    serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
                    or serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
                ),
                "edit_url": reverse("danh_sach_van_ban_di"),
            }
        )

    documents.sort(
        key=lambda item: (
            item.get("priority_rank", 3),
            -(item["sort_date"].toordinal() if item.get("sort_date") else timezone.datetime.min.date().toordinal()),
        )
    )
    for index, document in enumerate(documents, start=1):
        document["stt"] = index
    return documents


def build_created_documents(giao_vien):
    documents = []
    outgoing_documents = (
        annotate_priority_order(VanBanDi.objects.filter(nguoi_tao=giao_vien))
        .select_related("ma_loai_vb", "ma_muc_do")
        .order_by("priority_rank", "-ngay_ban_hanh", "-so_vb_di")
    )
    for index, document in enumerate(outgoing_documents, start=1):
        documents.append(
            {
                "stt": index,
                "loai": "di",
                "record_id": document.pk,
                "so_van_ban": document.so_vb_di,
                "ngay_ban_hanh_display": (
                    (document.ngay_ban_hanh or document.ngay_ky).strftime("%d/%m/%Y")
                    if (document.ngay_ban_hanh or document.ngay_ky)
                    else ""
                ),
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "nguon": "Van ban di",
                "co_quan_ban_hanh": getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND"),
                "trang_thai": document.trang_thai_vb_di,
                "file_name": build_primary_file_payload(document.ban_du_thao)["name"],
                "file_url": build_primary_file_payload(document.ban_du_thao)["url"],
                "attachments_json": serialize_attachment_json(
                    serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
                ),
            }
        )
    return documents


def build_returned_documents(giao_vien):
    documents = []
    van_ban_dis = (
        VanBanDi.objects.filter(nguoi_tao=giao_vien)
        .select_related("ma_loai_vb")
        .prefetch_related("nhat_kys__ma_nguoi_tao")
        .order_by("-ngay_ban_hanh", "-so_vb_di")
    )
    for document in van_ban_dis:
        latest_revision = document.nhat_kys.order_by("-thoi_gian_tao").first()
        if latest_revision is None or normalize_text(latest_revision.trang_thai) != normalize_text(NhatKyVanBan.TrangThai.CHO_CHINH_SUA):
            continue
        documents.append(
            {
                "stt": len(documents) + 1,
                "record_id": document.pk,
                "so_van_ban": document.so_vb_di,
                "ngay_ban_hanh_display": document.ngay_ban_hanh.strftime("%d/%m/%Y") if document.ngay_ban_hanh else "",
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "ma_loai_vb": document.ma_loai_vb_id,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "nguoi_yeu_cau": latest_revision.ma_nguoi_tao.ho_ten,
                "noi_dung_yeu_cau": latest_revision.yc_chinh_sua,
                "trang_thai": latest_revision.trang_thai,
                "file_name": build_primary_file_payload(document.ban_du_thao)["name"],
                "file_url": build_primary_file_payload(document.ban_du_thao)["url"],
                "attachments_json": serialize_attachment_json(
                    serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
                ),
            }
        )
    return documents


def build_external_published_documents():
    documents = []
    external_records = (
        LuanChuyenBenNgoai.objects.select_related(
            "ma_vb_di",
            "ma_vb_di__ma_loai_vb",
            "ma_noi_nhan",
            "nguoi_thuc_hien",
        )
        .order_by("-thoi_gian_gui", "-ma_luan_chuyen")
    )
    for index, record in enumerate(external_records, start=1):
        document = record.ma_vb_di
        documents.append(
            {
                "stt": index,
                "record_id": record.pk,
                "so_van_ban": document.so_vb_di,
                "ngay_ban_hanh_display": (
                    (document.ngay_ban_hanh or document.ngay_ky).strftime("%d/%m/%Y")
                    if (document.ngay_ban_hanh or document.ngay_ky)
                    else ""
                ),
                "ten_loai_vb": document.ma_loai_vb.ten_loai_vb,
                "so_ky_hieu": document.so_ky_hieu,
                "trich_yeu": document.trich_yeu,
                "trang_thai": record.trang_thai_gui,
                "noi_nhan_tong_hop": record.ma_noi_nhan.ten_noi_nhan,
                "nguoi_thuc_hien": record.nguoi_thuc_hien.ho_ten,
                "nguoi_thuc_hien_id": record.nguoi_thuc_hien_id,
                "ghi_chu": record.ghi_chu,
                "ma_noi_nhan": record.ma_noi_nhan_id,
                "thoi_gian_gui": (
                    timezone.localtime(record.thoi_gian_gui).strftime("%d/%m/%Y %H:%M")
                    if record.thoi_gian_gui
                    else ""
                ),
                "file_name": build_primary_file_payload(document.ban_chinh_thuc or document.ban_du_thao)["name"],
                "file_url": build_primary_file_payload(document.ban_chinh_thuc or document.ban_du_thao)["url"],
                "attachments_json": serialize_attachment_json(
                    serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
                    or serialize_outgoing_attachments(document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
                ),
            }
        )
    return documents


# Nhom view cong viec ca nhan va danh sach van ban theo nguoi dung.
@login_required
def van_ban_xu_ly_ca_nhan_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_personal_work(giao_vien))
    if denied_response:
        return denied_response
    context = {
        "page_title": "Cong viec ca nhan",
        "active_menu": "personal_work",
        "documents": build_personal_processing_documents(giao_vien),
        "is_personal_processing_list": True,
        "is_personal_returned_list": False,
        "can_transfer_assignment": is_truong_bo_mon(giao_vien) or is_phong_ban_to_chuc(giao_vien),
    }
    return render(request, "cong_viec_ca_nhan.html", context)


@login_required
def van_ban_tra_lai_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_personal_work(giao_vien))
    if denied_response:
        return denied_response
    context = {
        "page_title": "Cong viec ca nhan",
        "active_menu": "personal_work",
        "documents": build_returned_documents(giao_vien),
        "loai_van_ban_list": LoaiVanBan.objects.filter(ap_dung__in=[0, 2]).order_by("ten_loai_vb"),
        "is_personal_processing_list": False,
        "is_personal_returned_list": True,
        "can_transfer_assignment": False,
    }
    return render(request, "cong_viec_ca_nhan.html", context)


@login_required
def van_ban_da_ban_hanh_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_view_document_list(giao_vien))
    if denied_response:
        return denied_response
    context = {
        "page_title": "Danh sach van ban",
        "active_menu": "document_list",
        "documents": build_published_documents(),
        "is_published_document_list": True,
        "is_created_document_list": False,
        "can_edit_published_documents": is_van_thu(giao_vien),
    }
    return render(request, "danh_sach_van_ban.html", context)


@login_required
def van_ban_da_tao_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_view_created_document_list(giao_vien))
    if denied_response:
        return denied_response
    context = {
        "page_title": "Danh sach van ban",
        "active_menu": "document_list",
        "documents": build_created_documents(giao_vien),
        "is_published_document_list": False,
        "is_created_document_list": True,
        "can_edit_published_documents": False,
    }
    return render(request, "danh_sach_van_ban.html", context)


@login_required
def van_ban_phat_hanh_ben_ngoai_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(
        request,
        allowed=(giao_vien is None or is_van_thu(giao_vien)),
    )
    if denied_response:
        return denied_response
    context = {
        "page_title": "Phat hanh ben ngoai",
        "active_menu": "outgoing_text",
        "documents": build_external_published_documents(),
        "recipient_list": NoiNhan.objects.order_by("ten_noi_nhan"),
        "is_external_published_list": True,
    }
    return render(request, "van_ban_phat_hanh_ben_ngoai.html", context)


@login_required
def cap_nhat_tien_do_ca_nhan_view(request, ma_xu_ly):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_personal_work(giao_vien))
    if denied_response:
        return denied_response
    assignment = get_object_or_404(PhanCongXuLy.objects.select_related("nguoi_xu_ly"), pk=ma_xu_ly, nguoi_xu_ly=giao_vien)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)
    trang_thai_xl = request.POST.get("trang_thai_xl", "").strip()
    if trang_thai_xl not in {
        PhanCongXuLy.TrangThaiXuLy.DANG_XU_LY,
        PhanCongXuLy.TrangThaiXuLy.DA_HOAN_THANH,
    }:
        return JsonResponse({"success": False, "message": "Trang thai cap nhat khong hop le."}, status=400)
    assignment.trang_thai_xl = trang_thai_xl
    assignment.save(update_fields=["trang_thai_xl"])
    parent_document = assignment.so_vb_den or assignment.so_vb_di
    if parent_document is not None:
        sync_document_processing_status_from_assignments(parent_document, is_incoming=assignment.so_vb_den_id is not None)
    return JsonResponse({"success": True, "message": "Da cap nhat tien do xu ly.", "trang_thai_xl": assignment.trang_thai_xl})


@login_required
def chuyen_phan_cong_ca_nhan_view(request, ma_xu_ly):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_personal_work(giao_vien))
    if denied_response:
        return denied_response
    assignment = get_object_or_404(PhanCongXuLy.objects.select_related("nguoi_xu_ly", "so_vb_den", "so_vb_di"), pk=ma_xu_ly, nguoi_xu_ly=giao_vien)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)
    if not (is_truong_bo_mon(giao_vien) or is_phong_ban_to_chuc(giao_vien)):
        return JsonResponse({"success": False, "message": "Ban khong co quyen chuyen phan cong."}, status=403)
    if is_truong_bo_mon(giao_vien) and giao_vien.ma_to_id is None:
        return JsonResponse({"success": False, "message": "Tai khoan to truong chua duoc gan to chuyen mon."}, status=400)

    if is_truong_bo_mon(giao_vien):
        related_assignments = PhanCongXuLy.objects.filter(
            so_vb_den=assignment.so_vb_den,
            so_vb_di=assignment.so_vb_di,
        ).select_related("nguoi_xu_ly")
        has_teacher_assignment = any(
            item.nguoi_xu_ly_id != giao_vien.pk
            and item.nguoi_xu_ly.ma_to_id == giao_vien.ma_to_id
            and not is_truong_bo_mon(item.nguoi_xu_ly)
            for item in related_assignments
        )
        if has_teacher_assignment:
            return JsonResponse(
                {"success": False, "message": "Van ban nay da co giao vien trong to duoc phan cong xu ly."},
                status=400,
            )

    assignment.trang_thai_xl = PhanCongXuLy.TrangThaiXuLy.CHO_XU_LY
    assignment.save(update_fields=["trang_thai_xl"])
    parent_document = assignment.so_vb_den or assignment.so_vb_di
    if assignment.so_vb_den_id and parent_document is not None:
        parent_document.trang_thai_vb_den = VanBanDen.TrangThai.CHO_PHAN_CONG
        parent_document.save(update_fields=["trang_thai_vb_den"])
    elif parent_document is not None:
        parent_document.trang_thai_vb_di = VanBanDi.TrangThai.DA_DANG_KY
        parent_document.save(update_fields=["trang_thai_vb_di"])
    return JsonResponse({"success": True, "message": "Da chuyen van ban sang muc can phan cong cua to truong."})


@login_required
def hoan_thanh_chinh_sua_van_ban_view(request, so_vb_di):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_personal_work(giao_vien))
    if denied_response:
        return denied_response
    document = get_object_or_404(VanBanDi.objects.prefetch_related("nhat_kys"), pk=so_vb_di, nguoi_tao=giao_vien)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)
    latest_revision = document.nhat_kys.order_by("-thoi_gian_tao").first()
    if latest_revision is None or normalize_text(latest_revision.trang_thai) != normalize_text(NhatKyVanBan.TrangThai.CHO_CHINH_SUA):
        return JsonResponse({"success": False, "message": "Van ban nay khong co yeu cau chinh sua dang mo."}, status=400)

    trich_yeu = request.POST.get("trich_yeu", "").strip()
    ma_loai_vb_id = request.POST.get("ma_loai_vb", "").strip()
    uploaded_files = request.FILES.getlist("ban_du_thao")

    if not trich_yeu:
        return JsonResponse({"success": False, "message": "Vui long nhap trich yeu van ban."}, status=400)
    if not ma_loai_vb_id:
        return JsonResponse({"success": False, "message": "Vui long chon loai van ban."}, status=400)

    loai_van_ban = get_object_or_404(LoaiVanBan.objects.filter(ap_dung__in=[0, 2]), pk=ma_loai_vb_id)
    document.trich_yeu = trich_yeu
    document.ma_loai_vb = loai_van_ban
    if uploaded_files:
        document.ban_du_thao = uploaded_files[0]
    document.trang_thai_vb_di = VanBanDi.TrangThai.CHO_DUYET
    document.save()
    if uploaded_files:
        start_index = document.tep_dinh_kem_dis.filter(loai_tep=TepDinhKemVanBanDi.LoaiTep.DU_THAO).count()
        if not document.tep_dinh_kem_dis.filter(
            loai_tep=TepDinhKemVanBanDi.LoaiTep.DU_THAO,
            tep_tin=document.ban_du_thao.name,
        ).exists():
            TepDinhKemVanBanDi.objects.create(
                so_vb_di=document,
                loai_tep=TepDinhKemVanBanDi.LoaiTep.DU_THAO,
                tep_tin=document.ban_du_thao.name,
                thu_tu=start_index,
            )
            start_index += 1
        for offset, uploaded_file in enumerate(uploaded_files[1:], start=start_index):
            TepDinhKemVanBanDi.objects.create(
                so_vb_di=document,
                loai_tep=TepDinhKemVanBanDi.LoaiTep.DU_THAO,
                tep_tin=uploaded_file,
                thu_tu=offset,
            )
    latest_revision.trang_thai = NhatKyVanBan.TrangThai.DA_CHINH_SUA
    latest_revision.save(update_fields=["trang_thai"])
    document.xu_lys.filter(trang_thai_ky=XuLy.TRANG_THAI_CHO_CHINH_SUA).update(
        trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET
    )
    return JsonResponse({"success": True, "message": f"Da cap nhat ban du thao cho van ban {document.so_vb_di}."})


# Nhom API xu ly thao tac phan cong, duyet va cap nhat trang thai van ban.
@login_required
def luu_phan_cong_xu_ly_view(request):
    denied_response = deny_if_no_permission(
        request,
        allowed=can_manage_work(getattr(request.user, "ho_so_giao_vien", None)),
    )
    if denied_response:
        return denied_response
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    loai = request.POST.get("loai")
    record_id = request.POST.get("record_id")
    assignment_payload = request.POST.get("assignment_payload", "").strip()
    thoi_han = request.POST.get("thoi_han", "").strip()

    try:
        assignment_rows = json.loads(assignment_payload) if assignment_payload else []
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Du lieu phan cong khong hop le."}, status=400)

    normalized_assignment_rows = []
    for row in assignment_rows:
        giao_vien_id = str(row.get("id", "")).strip()
        noi_dung_cd = str(row.get("instruction", "")).strip()
        if not giao_vien_id:
            continue
        normalized_assignment_rows.append(
            {
                "id": giao_vien_id,
                "instruction": noi_dung_cd,
            }
        )

    assigned_ids = [row["id"] for row in normalized_assignment_rows]

    if loai not in {"den", "di"}:
        return JsonResponse({"success": False, "message": "Loai van ban khong hop le."}, status=400)
    if not record_id:
        return JsonResponse({"success": False, "message": "Thieu ma van ban de phan cong."}, status=400)
    if not assigned_ids:
        return JsonResponse({"success": False, "message": "Vui long chon it nhat mot nguoi xu ly."}, status=400)
    if not thoi_han:
        return JsonResponse({"success": False, "message": "Vui long chon thoi han xu ly."}, status=400)
    if any(not row["instruction"] for row in normalized_assignment_rows):
        return JsonResponse(
            {"success": False, "message": "Vui long nhap noi dung chi dao cho tung nguoi xu ly."},
            status=400,
        )
    nguoi_phan_cong = getattr(request.user, "ho_so_giao_vien", None)

    if loai == "den":
        document = get_object_or_404(VanBanDen, pk=record_id)
        existing_assignments = {assignment.nguoi_xu_ly_id: assignment for assignment in document.phan_congs.all()}
    else:
        document = get_object_or_404(VanBanDi, pk=record_id)
        placeholder_assignments = list(document.phan_congs.filter(noi_dung_cd=ASSIGNMENT_PLACEHOLDER_NOTE))
        existing_assignments = {
            assignment.nguoi_xu_ly_id: assignment
            for assignment in document.phan_congs.exclude(noi_dung_cd=ASSIGNMENT_PLACEHOLDER_NOTE)
        }

    if is_truong_bo_mon(nguoi_phan_cong):
        allowed_ids = set(get_assignable_teachers_for_user(nguoi_phan_cong).values_list("pk", flat=True))
        target_ids = set(assigned_ids)
        if any(giao_vien_id not in allowed_ids for giao_vien_id in target_ids):
            return JsonResponse(
                {"success": False, "message": "To truong chi duoc phan cong cho giao vien trong to minh."},
                status=400,
            )
        has_existing_teacher = any(
            assignment.nguoi_xu_ly_id != nguoi_phan_cong.pk
            and assignment.nguoi_xu_ly.ma_to_id == nguoi_phan_cong.ma_to_id
            and not is_truong_bo_mon(assignment.nguoi_xu_ly)
            for assignment in existing_assignments.values()
        )
        if has_existing_teacher:
            return JsonResponse(
                {"success": False, "message": "Van ban nay da co giao vien trong to duoc phan cong xu ly."},
                status=400,
            )
    elif is_phong_ban_to_chuc(nguoi_phan_cong):
        allowed_ids = set(get_assignable_teachers_for_user(nguoi_phan_cong).values_list("pk", flat=True))
        target_ids = set(assigned_ids)
        if any(giao_vien_id not in allowed_ids for giao_vien_id in target_ids):
            return JsonResponse(
                {
                    "success": False,
                    "message": "Nguoi dung phong ban to chuc chi duoc phan cong cho tat ca giao vien tru ban giam hieu.",
                },
                status=400,
            )
    else:
        target_ids = set(assigned_ids)
    for giao_vien_id, assignment in list(existing_assignments.items()):
        if giao_vien_id not in target_ids:
            assignment.delete()

    assignment_instructions = {row["id"]: row["instruction"] for row in normalized_assignment_rows}
    for giao_vien_id in assigned_ids:
        noi_dung_cd = assignment_instructions[giao_vien_id]
        assignment = existing_assignments.get(giao_vien_id)
        if assignment is None:
            assignment = PhanCongXuLy(
                nguoi_xu_ly=get_object_or_404(GiaoVien, pk=giao_vien_id),
                nguoi_phan_cong=nguoi_phan_cong,
                noi_dung_cd=noi_dung_cd,
                thoi_han=thoi_han,
                trang_thai_xl=PhanCongXuLy.TrangThaiXuLy.CHO_XU_LY,
            )
            if loai == "den":
                assignment.so_vb_den = document
            else:
                assignment.so_vb_di = document
            assignment.save()
        else:
            assignment.nguoi_phan_cong = nguoi_phan_cong
            assignment.noi_dung_cd = noi_dung_cd
            assignment.thoi_han = thoi_han
            assignment.thoi_gian_phan_cong = timezone.now()
            assignment.save(update_fields=["nguoi_phan_cong", "noi_dung_cd", "thoi_han", "thoi_gian_phan_cong"])

    if loai == "den":
        document.trang_thai_vb_den = VanBanDen.TrangThai.CHO_XU_LY
        document.save(update_fields=["trang_thai_vb_den"])
    else:
        if 'placeholder_assignments' in locals():
            for assignment in placeholder_assignments:
                assignment.delete()
        document.trang_thai_vb_di = VanBanDi.TrangThai.DA_DANG_KY
        document.save(update_fields=["trang_thai_vb_di"])

    return JsonResponse({"success": True, "message": "Da phan cong xu ly thanh cong."})


@login_required
def phan_cong_xu_ly_van_ban_di_view(request, so_vb_di):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_work(giao_vien))
    if denied_response:
        return denied_response
    document = get_object_or_404(
        VanBanDi.objects.select_related("ma_loai_vb", "nguoi_tao", "nguoi_ky").prefetch_related("phan_congs"),
        pk=so_vb_di,
    )
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    if giao_vien is None or not XuLy.objects.filter(ma_vb_di=document, ma_gv=giao_vien).exclude(
        trang_thai_ky=XuLy.TRANG_THAI_DA_DUYET
    ).exists():
        return JsonResponse({"success": False, "message": "Ban khong co quyen phan cong van ban nay."}, status=403)

    assigned_ids = [value for value in request.POST.getlist("assigned_ids[]") if value]
    chi_dao = request.POST.get("chi_dao", "").strip()

    placeholder_assignments = list(document.phan_congs.filter(noi_dung_cd=ASSIGNMENT_PLACEHOLDER_NOTE))
    existing_assignments = {
        assignment.nguoi_xu_ly_id: assignment
        for assignment in document.phan_congs.exclude(noi_dung_cd=ASSIGNMENT_PLACEHOLDER_NOTE)
    }
    target_ids = set(assigned_ids)

    for giao_vien_id, assignment in list(existing_assignments.items()):
        if giao_vien_id not in target_ids:
            assignment.delete()

    for giao_vien_id in assigned_ids:
        assignment = existing_assignments.get(giao_vien_id)
        if assignment is None:
            PhanCongXuLy.objects.create(
                so_vb_di=document,
                nguoi_xu_ly=get_object_or_404(GiaoVien, pk=giao_vien_id),
                nguoi_phan_cong=giao_vien,
                noi_dung_cd=chi_dao,
                thoi_han=timezone.localdate(),
                trang_thai_xl=PhanCongXuLy.TrangThaiXuLy.CHO_XU_LY,
            )
        else:
            assignment.nguoi_phan_cong = giao_vien
            assignment.noi_dung_cd = chi_dao
            assignment.thoi_gian_phan_cong = timezone.now()
            assignment.save(update_fields=["nguoi_phan_cong", "noi_dung_cd", "thoi_gian_phan_cong"])

    for assignment in placeholder_assignments:
        assignment.delete()

    document = (
        VanBanDi.objects.select_related("ma_loai_vb", "nguoi_tao", "nguoi_ky")
        .prefetch_related("phan_congs__nguoi_xu_ly")
        .get(pk=so_vb_di)
    )
    return JsonResponse(
        {
            "success": True,
            "message": f"Da luu phan cong xu ly cho van ban {document.so_vb_di}.",
            "document": serialize_van_ban_can_duyet(document),
        }
    )


@login_required
def duyet_van_ban_di_action_view(request, so_vb_di):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_work(giao_vien))
    if denied_response:
        return denied_response
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    xu_ly = get_object_or_404(
        XuLy.objects.select_related("ma_vb_di", "ma_gv"),
        ma_vb_di_id=so_vb_di,
        ma_gv=giao_vien,
    )
    if xu_ly.trang_thai_ky == XuLy.TRANG_THAI_DA_DUYET:
        return JsonResponse({"success": False, "message": "Van ban nay da duoc ban duyet truoc do."}, status=400)

    document = xu_ly.ma_vb_di
    action = request.POST.get("action", "approve").strip()

    if action == "request_revision":
        yc_chinh_sua = request.POST.get("yc_chinh_sua", "").strip()
        if not yc_chinh_sua:
            return JsonResponse({"success": False, "message": "Vui long nhap noi dung yeu cau chinh sua."}, status=400)
        NhatKyVanBan.objects.create(
            ma_nguoi_tao=giao_vien,
            ma_vb_di=document,
            yc_chinh_sua=yc_chinh_sua,
            trang_thai=NhatKyVanBan.TrangThai.CHO_CHINH_SUA,
        )
        xu_ly.trang_thai_ky = XuLy.TRANG_THAI_CHO_CHINH_SUA
        xu_ly.save(update_fields=["trang_thai_ky"])
        document.trang_thai_vb_di = VanBanDi.TrangThai.DANG_CHINH_SUA
        document.save(update_fields=["trang_thai_vb_di"])
        return JsonResponse(
            {
                "success": True,
                "message": f"Da tra lai van ban {document.so_vb_di} de chinh sua.",
                "document": {
                    "so_vb_di": document.so_vb_di,
                    "trang_thai_vb_di": document.trang_thai_vb_di,
                    "trang_thai_hien_thi": get_van_ban_di_status_label(document.trang_thai_vb_di),
                    "status_class": get_van_ban_di_status_class(document.trang_thai_vb_di),
                },
            }
        )

    if action == "delegate":
        delegate_id = request.POST.get("delegate_id", "").strip()
        delegate_target = get_object_or_404(GiaoVien, pk=delegate_id)
        if not is_hieu_truong(giao_vien):
            return JsonResponse({"success": False, "message": "Ban khong co quyen uy quyen duyet."}, status=403)
        if not is_pho_hieu_truong(delegate_target):
            return JsonResponse({"success": False, "message": "Chi duoc uy quyen cho pho hieu truong."}, status=400)
        delegated_record, created = XuLy.objects.get_or_create(
            ma_vb_di=document,
            ma_gv=delegate_target,
            defaults={"vai_tro_ky": XuLy.VAI_TRO_KY_THAY, "trang_thai_ky": XuLy.TRANG_THAI_CHO_DUYET},
        )
        if not created:
            delegated_record.vai_tro_ky = XuLy.VAI_TRO_KY_THAY
            delegated_record.trang_thai_ky = XuLy.TRANG_THAI_CHO_DUYET
            delegated_record.thoi_gian_ky = None
            delegated_record.save(update_fields=["vai_tro_ky", "trang_thai_ky", "thoi_gian_ky"])
        xu_ly.trang_thai_ky = XuLy.TRANG_THAI_DA_UY_QUYEN
        xu_ly.thoi_gian_ky = timezone.now()
        xu_ly.save(update_fields=["trang_thai_ky", "thoi_gian_ky"])
        return JsonResponse({"success": True, "message": f"Da uy quyen duyet van ban {document.so_vb_di}."})

    if action == "forward":
        if xu_ly.vai_tro_ky != XuLy.VAI_TRO_KY_NHAY:
            return JsonResponse({"success": False, "message": "Van ban nay khong o buoc gui duyet tiep."}, status=400)
        hieu_truong = get_hieu_truong()
        if hieu_truong is None:
            return JsonResponse({"success": False, "message": "Khong tim thay hieu truong de gui duyet."}, status=400)
        xu_ly.trang_thai_ky = XuLy.TRANG_THAI_DA_DUYET
        xu_ly.thoi_gian_ky = timezone.now()
        xu_ly.save(update_fields=["trang_thai_ky", "thoi_gian_ky"])
        XuLy.objects.update_or_create(
            ma_vb_di=document,
            ma_gv=hieu_truong,
            defaults={
                "vai_tro_ky": XuLy.VAI_TRO_KY_CHINH,
                "trang_thai_ky": XuLy.TRANG_THAI_CHO_DUYET,
                "thoi_gian_ky": None,
            },
        )
        document.trang_thai_vb_di = VanBanDi.TrangThai.CHO_DUYET
        document.save(update_fields=["trang_thai_vb_di"])
        return JsonResponse({"success": True, "message": f"Da gui van ban {document.so_vb_di} len hieu truong duyet."})

    xu_ly.trang_thai_ky = XuLy.TRANG_THAI_DA_DUYET
    xu_ly.thoi_gian_ky = timezone.now()
    xu_ly.save(update_fields=["trang_thai_ky", "thoi_gian_ky"])
    document.trang_thai_vb_di = VanBanDi.TrangThai.CHO_DANG_KY
    document.save(update_fields=["trang_thai_vb_di"])

    return JsonResponse(
        {
            "success": True,
            "message": f"Da duyet van ban {document.so_vb_di}.",
            "document": {
                "so_vb_di": document.so_vb_di,
                "trang_thai_vb_di": document.trang_thai_vb_di,
                "trang_thai_hien_thi": get_van_ban_di_status_label(document.trang_thai_vb_di),
                "status_class": get_van_ban_di_status_class(document.trang_thai_vb_di),
            },
        }
    )


# Nhom view quan ly mau van ban, cap so, luan chuyen va cap nhat van ban.
@login_required
def danh_sach_mau_van_ban_view(request):
    denied_response = deny_if_no_permission(
        request,
        allowed=can_manage_templates(getattr(request.user, "ho_so_giao_vien", None)),
    )
    if denied_response:
        return denied_response
    templates = MauVanBan.objects.select_related("ma_loai_vb").order_by("-ngay_tao", "ma_mau_vb")
    context = {
        "page_title": "Danh sach mau van ban",
        "active_menu": "template_text",
        "templates": templates,
        "loai_van_ban_list": LoaiVanBan.objects.filter(ap_dung__in=[0, 2]).order_by("ten_loai_vb"),
        "template_status_choices": [choice[0] for choice in MauVanBan.TRANG_THAI_CHOICES],
    }
    return render(request, "danh_sach_mau_van_ban.html", context)


@login_required
def cap_nhat_mau_van_ban_view(request, ma_mau_vb):
    denied_response = deny_if_no_permission(
        request,
        allowed=can_manage_templates(getattr(request.user, "ho_so_giao_vien", None)),
    )
    if denied_response:
        return denied_response
    mau_van_ban = get_object_or_404(MauVanBan.objects.select_related("ma_loai_vb"), pk=ma_mau_vb)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    form = CapNhatMauVanBanForm(request.POST, request.FILES, instance=mau_van_ban)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    updated_template = form.save()
    return JsonResponse(
        {
            "success": True,
            "message": f"Da cap nhat mau van ban {updated_template.ma_mau_vb}.",
            "template": serialize_mau_van_ban(updated_template),
        }
    )


@login_required
def xoa_mau_van_ban_view(request, ma_mau_vb):
    denied_response = deny_if_no_permission(
        request,
        allowed=can_manage_templates(getattr(request.user, "ho_so_giao_vien", None)),
    )
    if denied_response:
        return denied_response
    mau_van_ban = get_object_or_404(MauVanBan, pk=ma_mau_vb)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    mau_van_ban.delete()
    return JsonResponse({"success": True, "message": f"Da xoa mau van ban {ma_mau_vb}.", "ma_mau_vb": ma_mau_vb})


@login_required
def dang_ky_van_ban_di_view(request, so_vb_di):
    denied_response = deny_if_no_permission(
        request,
        allowed=(getattr(request.user, "ho_so_giao_vien", None) is None or is_van_thu(getattr(request.user, "ho_so_giao_vien", None))),
    )
    if denied_response:
        return denied_response
    document = get_object_or_404(
        VanBanDi.objects.select_related("ma_loai_vb", "ma_muc_do", "nguoi_tao", "nguoi_ky").prefetch_related("xu_lys__ma_gv"),
        pk=so_vb_di,
    )
    normalized_status = normalize_text(document.trang_thai_vb_di)
    if is_outgoing_post_registration_status(document.trang_thai_vb_di) and normalized_status != normalize_text(VanBanDi.TrangThai.DA_DANG_KY):
        document.trang_thai_vb_di = VanBanDi.TrangThai.DA_DANG_KY
        document.save(update_fields=["trang_thai_vb_di"])
        normalized_status = normalize_text(document.trang_thai_vb_di)
    can_register = normalized_status == normalize_text(VanBanDi.TrangThai.CHO_DANG_KY)
    can_transfer = is_outgoing_post_registration_status(document.trang_thai_vb_di)

    if request.method == "POST":
        if not can_register:
            messages.error(request, "Van ban nay khong o trang thai cho dang ky.")
            return redirect("dang_ky_van_ban_di", so_vb_di=document.so_vb_di)

        form = VanBanDiDangKyForm(
            request.POST,
            request.FILES,
            instance=document,
            editable=can_register,
        )
        if form.is_valid():
            registered_document = form.save(commit=False)
            if not registered_document.ngay_ban_hanh:
                registered_document.ngay_ban_hanh = timezone.localdate()
            so_thu_tu, so_ky_hieu = generate_registration_number(VanBanDi, registered_document)
            registered_document.so_thu_tu = so_thu_tu
            registered_document.so_ky_hieu = so_ky_hieu
            registered_document.trang_thai_vb_di = VanBanDi.TrangThai.DA_DANG_KY
            registered_document.save()
            form.save_uploaded_files(registered_document)
            messages.success(request, f"Da dang ky van ban di {registered_document.so_vb_di}.")
            return redirect("dang_ky_van_ban_di", so_vb_di=registered_document.so_vb_di)
    else:
        form = VanBanDiDangKyForm(instance=document, editable=can_register)

    context = {
        "page_title": "Dang ky van ban di",
        "active_menu": "outgoing_text",
        "document": document,
        "form": form,
        "can_register": can_register,
        "can_transfer": can_transfer,
        "can_external_publish": can_transfer and not document.da_phat_hanh_ben_ngoai,
        "can_internal_publish": can_transfer,
        "can_send_assignment": can_transfer and not document.da_gui_phan_cong,
        "is_new_registration": False,
        "show_draft_file": True,
        "recipient_list": NoiNhan.objects.order_by("ten_noi_nhan"),
        "registration_page_url": reverse("dang_ky_van_ban_di", kwargs={"so_vb_di": document.so_vb_di}),
    }
    document.nguoi_ky_hien_thi = get_document_signers_display(document)
    return render(request, "van_ban_di_form.html", context)


@login_required
def cap_so_van_ban_di_view(request, so_vb_di):
    denied_response = deny_if_no_permission(
        request,
        allowed=(getattr(request.user, "ho_so_giao_vien", None) is None or is_van_thu(getattr(request.user, "ho_so_giao_vien", None))),
    )
    if denied_response:
        return denied_response
    document = get_object_or_404(VanBanDi.objects.select_related("ma_loai_vb"), pk=so_vb_di)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    if normalize_text(document.trang_thai_vb_di) != normalize_text(VanBanDi.TrangThai.CHO_DANG_KY):
        return JsonResponse({"success": False, "message": "Chi cap so cho van ban dang cho dang ky."}, status=400)

    try:
        so_ky_hieu = generate_so_ky_hieu(VanBanDi, document)
    except ValueError as exc:
        return JsonResponse({"success": False, "message": str(exc)}, status=400)

    return JsonResponse({"success": True, "so_ky_hieu": so_ky_hieu})


@login_required
def luan_chuyen_van_ban_di_view(request, so_vb_di):
    denied_response = deny_if_no_permission(
        request,
        allowed=(getattr(request.user, "ho_so_giao_vien", None) is None or is_van_thu(getattr(request.user, "ho_so_giao_vien", None))),
    )
    if denied_response:
        return denied_response
    document = get_object_or_404(VanBanDi, pk=so_vb_di)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    if not is_outgoing_post_registration_status(document.trang_thai_vb_di):
        return JsonResponse({"success": False, "message": "Chi gui phan cong cho van ban da dang ky."}, status=400)

    signer_records = list(document.xu_lys.select_related("ma_gv").order_by("ma_xu_ly"))
    signer_ids = []
    for item in signer_records:
        if item.ma_gv_id not in signer_ids:
            signer_ids.append(item.ma_gv_id)
    if not signer_ids and document.nguoi_ky_id:
        signer_ids.append(document.nguoi_ky_id)
    if not signer_ids:
        return JsonResponse({"success": False, "message": "Van ban chua co nguoi ky de gui phan cong."}, status=400)

    for signer_id in signer_ids:
        PhanCongXuLy.objects.get_or_create(
            so_vb_di=document,
            nguoi_xu_ly_id=signer_id,
            defaults={
                "nguoi_phan_cong": getattr(request.user, "ho_so_giao_vien", None),
                "noi_dung_cd": ASSIGNMENT_PLACEHOLDER_NOTE,
                "thoi_han": timezone.localdate(),
                "trang_thai_xl": PhanCongXuLy.TrangThaiXuLy.CHO_XU_LY,
            },
        )

    document.da_gui_phan_cong = True
    document.save(update_fields=["da_gui_phan_cong"])

    return JsonResponse(
        {
            "success": True,
            "message": f"Da gui phan cong van ban {document.so_vb_di}.",
            "document": {
                "so_vb_di": document.so_vb_di,
                "trang_thai_vb_di": document.trang_thai_vb_di,
                "trang_thai_hien_thi": get_van_ban_di_status_label(document.trang_thai_vb_di),
                "status_class": get_van_ban_di_status_class(document.trang_thai_vb_di),
            },
        }
    )


@login_required
def ban_hanh_noi_bo_van_ban_den_view(request, so_vb_den):
    denied_response = deny_if_no_permission(
        request,
        allowed=(getattr(request.user, "ho_so_giao_vien", None) is None or is_van_thu(getattr(request.user, "ho_so_giao_vien", None))),
    )
    if denied_response:
        return denied_response
    document = get_object_or_404(VanBanDen.objects.select_related("ma_loai_vb", "ma_muc_do"), pk=so_vb_den)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    document.da_ban_hanh_noi_bo = not document.da_ban_hanh_noi_bo
    message = (
        f"Da ban hanh noi bo van ban den {document.so_vb_den}."
        if document.da_ban_hanh_noi_bo
        else f"Da ngung ban hanh van ban den {document.so_vb_den}."
    )
    document.save(update_fields=["da_ban_hanh_noi_bo"])
    return JsonResponse(
        {
            "success": True,
            "message": message,
            "document": serialize_van_ban_den_list_document(document),
        }
    )


@login_required
def cap_nhat_van_ban_den_view(request, so_vb_den):
    denied_response = deny_if_no_permission(
        request,
        allowed=(getattr(request.user, "ho_so_giao_vien", None) is None or is_van_thu(getattr(request.user, "ho_so_giao_vien", None))),
    )
    if denied_response:
        return denied_response
    van_ban_den = get_object_or_404(VanBanDen, pk=so_vb_den)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    normalized_status = normalize_text(van_ban_den.trang_thai_vb_den)
    has_attachment_changes = bool(
        request.FILES.getlist("tep_dinh_kem_uploads")
        or request.POST.get("tep_dinh_kem_xoa_ids", "").strip()
    )
    if normalized_status in {
        normalize_text(VanBanDen.TrangThai.CHO_XU_LY),
        normalize_text(VanBanDen.TrangThai.DA_HOAN_THANH),
        normalize_text(VanBanDen.TrangThai.DA_BAN_HANH),
    } and not has_attachment_changes:
        return JsonResponse(
            {"success": False, "message": "Van ban den da duoc phan cong thi khong con duoc chinh sua."},
            status=400,
        )

    form = VanBanDenUpdateForm(
        request.POST,
        copy_request_files_with_aliases(request, {"file_van_ban_uploads": "file_van_ban"}),
        instance=van_ban_den,
    )
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    updated_document = form.save()
    updated_document = VanBanDen.objects.select_related("ma_loai_vb", "ma_muc_do").get(pk=updated_document.pk)
    return JsonResponse(
        {
            "success": True,
            "message": f"Da cap nhat van ban den {updated_document.so_vb_den}.",
            "document": serialize_van_ban_den_list_document(updated_document),
        }
    )


@login_required
def cap_nhat_van_ban_di_view(request, so_vb_di):
    denied_response = deny_if_no_permission(
        request,
        allowed=(getattr(request.user, "ho_so_giao_vien", None) is None or is_van_thu(getattr(request.user, "ho_so_giao_vien", None))),
    )
    if denied_response:
        return denied_response
    van_ban_di = get_object_or_404(VanBanDi, pk=so_vb_di)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    form = VanBanDiUpdateForm(
        request.POST,
        copy_request_files_with_aliases(
            request,
            {
                "ban_du_thao_uploads": "ban_du_thao",
                "ban_chinh_thuc_uploads": "ban_chinh_thuc",
            },
        ),
        instance=van_ban_di,
    )
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    updated_document = form.save()
    draft_attachments = serialize_outgoing_attachments(updated_document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
    official_attachments = serialize_outgoing_attachments(updated_document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
    return JsonResponse(
        {
            "success": True,
            "message": f"Da cap nhat van ban di {updated_document.so_vb_di}.",
            "document": {
                "so_vb_di": updated_document.so_vb_di,
                "ngay_ban_hanh": (
                    updated_document.ngay_ban_hanh.strftime("%d/%m/%Y") if updated_document.ngay_ban_hanh else ""
                ),
                "ngay_ky": updated_document.ngay_ky.strftime("%d/%m/%Y") if updated_document.ngay_ky else "",
                "so_ky_hieu": updated_document.so_ky_hieu,
                "trich_yeu": updated_document.trich_yeu,
                "noi_nhan": updated_document.noi_nhan,
                "trang_thai_vb_di": updated_document.trang_thai_vb_di,
                "trang_thai_hien_thi": get_van_ban_di_status_label(updated_document.trang_thai_vb_di),
                "status_class": get_van_ban_di_status_class(updated_document.trang_thai_vb_di),
                "ten_loai_vb": updated_document.ma_loai_vb.ten_loai_vb,
                "muc_do": updated_document.ma_muc_do.muc_do,
                "nguoi_tao": updated_document.nguoi_tao.ho_ten,
                "nguoi_ky": updated_document.nguoi_ky.ho_ten,
                "nguoi_ky_display": get_document_signers_display(updated_document),
                "nguoi_ky_id": updated_document.nguoi_ky_id,
                "ban_du_thao_name": build_primary_file_payload(updated_document.ban_du_thao)["name"],
                "ban_du_thao_url": build_primary_file_payload(updated_document.ban_du_thao)["url"],
                "ban_du_thao_attachments_json": serialize_attachment_json(
                    serialize_outgoing_supporting_attachments(updated_document, TepDinhKemVanBanDi.LoaiTep.DU_THAO)
                ),
                "ban_chinh_thuc_name": build_primary_file_payload(updated_document.ban_chinh_thuc)["name"],
                "ban_chinh_thuc_url": build_primary_file_payload(updated_document.ban_chinh_thuc)["url"],
                "ban_chinh_thuc_attachments_json": serialize_attachment_json(
                    serialize_outgoing_supporting_attachments(updated_document, TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)
                ),
            },
        }
    )


@login_required
def phat_hanh_ben_ngoai_van_ban_di_view(request, so_vb_di):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(
        request,
        allowed=(giao_vien is None or is_van_thu(giao_vien)),
    )
    if denied_response:
        return denied_response
    document = get_object_or_404(VanBanDi, pk=so_vb_di)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    if not is_outgoing_post_registration_status(document.trang_thai_vb_di):
        return JsonResponse(
            {"success": False, "message": "Chi phat hanh ben ngoai cho van ban da dang ky."},
            status=400,
        )

    recipient_ids = request.POST.getlist("noi_nhan_ids[]") or request.POST.getlist("noi_nhan_ids")
    recipient_ids = [item.strip() for item in recipient_ids if item.strip()]
    if not recipient_ids:
        return JsonResponse({"success": False, "message": "Vui long chon it nhat mot noi nhan."}, status=400)
    ghi_chu = request.POST.get("ghi_chu", "").strip()

    recipients = list(NoiNhan.objects.filter(pk__in=recipient_ids).order_by("ten_noi_nhan"))
    if len(recipients) != len(set(recipient_ids)):
        return JsonResponse({"success": False, "message": "Danh sach noi nhan khong hop le."}, status=400)

    created_records = []
    for recipient in recipients:
        record, created = LuanChuyenBenNgoai.objects.get_or_create(
            ma_vb_di=document,
            ma_noi_nhan=recipient,
            defaults={
                "nguoi_thuc_hien": giao_vien,
                "trang_thai_gui": LuanChuyenBenNgoai.TrangThaiGui.CHO_GUI,
                "ghi_chu": ghi_chu,
                "thoi_gian_gui": None,
            },
        )
        if created:
            created_records.append(record)

    if not created_records:
        return JsonResponse(
            {"success": False, "message": "Van ban nay da duoc phat hanh den cac noi nhan da chon."},
            status=400,
        )

    document.da_phat_hanh_ben_ngoai = True
    document.save(update_fields=["da_phat_hanh_ben_ngoai"])

    return JsonResponse(
        {
            "success": True,
            "message": f"Da tao {len(created_records)} ban ghi phat hanh ben ngoai cho van ban {document.so_vb_di}.",
            "records": [serialize_external_dispatch_record(record) for record in created_records],
        }
    )


@login_required
def cap_nhat_luan_chuyen_ben_ngoai_view(request, ma_luan_chuyen):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(
        request,
        allowed=(giao_vien is None or is_van_thu(giao_vien)),
    )
    if denied_response:
        return JsonResponse({"success": False, "message": "Ban khong co quyen cap nhat phat hanh ben ngoai."}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    record = get_object_or_404(
        LuanChuyenBenNgoai.objects.select_related("ma_vb_di", "ma_vb_di__ma_loai_vb", "ma_noi_nhan", "nguoi_thuc_hien"),
        pk=ma_luan_chuyen,
    )
    if record.trang_thai_gui == LuanChuyenBenNgoai.TrangThaiGui.DA_GUI:
        return JsonResponse({"success": False, "message": "Ban ghi nay da duoc danh dau da gui."}, status=400)

    ma_noi_nhan = request.POST.get("ma_noi_nhan", "").strip()
    if not ma_noi_nhan:
        return JsonResponse({"success": False, "message": "Vui long chon noi nhan."}, status=400)
    recipient = get_object_or_404(NoiNhan, pk=ma_noi_nhan)
    duplicate_record = (
        LuanChuyenBenNgoai.objects.exclude(pk=record.pk)
        .filter(ma_vb_di=record.ma_vb_di, ma_noi_nhan=recipient)
        .exists()
    )
    if duplicate_record:
        return JsonResponse({"success": False, "message": "Van ban nay da co ban ghi cho noi nhan da chon."}, status=400)

    record.ma_noi_nhan = recipient
    record.ghi_chu = request.POST.get("ghi_chu", "").strip()
    record.save(update_fields=["ma_noi_nhan", "ghi_chu"])
    record = LuanChuyenBenNgoai.objects.select_related("ma_vb_di", "ma_vb_di__ma_loai_vb", "ma_noi_nhan", "nguoi_thuc_hien").get(pk=record.pk)
    return JsonResponse(
        {
            "success": True,
            "message": "Da cap nhat thong tin phat hanh ben ngoai.",
            "record": serialize_external_dispatch_record(record),
        }
    )


@login_required
def danh_dau_da_gui_luan_chuyen_ben_ngoai_view(request, ma_luan_chuyen):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(
        request,
        allowed=(giao_vien is None or is_van_thu(giao_vien)),
    )
    if denied_response:
        return JsonResponse({"success": False, "message": "Ban khong co quyen cap nhat phat hanh ben ngoai."}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    record = get_object_or_404(
        LuanChuyenBenNgoai.objects.select_related("ma_vb_di", "ma_vb_di__ma_loai_vb", "ma_noi_nhan", "nguoi_thuc_hien"),
        pk=ma_luan_chuyen,
    )
    if record.trang_thai_gui == LuanChuyenBenNgoai.TrangThaiGui.DA_GUI:
        return JsonResponse({"success": False, "message": "Ban ghi nay da duoc danh dau da gui."}, status=400)

    record.trang_thai_gui = LuanChuyenBenNgoai.TrangThaiGui.DA_GUI
    record.thoi_gian_gui = timezone.now()
    record.save(update_fields=["trang_thai_gui", "thoi_gian_gui"])
    record = LuanChuyenBenNgoai.objects.select_related("ma_vb_di", "ma_vb_di__ma_loai_vb", "ma_noi_nhan", "nguoi_thuc_hien").get(pk=record.pk)
    return JsonResponse(
        {
            "success": True,
            "message": "Da danh dau ban ghi la da gui.",
            "record": serialize_external_dispatch_record(record),
        }
    )


@login_required
def ban_hanh_noi_bo_van_ban_di_view(request, so_vb_di):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(
        request,
        allowed=(giao_vien is None or is_van_thu(giao_vien)),
    )
    if denied_response:
        return denied_response
    document = get_object_or_404(VanBanDi, pk=so_vb_di)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)
    if not is_outgoing_post_registration_status(document.trang_thai_vb_di):
        return JsonResponse({"success": False, "message": "Chi ban hanh noi bo cho van ban da dang ky."}, status=400)

    document.da_ban_hanh_noi_bo = not document.da_ban_hanh_noi_bo
    document.save(update_fields=["da_ban_hanh_noi_bo"])
    return JsonResponse(
        {
            "success": True,
            "message": (
                f"Da ban hanh noi bo van ban {document.so_vb_di}."
                if document.da_ban_hanh_noi_bo
                else f"Da ngung ban hanh van ban {document.so_vb_di}."
            ),
            "document": {
                "so_vb_di": document.so_vb_di,
                "da_ban_hanh_noi_bo": document.da_ban_hanh_noi_bo,
            },
        }
    )


@login_required
def danh_sach_nguoi_dung_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return denied_response

    giao_vien_list = (
        GiaoVien.objects.select_related("ma_to", "user")
        .prefetch_related("user__groups")
        .order_by("ho_ten", "ma_gv")
    )
    context = {
        "page_title": "Quan ly tai khoan",
        "active_menu": "account_management",
        "giao_vien_list": giao_vien_list,
        "to_chuyen_mon_list": ToChuyenMon.objects.order_by("ten_to"),
        "account_status_choices": [
            GiaoVien.TrangThaiTaiKhoan.HOAT_DONG,
            GiaoVien.TrangThaiTaiKhoan.NGUNG_HOAT_DONG,
        ],
        "is_account_user_list": True,
    }
    return render(request, "quan_ly_tai_khoan_danh_sach.html", context)


@login_required
def danh_sach_noi_nhan_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return denied_response

    recipient_list = NoiNhan.objects.order_by("ten_noi_nhan", "ma_noi_nhan")
    context = {
        "page_title": "Quan ly noi nhan",
        "active_menu": "recipient_management",
        "recipient_list": recipient_list,
        "is_recipient_list": True,
    }
    return render(request, "quan_ly_noi_nhan.html", context)


@login_required
def them_noi_nhan_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return JsonResponse({"success": False, "message": "Ban khong co quyen them noi nhan."}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    ten_noi_nhan = request.POST.get("ten_noi_nhan", "").strip()
    dia_chi = request.POST.get("dia_chi", "").strip()
    so_dien_thoai = request.POST.get("so_dien_thoai", "").strip()
    gmail = request.POST.get("gmail", "").strip()
    thong_tin_khac = request.POST.get("thong_tin_khac", "").strip()

    if not ten_noi_nhan:
        return JsonResponse({"success": False, "message": "Vui long nhap ten noi nhan."}, status=400)
    if NoiNhan.objects.filter(ten_noi_nhan__iexact=ten_noi_nhan).exists():
        return JsonResponse({"success": False, "message": "Ten noi nhan da ton tai."}, status=400)

    recipient = NoiNhan.objects.create(
        ten_noi_nhan=ten_noi_nhan,
        dia_chi=dia_chi,
        so_dien_thoai=so_dien_thoai,
        gmail=gmail,
        thong_tin_khac=thong_tin_khac,
    )
    return JsonResponse(
        {
            "success": True,
            "message": f"Da them noi nhan {recipient.ten_noi_nhan}.",
            "recipient": serialize_recipient(recipient),
            "row_html": serialize_recipient_row_html(request, recipient),
        }
    )


@login_required
def cap_nhat_noi_nhan_view(request, ma_noi_nhan):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return JsonResponse({"success": False, "message": "Ban khong co quyen cap nhat noi nhan."}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    recipient = get_object_or_404(NoiNhan, pk=ma_noi_nhan)
    ten_noi_nhan = request.POST.get("ten_noi_nhan", "").strip()
    dia_chi = request.POST.get("dia_chi", "").strip()
    so_dien_thoai = request.POST.get("so_dien_thoai", "").strip()
    gmail = request.POST.get("gmail", "").strip()
    thong_tin_khac = request.POST.get("thong_tin_khac", "").strip()

    if not ten_noi_nhan:
        return JsonResponse({"success": False, "message": "Vui long nhap ten noi nhan."}, status=400)
    if NoiNhan.objects.exclude(pk=recipient.pk).filter(ten_noi_nhan__iexact=ten_noi_nhan).exists():
        return JsonResponse({"success": False, "message": "Ten noi nhan da ton tai."}, status=400)

    recipient.ten_noi_nhan = ten_noi_nhan
    recipient.dia_chi = dia_chi
    recipient.so_dien_thoai = so_dien_thoai
    recipient.gmail = gmail
    recipient.thong_tin_khac = thong_tin_khac
    recipient.save()

    return JsonResponse(
        {
            "success": True,
            "message": f"Da cap nhat noi nhan {recipient.ten_noi_nhan}.",
            "recipient": serialize_recipient(recipient),
        }
    )


@login_required
def them_giao_vien_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return JsonResponse({"success": False, "message": "Ban khong co quyen them giao vien."}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    form = ThemGiaoVienForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    giao_vien_moi = form.save()
    giao_vien_moi = (
        GiaoVien.objects.select_related("ma_to", "user")
        .prefetch_related("user__groups")
        .get(pk=giao_vien_moi.pk)
    )
    return JsonResponse(
        {
            "success": True,
            "message": f"Da them giao vien {giao_vien_moi.ho_ten}.",
            "teacher": serialize_teacher_account(giao_vien_moi),
            "row_html": serialize_teacher_row_html(request, giao_vien_moi),
        }
    )


@login_required
def cap_nhat_ho_so_ca_nhan_view(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    if giao_vien is None:
        return JsonResponse({"success": False, "message": "Tai khoan hien tai chua co ho so giao vien."}, status=400)

    form = HoSoCaNhanForm(request.POST, instance=giao_vien)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    giao_vien = form.save()
    giao_vien = (
        GiaoVien.objects.select_related("ma_to", "user")
        .prefetch_related("user__groups")
        .get(pk=giao_vien.pk)
    )
    return JsonResponse(
        {
            "success": True,
            "message": "Da cap nhat thong tin ca nhan.",
            "profile": serialize_personal_profile(giao_vien),
        }
    )


@login_required
def doi_mat_khau_ca_nhan_view(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    form = DoiMatKhauCaNhanForm(request.POST, user=request.user)
    if not form.is_valid():
        errors = form.errors.get("__all__") or sum(form.errors.values(), [])
        return JsonResponse({"success": False, "message": " ".join(errors)}, status=400)

    request.user.set_password(form.cleaned_data["mat_khau_moi"])
    request.user.save(update_fields=["password"])
    update_session_auth_hash(request, request.user)
    return JsonResponse({"success": True, "message": "Da doi mat khau thanh cong."})


@login_required
def cap_nhat_tai_khoan_giao_vien_view(request, ma_gv):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return JsonResponse({"success": False, "message": "Ban khong co quyen cap nhat tai khoan."}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    giao_vien_duoc_sua = get_object_or_404(GiaoVien.objects.select_related("ma_to", "user"), pk=ma_gv)
    form = GiaoVienTaiKhoanForm(request.POST, instance=giao_vien_duoc_sua)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    form.save()
    giao_vien_duoc_sua = (
        GiaoVien.objects.select_related("ma_to", "user")
        .prefetch_related("user__groups")
        .get(pk=ma_gv)
    )
    return JsonResponse(
        {
            "success": True,
            "message": f"Da cap nhat tai khoan giao vien {giao_vien_duoc_sua.ho_ten}.",
            "teacher": serialize_teacher_account(giao_vien_duoc_sua),
        }
    )


@login_required
def reset_mat_khau_giao_vien_view(request, ma_gv):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return JsonResponse({"success": False, "message": "Ban khong co quyen reset mat khau."}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    mat_khau_moi = request.POST.get("password", "")
    nhap_lai_mat_khau = request.POST.get("confirm_password", "")
    if not mat_khau_moi:
        return JsonResponse({"success": False, "message": "Vui long nhap mat khau moi."}, status=400)
    if mat_khau_moi != nhap_lai_mat_khau:
        return JsonResponse({"success": False, "message": "Mat khau nhap lai khong khop."}, status=400)

    giao_vien_duoc_reset = get_object_or_404(GiaoVien.objects.select_related("user"), pk=ma_gv)
    giao_vien_duoc_reset.ensure_user_account()
    giao_vien_duoc_reset.user.set_password(mat_khau_moi)
    giao_vien_duoc_reset.user.save(update_fields=["password"])

    return JsonResponse(
        {
            "success": True,
            "message": f"Da reset mat khau cho giao vien {giao_vien_duoc_reset.ho_ten}.",
        }
    )


@login_required
def phan_quyen_nguoi_dung_view(request):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return denied_response

    giao_vien_list = (
        GiaoVien.objects.select_related("ma_to", "user")
        .prefetch_related("user__groups")
        .order_by("ho_ten", "ma_gv")
    )
    context = {
        "page_title": "Phan quyen nguoi dung",
        "active_menu": "account_management",
        "giao_vien_list": giao_vien_list,
        "group_list": Group.objects.order_by("name"),
        "is_account_permission_list": True,
    }
    return render(request, "phan_quyen_nguoi_dung.html", context)


@login_required
def cap_nhat_phan_quyen_nguoi_dung_view(request, ma_gv):
    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    denied_response = deny_if_no_permission(request, allowed=can_manage_accounts(giao_vien))
    if denied_response:
        return JsonResponse({"success": False, "message": "Ban khong co quyen phan quyen nguoi dung."}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Phuong thuc khong hop le."}, status=405)

    giao_vien_duoc_phan_quyen = get_object_or_404(GiaoVien.objects.select_related("user"), pk=ma_gv)
    form = PhanQuyenNguoiDungForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"success": False, "errors": form.errors}, status=400)

    giao_vien_duoc_phan_quyen.ensure_user_account()
    giao_vien_duoc_phan_quyen.user.groups.set(form.cleaned_data["nhom_quyen"])
    giao_vien_duoc_phan_quyen = (
        GiaoVien.objects.select_related("ma_to", "user")
        .prefetch_related("user__groups")
        .get(pk=ma_gv)
    )
    return JsonResponse(
        {
            "success": True,
            "message": f"Da cap nhat phan quyen cho giao vien {giao_vien_duoc_phan_quyen.ho_ten}.",
            "teacher": serialize_teacher_account(giao_vien_duoc_phan_quyen),
        }
    )


# Nhom view ket thuc phien dang nhap va chuyen huong dang nhap admin.
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")


def admin_login_redirect_view(request):
    next_url = request.GET.get("next") or "/admin/"
    query_string = urlencode({"next": next_url})
    return redirect(f"/dang-nhap/?{query_string}")
