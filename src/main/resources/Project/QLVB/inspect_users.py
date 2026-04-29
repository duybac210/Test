import sys
sys.stdout.reconfigure(encoding='utf-8')
from django.contrib.auth.models import User

for username in ['TT001', 'GV00000001', 'GV00000014', 'GV000006']:
    u = User.objects.get(username=username)
    gv = getattr(u, 'ho_so_giao_vien', None)
    groups = list(u.groups.values_list('name', flat=True))
    chuc_vu = gv.chuc_vu if gv else 'N/A'

    # Tính quyền theo context_processor logic
    from QLVBDH.context_processors import has_group, has_role, is_limited_bgh_user, has_any_group
    is_van_thu = has_group(gv, "Van thu") or has_role(gv, "Van thu")
    is_bgh = is_limited_bgh_user(gv)
    is_truong_bo_mon = (
        has_group(gv, "To chuyen mon") or has_group(gv, "To truong") or
        has_group(gv, "To truong chuyen mon") or has_role(gv, "To truong")
    )
    is_to_chuc = has_any_group(gv, "Phong/ ban/ to chuc", "Phong/ban / to chuc", "Nguoi dung to chuc trong truong")
    is_gv = gv is not None and not is_bgh and not is_van_thu and not is_to_chuc and not is_truong_bo_mon

    can_duyet = is_bgh or is_truong_bo_mon or is_to_chuc
    can_tao   = is_van_thu or is_truong_bo_mon or is_to_chuc or is_gv

    print(f"{username} | chuc_vu={chuc_vu} | groups={groups}")
    print(f"  -> is_bgh={is_bgh} | is_truong_bo_mon={is_truong_bo_mon} | is_gv={is_gv}")
    print(f"  -> can_duyet_vanban={can_duyet} | can_tao_vanban={can_tao}")
    print()
