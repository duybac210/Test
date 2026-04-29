import unicodedata


def normalize_text(value):
    normalized = unicodedata.normalize("NFD", value or "")
    without_marks = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    compact = " ".join(without_marks.strip().lower().split())
    return compact.replace(" /", "/").replace("/ ", "/")


def has_role(giao_vien, role_name):
    if giao_vien is None:
        return False
    return normalize_text(giao_vien.chuc_vu) == normalize_text(role_name)


def has_group(giao_vien, group_name):
    if giao_vien is None or not giao_vien.user_id:
        return False
    target = normalize_text(group_name)
    return any(target == normalize_text(name) for name in giao_vien.user.groups.values_list("name", flat=True))


def has_any_group(giao_vien, *group_names):
    return any(has_group(giao_vien, group_name) for group_name in group_names)


def is_limited_bgh_user(giao_vien):
    return has_group(giao_vien, "Ban giam hieu")


def user_profile_display(request):
    if not request.user.is_authenticated:
        return {}

    giao_vien = getattr(request.user, "ho_so_giao_vien", None)
    if giao_vien is None:
        return {
            "display_ho_ten": request.user.get_full_name() or request.user.get_username(),
            "display_chuc_vu": "Quan tri",
            "personal_profile": None,
            "ui_permissions": {},
        }

    is_van_thu = has_group(giao_vien, "Van thu") or has_role(giao_vien, "Van thu")
    is_ban_giam_hieu = is_limited_bgh_user(giao_vien)
    is_truong_bo_mon = (
        has_group(giao_vien, "To chuyen mon")
        or has_group(giao_vien, "To truong")
        or has_group(giao_vien, "To truong chuyen mon")
        or has_role(giao_vien, "To truong")
    )
    is_to_chuc = has_any_group(
        giao_vien,
        "Phong/ ban/ to chuc",
        "Phong/ban / to chuc",
        "Nguoi dung to chuc trong truong",
    )

    is_giao_vien = giao_vien is not None and not is_ban_giam_hieu and not is_van_thu and not is_to_chuc and not is_truong_bo_mon

    ui_permissions = {
        "can_follow_condition": is_van_thu,
        "can_view_incoming_outgoing": is_van_thu or is_ban_giam_hieu,
        "can_create_document": is_van_thu or is_truong_bo_mon or is_to_chuc or is_giao_vien,
        "can_manage_work": is_ban_giam_hieu or is_truong_bo_mon or is_to_chuc,
        "can_personal_work": is_van_thu or is_truong_bo_mon or is_to_chuc or is_giao_vien,
        "can_document_list": is_van_thu or is_ban_giam_hieu or is_truong_bo_mon or is_to_chuc or is_giao_vien,
        "can_document_list_created": is_van_thu or is_ban_giam_hieu or is_truong_bo_mon or is_to_chuc or is_giao_vien,
        "can_template_text": is_van_thu,
        "can_manage_accounts": is_van_thu,
        "can_manage_recipients": is_van_thu,
    }

    return {
        "display_ho_ten": giao_vien.ho_ten,
        "display_chuc_vu": giao_vien.ten_vai_tro_hien_thi or "Nguoi dung he thong",
        "personal_profile": {
            "ma_gv": giao_vien.ma_gv,
            "ho_ten": giao_vien.ho_ten,
            "lan_cuoi_dang_nhap": (
                giao_vien.user.last_login.astimezone().strftime("%d/%m/%Y %H:%M")
                if giao_vien.user_id and giao_vien.user.last_login
                else "Chua dang nhap"
            ),
            "nhom_quyen_display": giao_vien.ten_nhom_quyen_hien_thi or "Chua phan quyen",
        },
        "ui_permissions": ui_permissions,
    }
