import json
import tempfile
from pathlib import Path

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import GiaoVien, LoaiVanBan, LuanChuyenBenNgoai, MauVanBan, MucDoUuTien, NhatKyVanBan, NoiNhan, PhanCongXuLy, TepDinhKemVanBanDen, TepDinhKemVanBanDi, ToChuyenMon, VanBanDen, VanBanDi, XuLy
from .views import get_document_signers_display


TEST_MEDIA_ROOT = Path(tempfile.mkdtemp())


class _VaiTroStub:
    def __init__(self, ten_vai_tro, nhom_quyen):
        self.ten_vai_tro = ten_vai_tro
        self.nhom_quyen = nhom_quyen


class _VaiTroManagerStub:
    @staticmethod
    def create(*, ten_vai_tro, nhom_quyen):
        return _VaiTroStub(ten_vai_tro=ten_vai_tro, nhom_quyen=nhom_quyen)


class VaiTro:
    objects = _VaiTroManagerStub()


def set_giao_vien_roles(giao_vien, *vai_tros):
    giao_vien.chuc_vu = ", ".join(vai_tro.ten_vai_tro for vai_tro in vai_tros)
    giao_vien.save(update_fields=["chuc_vu"])
    if giao_vien.user_id:
        giao_vien.user.groups.set([vai_tro.nhom_quyen for vai_tro in vai_tros])


class LoaiVanBanTests(TestCase):
    def test_ap_dung_mac_dinh_la_ca_hai(self):
        loai_van_ban = LoaiVanBan.objects.create(ten_loai_vb="Thong bao", ten_viet_tat="TB")

        self.assertEqual(loai_van_ban.ap_dung, 2)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class MauVanBanViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret123")
        self.client.force_login(self.user)
        self.loai_van_ban = LoaiVanBan.objects.create(ten_loai_vb="To trinh", ten_viet_tat="TT")

    def test_them_mau_van_ban_view_creates_template(self):
        response = self.client.post(
            reverse("them_mau_van_ban"),
            data={
                "ngay_tao": "2026-03-29",
                "ten_mau": "To trinh cong tac can bo",
                "ma_loai_vb": self.loai_van_ban.pk,
                "trang_thai": MauVanBan.TRANG_THAI_DANG_SU_DUNG,
                "muc_dich": "Phuc vu trinh duyet noi bo",
                "file_mau": SimpleUploadedFile(
                    "mau-to-trinh.pdf",
                    b"%PDF-1.4 mau van ban",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertRedirects(response, reverse("them_mau_van_ban"))
        mau_van_ban = MauVanBan.objects.get()
        self.assertEqual(mau_van_ban.ten_mau, "To trinh cong tac can bo")
        self.assertEqual(mau_van_ban.muc_dich, "Phuc vu trinh duyet noi bo")
        self.assertEqual(mau_van_ban.ma_loai_vb, self.loai_van_ban)
        self.assertEqual(mau_van_ban.trang_thai, MauVanBan.TRANG_THAI_DANG_SU_DUNG)
        self.assertTrue(mau_van_ban.file_mau.name.endswith("mau-to-trinh.pdf"))

    def test_danh_sach_mau_van_ban_view_returns_templates(self):
        MauVanBan.objects.create(
            ngay_tao="2026-03-29",
            ten_mau="Mau thong bao",
            ma_loai_vb=self.loai_van_ban,
            trang_thai=MauVanBan.TRANG_THAI_DANG_SU_DUNG,
            muc_dich="Phuc vu quan ly noi bo",
            file_mau=SimpleUploadedFile("mau-thong-bao.pdf", b"%PDF-1.4 template", content_type="application/pdf"),
        )

        response = self.client.get(reverse("danh_sach_mau_van_ban"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mau thong bao")

    def test_cap_nhat_mau_van_ban_view_updates_template(self):
        mau_van_ban = MauVanBan.objects.create(
            ngay_tao="2026-03-29",
            ten_mau="Mau cu",
            ma_loai_vb=self.loai_van_ban,
            trang_thai=MauVanBan.TRANG_THAI_DANG_SU_DUNG,
            muc_dich="Noi dung cu",
            file_mau=SimpleUploadedFile("mau-cu.pdf", b"%PDF-1.4 old", content_type="application/pdf"),
        )
        loai_moi = LoaiVanBan.objects.create(ten_loai_vb="Thong bao", ten_viet_tat="TB", ap_dung=0)

        response = self.client.post(
            reverse("cap_nhat_mau_van_ban", args=[mau_van_ban.ma_mau_vb]),
            data={
                "ngay_tao": "2026-03-30",
                "ten_mau": "Mau moi",
                "ma_loai_vb": loai_moi.pk,
                "trang_thai": MauVanBan.TRANG_THAI_DUNG_SU_DUNG,
                "muc_dich": "Noi dung moi",
                "file_mau": SimpleUploadedFile("mau-moi.pdf", b"%PDF-1.4 new", content_type="application/pdf"),
            },
        )

        self.assertEqual(response.status_code, 200)
        mau_van_ban.refresh_from_db()
        self.assertEqual(mau_van_ban.ten_mau, "Mau moi")
        self.assertEqual(mau_van_ban.ma_loai_vb, loai_moi)
        self.assertEqual(mau_van_ban.trang_thai, MauVanBan.TRANG_THAI_DUNG_SU_DUNG)
        self.assertTrue(mau_van_ban.file_mau.name.endswith("mau-moi.pdf"))
        self.assertEqual(response.json()["template"]["ten_mau"], "Mau moi")

    def test_xoa_mau_van_ban_view_deletes_template(self):
        mau_van_ban = MauVanBan.objects.create(
            ngay_tao="2026-03-29",
            ten_mau="Mau xoa",
            ma_loai_vb=self.loai_van_ban,
            trang_thai=MauVanBan.TRANG_THAI_DANG_SU_DUNG,
            muc_dich="Se bi xoa",
            file_mau=SimpleUploadedFile("mau-xoa.pdf", b"%PDF-1.4 delete", content_type="application/pdf"),
        )

        response = self.client.post(reverse("xoa_mau_van_ban", args=[mau_van_ban.ma_mau_vb]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(MauVanBan.objects.filter(pk=mau_van_ban.pk).exists())


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class DangKyVanBanDenViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret123")
        self.client.force_login(self.user)
        self.loai_van_ban = LoaiVanBan.objects.create(ten_loai_vb="Cong van", ten_viet_tat="CV")
        self.muc_do = MucDoUuTien.objects.create(muc_do="Khan")
        self.nhom_quyen = Group.objects.create(name="Ban giam hieu")
        self.vai_tro_hieu_truong = VaiTro.objects.create(ten_vai_tro="Hieu truong", nhom_quyen=self.nhom_quyen)
        self.hieu_truong = GiaoVien.objects.create(ma_gv="GVHT001", ho_ten="Hieu Truong")
        set_giao_vien_roles(self.hieu_truong, self.vai_tro_hieu_truong)

    def test_get_displays_next_generated_number(self):
        VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="Bo Giao duc va Dao tao",
            so_ky_hieu="123/ABC",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban hien co",
            file_van_ban=SimpleUploadedFile("existing.pdf", b"%PDF-1.4 existing", content_type="application/pdf"),
            trang_thai_vb_den="Da tiep nhan",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )

        response = self.client.get(reverse("dang_ky_van_ban_den"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["next_so_vb_den"], "VBD0000002")

    def test_post_creates_document_with_expected_status(self):
        response = self.client.post(
            reverse("dang_ky_van_ban_den"),
            data={
                "ngay_nhan": "2026-03-28",
                "ngay_ky": "2026-03-27",
                "so_ky_hieu": "224/BGDDT",
                "ma_loai_vb": self.loai_van_ban.pk,
                "ma_muc_do": self.muc_do.pk,
                "co_quan_ban_hanh": "Bo Giao duc va Dao tao",
                "trich_yeu": "Tang cuong chi dao va khac phuc vi pham dao duc nha giao",
                "file_van_ban": SimpleUploadedFile(
                    "incoming.pdf",
                    b"%PDF-1.4 incoming",
                    content_type="application/pdf",
                ),
                "tep_dinh_kem_uploads": [
                    SimpleUploadedFile(
                        "incoming-attachment-1.pdf",
                        b"%PDF-1.4 attachment 1",
                        content_type="application/pdf",
                    ),
                    SimpleUploadedFile(
                        "incoming-attachment-2.docx",
                        b"PK incoming attachment 2",
                        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ),
                ],
            },
        )

        self.assertRedirects(response, reverse("dang_ky_van_ban_den"))
        van_ban_den = VanBanDen.objects.get()
        self.assertEqual(van_ban_den.ngay_nhan.isoformat(), "2026-03-28")
        self.assertEqual(van_ban_den.so_vb_den, "VBD0000001")
        self.assertEqual(van_ban_den.trang_thai_vb_den, "Cho phan cong")
        self.assertIn("incoming", van_ban_den.file_van_ban.name)
        self.assertEqual(van_ban_den.tep_dinh_kems.count(), 3)
        phan_cong = PhanCongXuLy.objects.get(so_vb_den=van_ban_den)
        self.assertEqual(phan_cong.nguoi_xu_ly, self.hieu_truong)
        self.assertEqual(phan_cong.trang_thai_xl, "Cho xu ly")

    def test_ban_hanh_noi_bo_toggle_switches_between_completed_and_published(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="Bo Giao duc va Dao tao",
            so_ky_hieu="300/BGDDT",
            ngay_ky="2026-03-27",
            trich_yeu="Van ban den da hoan thanh",
            file_van_ban=SimpleUploadedFile("incoming-finished.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den=VanBanDen.TrangThai.DA_HOAN_THANH,
            ngay_nhan="2026-03-28",
            ma_muc_do=self.muc_do,
        )

        publish_response = self.client.post(reverse("ban_hanh_noi_bo_van_ban_den", args=[van_ban_den.so_vb_den]))

        self.assertEqual(publish_response.status_code, 200)
        van_ban_den.refresh_from_db()
        self.assertTrue(van_ban_den.da_ban_hanh_noi_bo)

        unpublish_response = self.client.post(reverse("ban_hanh_noi_bo_van_ban_den", args=[van_ban_den.so_vb_den]))

        self.assertEqual(unpublish_response.status_code, 200)
        van_ban_den.refresh_from_db()
        self.assertFalse(van_ban_den.da_ban_hanh_noi_bo)

    def test_list_view_returns_documents(self):
        VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="15/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Thong bao cong tac",
            file_van_ban=SimpleUploadedFile("list.pdf", b"%PDF-1.4 list", content_type="application/pdf"),
            trang_thai_vb_den="Da tiep nhan",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )

        response = self.client.get(reverse("danh_sach_van_ban_den"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VBD0000001")

    def test_list_view_embeds_attachment_data_for_detail_modal(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="16/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Thong bao co tep dinh kem",
            file_van_ban=SimpleUploadedFile("incoming-main.pdf", b"%PDF-1.4 main", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        TepDinhKemVanBanDen.objects.create(
            so_vb_den=van_ban_den,
            tep_tin=SimpleUploadedFile("incoming-extra.pdf", b"%PDF-1.4 extra", content_type="application/pdf"),
            thu_tu=1,
        )

        response = self.client.get(reverse("danh_sach_van_ban_den"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-attachments-json", html=False)
        self.assertContains(response, "incoming-extra.pdf", html=False)

    def test_list_view_orders_documents_by_priority_then_date(self):
        hoa_toc = MucDoUuTien.objects.create(muc_do="Hoa toc")
        thuong_khan = MucDoUuTien.objects.create(muc_do="Thuong khan")
        binh_thuong = MucDoUuTien.objects.create(muc_do="Binh thuong")

        VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="01/BT",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban binh thuong",
            file_van_ban=SimpleUploadedFile("normal.pdf", b"%PDF-1.4 normal", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-30",
            ma_muc_do=binh_thuong,
        )
        VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="02/TK",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban thuong khan",
            file_van_ban=SimpleUploadedFile("urgent.pdf", b"%PDF-1.4 urgent", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-29",
            ma_muc_do=thuong_khan,
        )
        VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="03/HT",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban hoa toc",
            file_van_ban=SimpleUploadedFile("hot.pdf", b"%PDF-1.4 hot", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-28",
            ma_muc_do=hoa_toc,
        )

        response = self.client.get(reverse("danh_sach_van_ban_den"))

        documents = response.context["documents"]
        self.assertEqual(
            [document.trich_yeu for document in documents[:3]],
            ["Van ban hoa toc", "Van ban thuong khan", "Van ban binh thuong"],
        )

    def test_update_view_updates_document_and_returns_json(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="15/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Thong bao cong tac",
            file_van_ban=SimpleUploadedFile("update.pdf", b"%PDF-1.4 update", content_type="application/pdf"),
            trang_thai_vb_den="Da tiep nhan",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        muc_do_moi = MucDoUuTien.objects.create(muc_do="Thuong")

        response = self.client.post(
            reverse("cap_nhat_van_ban_den", args=[van_ban_den.so_vb_den]),
            data={
                "trang_thai_vb_den": "Đã hoàn thành",
                "ngay_nhan": "2026-03-28",
                "ngay_ky": "2026-03-27",
                "so_ky_hieu": "20/SGD",
                "ma_loai_vb": self.loai_van_ban.pk,
                "ma_muc_do": muc_do_moi.pk,
                "co_quan_ban_hanh": "Bo Giao duc",
                "trich_yeu": "Da cap nhat noi dung",
                "file_van_ban": SimpleUploadedFile(
                    "updated.pdf",
                    b"%PDF-1.4 updated",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        van_ban_den.refresh_from_db()
        self.assertEqual(van_ban_den.co_quan_ban_hanh, "Bo Giao duc")
        self.assertEqual(response.json()["document"]["status_class"], "status-done")
        self.assertTrue(van_ban_den.file_van_ban.name.endswith("updated.pdf"))

    def test_update_view_rejects_document_already_assigned(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="15/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Thong bao cong tac",
            file_van_ban=SimpleUploadedFile("assigned.pdf", b"%PDF-1.4 assigned", content_type="application/pdf"),
            trang_thai_vb_den="Cho xu ly",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )

        response = self.client.post(
            reverse("cap_nhat_van_ban_den", args=[van_ban_den.so_vb_den]),
            data={
                "trang_thai_vb_den": "Cho xu ly",
                "ngay_nhan": "2026-03-28",
                "ngay_ky": "2026-03-27",
                "so_ky_hieu": "20/SGD",
                "ma_loai_vb": self.loai_van_ban.pk,
                "ma_muc_do": self.muc_do.pk,
                "co_quan_ban_hanh": "Bo Giao duc",
                "trich_yeu": "Da cap nhat noi dung",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("khong con duoc chinh sua", response.json()["message"].lower())

    def test_theo_doi_tinh_trang_includes_processing_priority_counts(self):
        hoa_toc = MucDoUuTien.objects.create(muc_do="Hoa toc")
        thuong_khan = MucDoUuTien.objects.create(muc_do="Thuong khan")
        binh_thuong = MucDoUuTien.objects.create(muc_do="Binh thuong")

        VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="90/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban den hoa toc dang xu ly",
            file_van_ban=SimpleUploadedFile("incoming-priority.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den=VanBanDen.TrangThai.CHO_XU_LY,
            ngay_nhan="2026-03-21",
            ma_muc_do=hoa_toc,
        )
        VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.hieu_truong,
            trich_yeu="Van ban di thuong khan cho dang ky",
            nguoi_ky=self.hieu_truong,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("outgoing-priority.pdf", b"%PDF-1.4 outgoing", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.CHO_DANG_KY,
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=thuong_khan,
            so_ky_hieu="91/SGD",
        )
        VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.hieu_truong,
            trich_yeu="Van ban di binh thuong da ban hanh",
            nguoi_ky=self.hieu_truong,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("outgoing-done.pdf", b"%PDF-1.4 outgoing done", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.DA_BAN_HANH,
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=binh_thuong,
            so_ky_hieu="92/SGD",
        )

        response = self.client.get(reverse("theo_doi_tinh_trang"))

        self.assertEqual(response.status_code, 200)
        priority_card = next(card for card in response.context["dashboard_cards"] if card["title"] == "Văn bản ưu tiên")
        self.assertEqual(
            priority_card["items"],
            [("Hỏa tốc:", 1), ("Thượng khẩn:", 1), ("Khẩn:", 0), ("Bình thường:", 0)],
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class VanBanDiViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="secret123")
        self.client.force_login(self.user)
        self.loai_van_ban = LoaiVanBan.objects.create(ten_loai_vb="Cong van", ten_viet_tat="CV")
        self.muc_do = MucDoUuTien.objects.create(muc_do="Khan")
        self.nhom_quyen = Group.objects.create(name="Van thu")
        self.vai_tro = VaiTro.objects.create(ten_vai_tro="Van thu", nhom_quyen=self.nhom_quyen)
        self.nguoi_tao = GiaoVien.objects.create(ma_gv="GV000001", ho_ten="Nguyen Van A")
        set_giao_vien_roles(self.nguoi_tao, self.vai_tro)
        self.nguoi_ky = GiaoVien.objects.create(ma_gv="GV000002", ho_ten="Nguyen Van B")
        set_giao_vien_roles(self.nguoi_ky, self.vai_tro)
        self.nguoi_tao_khac = GiaoVien.objects.create(ma_gv="GV000003", ho_ten="Nguyen Van C")
        set_giao_vien_roles(self.nguoi_tao_khac, self.vai_tro)

    def test_list_view_returns_documents(self):
        VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Trien khai ke hoach cong tac",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("draft.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Da duyet",
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="15/SGD",
        )

        response = self.client.get(reverse("danh_sach_van_ban_di"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "VBO00000001")
        self.assertContains(response, "Trien khai ke hoach cong tac")

    def test_list_view_orders_documents_by_priority_then_date(self):
        hoa_toc = MucDoUuTien.objects.create(muc_do="Hoa toc")
        thuong_khan = MucDoUuTien.objects.create(muc_do="Thuong khan")
        binh_thuong = MucDoUuTien.objects.create(muc_do="Binh thuong")

        VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban di binh thuong",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("normal-out.pdf", b"%PDF-1.4 normal", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-30",
            ma_muc_do=binh_thuong,
            so_ky_hieu="10/BT",
        )
        VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban di thuong khan",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("urgent-out.pdf", b"%PDF-1.4 urgent", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-29",
            ma_muc_do=thuong_khan,
            so_ky_hieu="11/TK",
        )
        VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban di hoa toc",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("hot-out.pdf", b"%PDF-1.4 hot", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-28",
            ma_muc_do=hoa_toc,
            so_ky_hieu="12/HT",
        )

        response = self.client.get(reverse("danh_sach_van_ban_di"))

        documents = response.context["documents"]
        self.assertEqual(
            [document.trich_yeu for document in documents[:3]],
            ["Van ban di hoa toc", "Van ban di thuong khan", "Van ban di binh thuong"],
        )

    def test_update_view_updates_document_and_returns_json(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban hien co",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="UBND tinh",
            ban_du_thao=SimpleUploadedFile("existing-draft.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Soan thao",
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="20/SGD",
        )
        muc_do_moi = MucDoUuTien.objects.create(muc_do="Thuong")

        response = self.client.post(
            reverse("cap_nhat_van_ban_di", args=[van_ban_di.so_vb_di]),
            data={
                "trang_thai_vb_di": "Đã ban hành",
                "ngay_ban_hanh": "2026-03-28",
                "ngay_ky": "2026-03-27",
                "so_ky_hieu": "25/SGD",
                "ma_loai_vb": self.loai_van_ban.pk,
                "ma_muc_do": muc_do_moi.pk,
                "nguoi_tao": self.nguoi_tao_khac.pk,
                "nguoi_ky": self.nguoi_ky.pk,
                "noi_nhan": "Bo Giao duc",
                "trich_yeu": "Da cap nhat noi dung",
                "ban_du_thao": SimpleUploadedFile(
                    "updated-draft.pdf",
                    b"%PDF-1.4 updated draft",
                    content_type="application/pdf",
                ),
                "ban_chinh_thuc": SimpleUploadedFile(
                    "official.pdf",
                    b"%PDF-1.4 official",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        van_ban_di.refresh_from_db()
        self.assertEqual(van_ban_di.noi_nhan, "Bo Giao duc")
        self.assertEqual(van_ban_di.nguoi_tao, self.nguoi_tao)
        self.assertEqual(response.json()["document"]["status_class"], "status-done")
        self.assertTrue(van_ban_di.ban_du_thao.name.endswith("updated-draft.pdf"))
        self.assertTrue(van_ban_di.ban_chinh_thuc.name.endswith("official.pdf"))

    def test_tao_van_ban_view_creates_van_ban_di(self):
        self.client.force_login(self.nguoi_tao.user)

        response = self.client.post(
            reverse("tao_van_ban"),
            data={
                "ma_loai_vb": self.loai_van_ban.pk,
                "ma_muc_do": self.muc_do.pk,
                "noi_nhan": "Cong doan",
                "trich_yeu": "Trinh duyet van ban moi",
                "ban_du_thao": SimpleUploadedFile(
                    "tao-moi.pdf",
                    b"%PDF-1.4 tao moi",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertRedirects(response, reverse("danh_sach_van_ban_di"))
        van_ban_di = VanBanDi.objects.latest("so_vb_di")
        self.assertEqual(van_ban_di.nguoi_tao, self.nguoi_tao)
        self.assertEqual(van_ban_di.nguoi_ky, self.nguoi_tao)
        self.assertEqual(van_ban_di.ma_muc_do, self.muc_do)
        self.assertEqual(van_ban_di.trang_thai_vb_di, "Cho duyet")
        self.assertEqual(van_ban_di.so_ky_hieu, "")
        self.assertIn("tao-moi", van_ban_di.ban_du_thao.name)
        self.assertEqual(
            van_ban_di.tep_dinh_kem_dis.filter(loai_tep="du_thao").count(),
            0,
        )
        xu_ly = XuLy.objects.get(ma_vb_di=van_ban_di)
        self.assertEqual(xu_ly.trang_thai_ky, XuLy.TRANG_THAI_CHO_DUYET)
        self.assertEqual(xu_ly.vai_tro_ky, XuLy.VAI_TRO_KY_CHINH)

    def test_tao_van_ban_view_for_truong_bo_mon_two_level_sends_directly_to_hieu_truong(self):
        nhom_bgh = Group.objects.create(name="Ban giam hieu tao van ban")
        nhom_to = Group.objects.create(name="To truong")
        vai_tro_hieu_truong = VaiTro.objects.create(ten_vai_tro="Hieu truong", nhom_quyen=nhom_bgh)
        vai_tro_truong_bo_mon = VaiTro.objects.create(ten_vai_tro="To truong", nhom_quyen=nhom_to)
        loai_hai_cap = LoaiVanBan.objects.create(
            ten_loai_vb="To trinh hai cap",
            ten_viet_tat="TT",
            twocap=LoaiVanBan.TWO_CAP_HAI_CAP,
        )
        hieu_truong = GiaoVien.objects.create(ma_gv="GVHT9001", ho_ten="Hieu Truong Moi")
        set_giao_vien_roles(hieu_truong, vai_tro_hieu_truong)
        truong_bo_mon = GiaoVien.objects.create(ma_gv="GVTBM001", ho_ten="Truong Bo Mon")
        set_giao_vien_roles(truong_bo_mon, vai_tro_truong_bo_mon)
        to_chuyen_mon = ToChuyenMon.objects.create(ten_to="To Van", to_truong=truong_bo_mon)
        truong_bo_mon.ma_to = to_chuyen_mon
        truong_bo_mon.save()

        self.client.force_login(truong_bo_mon.user)

        response = self.client.post(
            reverse("tao_van_ban"),
            data={
                "ma_loai_vb": loai_hai_cap.pk,
                "ma_muc_do": self.muc_do.pk,
                "noi_nhan": "Ban giam hieu",
                "trich_yeu": "Van ban hai cap do truong bo mon tao",
                "ban_du_thao": SimpleUploadedFile(
                    "truong-bo-mon.pdf",
                    b"%PDF-1.4 truong bo mon",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("danh_sach_van_ban_di"))
        van_ban_di = VanBanDi.objects.latest("so_vb_di")
        xu_lys = XuLy.objects.filter(ma_vb_di=van_ban_di).order_by("ma_xu_ly")
        self.assertEqual(xu_lys.count(), 2)
        self.assertTrue(
            xu_lys.filter(
                ma_gv=truong_bo_mon,
                vai_tro_ky=XuLy.VAI_TRO_KY_NHAY,
                trang_thai_ky=XuLy.TRANG_THAI_DA_DUYET,
            ).exists()
        )
        self.assertTrue(
            xu_lys.filter(
                ma_gv=hieu_truong,
                vai_tro_ky=XuLy.VAI_TRO_KY_CHINH,
                trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
            ).exists()
        )

    def test_tao_van_ban_view_for_regular_teacher_two_level_creates_waiting_to_truong_record(self):
        nhom_bgh = Group.objects.create(name="Ban giam hieu giao vien thuong")
        nhom_to = Group.objects.create(name="To truong giao vien thuong")
        vai_tro_hieu_truong = VaiTro.objects.create(ten_vai_tro="Hieu truong", nhom_quyen=nhom_bgh)
        vai_tro_to_truong = VaiTro.objects.create(ten_vai_tro="To truong", nhom_quyen=nhom_to)
        loai_hai_cap = LoaiVanBan.objects.create(
            ten_loai_vb="Ke hoach hai cap giao vien thuong",
            ten_viet_tat="KH",
            twocap=LoaiVanBan.TWO_CAP_HAI_CAP,
        )
        hieu_truong = GiaoVien.objects.create(ma_gv="GVHT9010", ho_ten="Hieu Truong Thuong")
        set_giao_vien_roles(hieu_truong, vai_tro_hieu_truong)
        to_truong = GiaoVien.objects.create(ma_gv="GVTT9010", ho_ten="To Truong Thuong")
        set_giao_vien_roles(to_truong, vai_tro_to_truong)
        to_chuyen_mon = ToChuyenMon.objects.create(ten_to="To Sinh", to_truong=to_truong)
        giao_vien_thuong = GiaoVien.objects.create(ma_gv="GVTH9010", ho_ten="Giao Vien Thuong", ma_to=to_chuyen_mon)

        self.client.force_login(giao_vien_thuong.user)

        response = self.client.post(
            reverse("tao_van_ban"),
            data={
                "ma_loai_vb": loai_hai_cap.pk,
                "ma_muc_do": self.muc_do.pk,
                "noi_nhan": "Ban giam hieu",
                "trich_yeu": "Van ban hai cap do giao vien thuong tao",
                "ban_du_thao": SimpleUploadedFile(
                    "giao-vien-thuong-hai-cap.pdf",
                    b"%PDF-1.4 teacher two level",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        van_ban_di = VanBanDi.objects.latest("so_vb_di")
        self.assertTrue(
            XuLy.objects.filter(
                ma_vb_di=van_ban_di,
                ma_gv=to_truong,
                vai_tro_ky=XuLy.VAI_TRO_KY_NHAY,
                trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
            ).exists()
        )
        self.assertFalse(
            XuLy.objects.filter(
                ma_vb_di=van_ban_di,
                ma_gv=hieu_truong,
                trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
            ).exists()
        )

    def test_tao_van_ban_view_for_phong_ban_to_chuc_two_level_creates_self_and_principal_records(self):
        nhom_bgh = Group.objects.create(name="Ban giam hieu tao van ban phong ban")
        nhom_to_chuc = Group.objects.create(name="Phong/ban / to chuc")
        vai_tro_hieu_truong = VaiTro.objects.create(ten_vai_tro="Hieu truong", nhom_quyen=nhom_bgh)
        vai_tro_to_chuc = VaiTro.objects.create(ten_vai_tro="Bi thu doan thanh nien", nhom_quyen=nhom_to_chuc)
        loai_hai_cap = LoaiVanBan.objects.create(
            ten_loai_vb="Thong bao hai cap",
            ten_viet_tat="TB",
            twocap=LoaiVanBan.TWO_CAP_HAI_CAP,
        )
        hieu_truong = GiaoVien.objects.create(ma_gv="GVHT9002", ho_ten="Hieu Truong Phong Ban")
        set_giao_vien_roles(hieu_truong, vai_tro_hieu_truong)
        nguoi_to_chuc = GiaoVien.objects.create(ma_gv="GVTC9002", ho_ten="Bi Thu Doan")
        set_giao_vien_roles(nguoi_to_chuc, vai_tro_to_chuc)

        self.client.force_login(nguoi_to_chuc.user)

        response = self.client.post(
            reverse("tao_van_ban"),
            data={
                "ma_loai_vb": loai_hai_cap.pk,
                "ma_muc_do": self.muc_do.pk,
                "noi_nhan": "Toan truong",
                "trich_yeu": "Van ban hai cap do phong ban to chuc tao",
                "ban_du_thao": SimpleUploadedFile(
                    "phong-ban-to-chuc.pdf",
                    b"%PDF-1.4 organization",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        van_ban_di = VanBanDi.objects.latest("so_vb_di")
        self.assertTrue(
            XuLy.objects.filter(
                ma_vb_di=van_ban_di,
                ma_gv=nguoi_to_chuc,
                vai_tro_ky=XuLy.VAI_TRO_KY_NHAY,
                trang_thai_ky=XuLy.TRANG_THAI_DA_DUYET,
            ).exists()
        )
        self.assertTrue(
            XuLy.objects.filter(
                ma_vb_di=van_ban_di,
                ma_gv=hieu_truong,
                vai_tro_ky=XuLy.VAI_TRO_KY_CHINH,
                trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
            ).exists()
        )

    def test_cap_so_view_returns_generated_so_ky_hieu_for_waiting_registration_document(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Cho dang ky",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("draft-register.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Cho dang ky",
            ma_muc_do=self.muc_do,
            so_ky_hieu="",
        )

        response = self.client.post(reverse("cap_so_van_ban_di", args=[van_ban_di.so_vb_di]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["so_ky_hieu"], "01/CV-THPTND")

    def test_dang_ky_view_updates_status_and_so_ky_hieu(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Cho dang ky",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("draft-register-save.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Cho dang ky",
            ma_muc_do=self.muc_do,
            so_ky_hieu="",
        )

        response = self.client.post(
            reverse("dang_ky_van_ban_di", args=[van_ban_di.so_vb_di]),
            data={
                "so_ky_hieu": "01/CV-THPTND",
                "ban_chinh_thuc": SimpleUploadedFile(
                    "official-register.pdf",
                    b"%PDF-1.4 official register",
                    content_type="application/pdf",
                ),
                "tep_dinh_kem_uploads": [
                    SimpleUploadedFile(
                        "official-attachment-1.pdf",
                        b"%PDF-1.4 official attachment 1",
                        content_type="application/pdf",
                    ),
                    SimpleUploadedFile(
                        "official-attachment-2.docx",
                        b"PK official attachment 2",
                        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    ),
                ],
            },
        )

        self.assertRedirects(response, reverse("dang_ky_van_ban_di", args=[van_ban_di.so_vb_di]))
        van_ban_di.refresh_from_db()
        self.assertEqual(van_ban_di.trang_thai_vb_di, VanBanDi.TrangThai.DA_DANG_KY)
        self.assertEqual(van_ban_di.ngay_ban_hanh, timezone.localdate())
        self.assertEqual(van_ban_di.so_thu_tu, 1)
        self.assertEqual(van_ban_di.so_ky_hieu, "01/CV-THPTND")
        self.assertIn("official-register", van_ban_di.ban_chinh_thuc.name)
        self.assertEqual(
            van_ban_di.tep_dinh_kem_dis.filter(loai_tep="chinh_thuc").count(),
            2,
        )

    def test_dang_ky_view_shows_post_registration_buttons_for_legacy_waiting_transfer_status(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Cho luan chuyen cu",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("draft-legacy-transfer.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.CHO_LUAN_CHUYEN,
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="01/CV-THPTND",
        )

        response = self.client.get(reverse("dang_ky_van_ban_di", args=[van_ban_di.so_vb_di]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Phat hanh ben ngoai")

    def test_list_view_embeds_attachment_data_for_detail_modal(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban co tep dinh kem",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("draft-detail.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            ban_chinh_thuc=SimpleUploadedFile("official-detail.pdf", b"%PDF-1.4 official", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.DA_DANG_KY,
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="09/CV-THPTND",
        )
        TepDinhKemVanBanDi.objects.create(
            so_vb_di=van_ban_di,
            loai_tep=TepDinhKemVanBanDi.LoaiTep.CHINH_THUC,
            tep_tin=SimpleUploadedFile("official-extra.pdf", b"%PDF-1.4 extra", content_type="application/pdf"),
            thu_tu=1,
        )

        response = self.client.get(reverse("danh_sach_van_ban_di"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-ban-chinh-thuc-attachments-json", html=False)
        self.assertContains(response, "official-extra.pdf", html=False)
        van_ban_di.refresh_from_db()
        self.assertEqual(van_ban_di.trang_thai_vb_di, VanBanDi.TrangThai.DA_DANG_KY)

    def test_luan_chuyen_view_updates_waiting_transfer_status(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Da dang ky",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Giao duc",
            ban_du_thao=SimpleUploadedFile("draft-transfer.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.DA_DANG_KY,
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="01/CV-THPTND",
        )

        response = self.client.post(reverse("luan_chuyen_van_ban_di", args=[van_ban_di.so_vb_di]))

        self.assertEqual(response.status_code, 200)
        van_ban_di.refresh_from_db()
        self.assertEqual(van_ban_di.trang_thai_vb_di, VanBanDi.TrangThai.DA_DANG_KY)
        self.assertTrue(van_ban_di.da_gui_phan_cong)
        self.assertEqual(response.json()["document"]["status_class"], "status-processing")

    def test_danh_sach_van_ban_di_modal_contains_post_registration_buttons(self):
        NoiNhan.objects.create(ten_noi_nhan="So Giao duc")

        response = self.client.get(reverse("danh_sach_van_ban_di"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="btn-external-publish"', html=False)
        self.assertContains(response, 'id="btn-internal-publish"', html=False)
        self.assertContains(response, 'id="btn-transfer"', html=False)
        self.assertContains(response, 'id="recipient-modal"', html=False)

    def test_van_ban_da_ban_hanh_view_returns_published_documents_and_allows_van_thu_edit_link(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So Giao duc",
            so_ky_hieu="33/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban den ban hanh noi bo",
            file_van_ban=SimpleUploadedFile("incoming-published.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den=VanBanDen.TrangThai.DA_HOAN_THANH,
            da_ban_hanh_noi_bo=True,
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban di da ban hanh",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="Bo Giao duc",
            ban_du_thao=SimpleUploadedFile("draft-published.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            ban_chinh_thuc=SimpleUploadedFile("official-published.pdf", b"%PDF-1.4 official", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.DA_HOAN_THANH,
            da_ban_hanh_noi_bo=True,
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="34/SGD",
        )

        self.client.force_login(self.nguoi_tao.user)
        response = self.client.get(reverse("van_ban_da_ban_hanh"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, van_ban_den.so_vb_den)
        self.assertContains(response, van_ban_di.so_vb_di)
        self.assertTrue(response.context["can_edit_published_documents"])

    def test_van_ban_da_tao_view_only_returns_documents_created_by_current_user(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban do minh tao",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="Bo Giao duc",
            ban_du_thao=SimpleUploadedFile("draft-own.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="35/SGD",
        )
        VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao_khac,
            trich_yeu="Van ban cua nguoi khac",
            nguoi_ky=self.nguoi_ky,
            ngay_ky="2026-03-20",
            noi_nhan="So Noi vu",
            ban_du_thao=SimpleUploadedFile("draft-other.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="36/SGD",
        )

        self.client.force_login(self.nguoi_tao.user)
        response = self.client.get(reverse("van_ban_da_tao"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, van_ban_di.so_vb_di)
        self.assertNotContains(response, "Van ban cua nguoi khac")


class GiaoVienVaiTroTests(TestCase):
    def test_giao_vien_tu_sinh_ma_gv_khi_de_trong(self):
        giao_vien = GiaoVien.objects.create(ho_ten="Tran Van Tu Dong")

        self.assertTrue(giao_vien.ma_gv.startswith("GV"))
        self.assertEqual(giao_vien.user.username, giao_vien.ma_gv)

    def test_giao_vien_can_giu_nhieu_vai_tro_va_duoc_dong_bo_group(self):
        nhom_van_thu = Group.objects.create(name="Van thu")
        nhom_quan_ly = Group.objects.create(name="Quan ly")
        vai_tro_van_thu = VaiTro.objects.create(ten_vai_tro="Van thu", nhom_quyen=nhom_van_thu)
        vai_tro_quan_ly = VaiTro.objects.create(ten_vai_tro="Quan ly", nhom_quyen=nhom_quan_ly)

        giao_vien = GiaoVien.objects.create(ma_gv="GV000010", ho_ten="Tran Van D")
        set_giao_vien_roles(giao_vien, vai_tro_van_thu, vai_tro_quan_ly)

        giao_vien.refresh_from_db()

        self.assertEqual(giao_vien.chuc_vu, "Van thu, Quan ly")
        self.assertEqual(
            set(giao_vien.user.groups.values_list("name", flat=True)),
            {"Van thu", "Quan ly"},
        )
        self.assertEqual(
            set(giao_vien.user.groups.values_list("name", flat=True)),
            {"Van thu", "Quan ly"},
        )

    def test_mot_giao_vien_chi_duoc_lam_to_truong_mot_to(self):
        nhom_to = Group.objects.create(name="To bo mon")
        vai_tro_truong_bo_mon = VaiTro.objects.create(ten_vai_tro="To truong", nhom_quyen=nhom_to)
        giao_vien = GiaoVien.objects.create(ho_ten="Nguyen Van To Truong")
        set_giao_vien_roles(giao_vien, vai_tro_truong_bo_mon)

        ToChuyenMon.objects.create(ten_to="To Toan", to_truong=giao_vien)

        with self.assertRaises(ValidationError):
            ToChuyenMon.objects.create(ten_to="To Ly", to_truong=giao_vien)

    def test_to_truong_khong_duoc_kiem_nhiem_vai_tro_khac(self):
        nhom_to = Group.objects.create(name="To chuyen mon")
        nhom_bgh = Group.objects.create(name="Ban giam hieu phu")
        vai_tro_truong_bo_mon = VaiTro.objects.create(ten_vai_tro="To truong", nhom_quyen=nhom_to)
        vai_tro_pho_hieu_truong = VaiTro.objects.create(ten_vai_tro="Pho hieu truong", nhom_quyen=nhom_bgh)
        giao_vien = GiaoVien.objects.create(ho_ten="Nguyen Van Kiem Nhiem")
        set_giao_vien_roles(giao_vien, vai_tro_truong_bo_mon, vai_tro_pho_hieu_truong)

        with self.assertRaises(ValidationError):
            ToChuyenMon.objects.create(ten_to="To Hoa", to_truong=giao_vien)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class QuanLyCongViecTests(TestCase):
    def setUp(self):
        self.nhom_quyen = Group.objects.create(name="To chuyen mon")
        self.vai_tro = VaiTro.objects.create(ten_vai_tro="To truong", nhom_quyen=self.nhom_quyen)
        self.loai_van_ban = LoaiVanBan.objects.create(ten_loai_vb="Ke hoach", ten_viet_tat="KH")
        self.muc_do = MucDoUuTien.objects.create(muc_do="Thuong")
        self.nguoi_tao = GiaoVien.objects.create(ma_gv="GV100001", ho_ten="Nguoi Tao")
        self.nguoi_duyet = GiaoVien.objects.create(ma_gv="GV100002", ho_ten="Nguoi Duyet")
        set_giao_vien_roles(self.nguoi_duyet, self.vai_tro)
        self.nguoi_khac = GiaoVien.objects.create(ma_gv="GV100003", ho_ten="Nguoi Khac")
        self.client.force_login(self.nguoi_duyet.user)

    def tao_van_ban_cho_duyet(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban can duyet",
            nguoi_ky=self.nguoi_duyet,
            ngay_ky="2026-03-20",
            noi_nhan="Phong chuyen mon",
            ban_du_thao=SimpleUploadedFile("du-thao.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="01/KH-THPTND",
        )
        XuLy.objects.create(
            ma_vb_di=van_ban_di,
            ma_gv=self.nguoi_duyet,
            vai_tro_ky=XuLy.VAI_TRO_KY_CHINH,
            trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
        )
        return van_ban_di

    def test_duyet_van_ban_view_only_returns_documents_for_current_approver(self):
        van_ban_di = self.tao_van_ban_cho_duyet()
        van_ban_khac = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban cua nguoi khac",
            nguoi_ky=self.nguoi_khac,
            ngay_ky="2026-03-20",
            noi_nhan="Phong hanh chinh",
            ban_du_thao=SimpleUploadedFile("du-thao-khac.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-22",
            ma_muc_do=self.muc_do,
            so_ky_hieu="02/KH-THPTND",
        )
        XuLy.objects.create(
            ma_vb_di=van_ban_khac,
            ma_gv=self.nguoi_khac,
            vai_tro_ky=XuLy.VAI_TRO_KY_CHINH,
            trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
        )

        response = self.client.get(reverse("duyet_van_ban"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, van_ban_di.so_vb_di)
        self.assertNotContains(response, van_ban_khac.so_vb_di)

    def test_van_ban_xu_ly_ca_nhan_only_shows_documents_current_user_is_processing(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="40/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban dang xu ly",
            file_van_ban=SimpleUploadedFile("personal-processing.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Da phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban chi de phan cong tiep",
            nguoi_ky=self.nguoi_duyet,
            ngay_ky="2026-03-20",
            noi_nhan="Phong chuyen mon",
            ban_du_thao=SimpleUploadedFile("personal-assign.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            trang_thai_vb_di="Cho phan cong",
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="41/SGD",
        )
        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_den,
            nguoi_xu_ly=self.nguoi_duyet,
            nguoi_phan_cong=self.nguoi_tao,
            noi_dung_cd="Xu ly truc tiep.",
            thoi_han="2026-03-31",
            trang_thai_xl="Dang xu ly",
        )
        PhanCongXuLy.objects.create(
            so_vb_di=van_ban_di,
            nguoi_xu_ly=self.nguoi_duyet,
            nguoi_phan_cong=self.nguoi_tao,
            noi_dung_cd="Chi de chuyen phan cong.",
            thoi_han="2026-03-31",
            trang_thai_xl="Cho xu ly",
        )

        response = self.client.get(reverse("van_ban_xu_ly_ca_nhan"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, van_ban_den.so_vb_den)
        self.assertNotContains(response, van_ban_di.so_vb_di)

    def test_nguoi_dung_to_chuc_trong_truong_duoc_phan_cong_cho_tat_ca_tru_ban_giam_hieu(self):
        nhom_to_chuc = Group.objects.create(name="Nguoi dung to chuc trong truong")
        nhom_bgh = Group.objects.create(name="Ban giam hieu")
        vai_tro_to_chuc = VaiTro.objects.create(
            ten_vai_tro="Nguoi dung to chuc trong truong",
            nhom_quyen=nhom_to_chuc,
        )
        vai_tro_bgh = VaiTro.objects.create(ten_vai_tro="Pho hieu truong", nhom_quyen=nhom_bgh)
        nguoi_to_chuc = GiaoVien.objects.create(ma_gv="GV200001", ho_ten="Nguoi To Chuc")
        set_giao_vien_roles(nguoi_to_chuc, vai_tro_to_chuc)
        giao_vien_thuong = GiaoVien.objects.create(ma_gv="GV200002", ho_ten="Giao Vien Thuong")
        giao_vien_bgh = GiaoVien.objects.create(ma_gv="GV200003", ho_ten="Pho Hieu Truong")
        set_giao_vien_roles(giao_vien_bgh, vai_tro_bgh)

        self.client.force_login(nguoi_to_chuc.user)

        response = self.client.get(reverse("can_phan_cong"))

        self.assertEqual(response.status_code, 200)
        allowed_ids = {giao_vien.pk for giao_vien in response.context["giao_vien_list"]}
        self.assertIn(giao_vien_thuong.pk, allowed_ids)
        self.assertNotIn(giao_vien_bgh.pk, allowed_ids)

    def test_nguoi_dung_to_chuc_trong_truong_khong_duoc_phan_cong_cho_ban_giam_hieu(self):
        nhom_to_chuc = Group.objects.create(name="Nguoi dung to chuc trong truong")
        nhom_bgh = Group.objects.create(name="Ban giam hieu")
        vai_tro_to_chuc = VaiTro.objects.create(
            ten_vai_tro="Nguoi dung to chuc trong truong",
            nhom_quyen=nhom_to_chuc,
        )
        vai_tro_bgh = VaiTro.objects.create(ten_vai_tro="Hieu truong", nhom_quyen=nhom_bgh)
        nguoi_to_chuc = GiaoVien.objects.create(ma_gv="GV200011", ho_ten="Nguoi To Chuc 2")
        set_giao_vien_roles(nguoi_to_chuc, vai_tro_to_chuc)
        giao_vien_bgh = GiaoVien.objects.create(ma_gv="GV200012", ho_ten="Hieu Truong Test")
        set_giao_vien_roles(giao_vien_bgh, vai_tro_bgh)
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="42/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban de test phan cong",
            file_van_ban=SimpleUploadedFile("organization.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )

        self.client.force_login(nguoi_to_chuc.user)
        response = self.client.post(
            reverse("luu_phan_cong_xu_ly"),
            data={
                "loai": "den",
                "record_id": van_ban_den.so_vb_den,
                "assignment_payload": json.dumps(
                    [{"id": giao_vien_bgh.pk, "instruction": "Khong hop le."}]
                ),
                "thoi_han": "2026-03-31",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("tru ban giam hieu", response.json()["message"].lower())

    def test_ban_giam_hieu_chi_bi_chan_tao_van_ban_cong_viec_ca_nhan_va_dang_ky(self):
        nhom_bgh_user = Group.objects.create(name="Ban giam hieu")
        vai_tro_bgh_user = VaiTro.objects.create(ten_vai_tro="Pho hieu truong", nhom_quyen=nhom_bgh_user)
        nguoi_bgh = GiaoVien.objects.create(ma_gv="GVBGH999", ho_ten="Nguoi dung BGH")
        set_giao_vien_roles(nguoi_bgh, vai_tro_bgh_user)

        self.client.force_login(nguoi_bgh.user)

        response_create = self.client.get(reverse("tao_van_ban"))
        response_work = self.client.get(reverse("duyet_van_ban"))
        response_personal = self.client.get(reverse("van_ban_xu_ly_ca_nhan"))
        response_created = self.client.get(reverse("van_ban_da_tao"))
        response_published = self.client.get(reverse("van_ban_da_ban_hanh"))
        response_incoming = self.client.get(reverse("danh_sach_van_ban_den"))
        response_register_incoming = self.client.get(reverse("dang_ky_van_ban_den"))
        response_register_outgoing = self.client.get(reverse("dang_ky_van_ban_di_tu_danh_muc"))

        self.assertEqual(response_create.status_code, 302)
        self.assertEqual(response_work.status_code, 200)
        self.assertEqual(response_personal.status_code, 302)
        self.assertEqual(response_created.status_code, 200)
        self.assertEqual(response_published.status_code, 200)
        self.assertEqual(response_incoming.status_code, 200)
        self.assertEqual(response_register_incoming.status_code, 302)
        self.assertEqual(response_register_outgoing.status_code, 302)

    def test_van_thu_khong_duoc_truy_cap_quan_ly_cong_viec(self):
        nhom_van_thu = Group.objects.create(name="Van thu")
        vai_tro_van_thu = VaiTro.objects.create(ten_vai_tro="Van thu", nhom_quyen=nhom_van_thu)
        nguoi_van_thu = GiaoVien.objects.create(ma_gv="GVVT001", ho_ten="Nguoi Van Thu")
        set_giao_vien_roles(nguoi_van_thu, vai_tro_van_thu)

        self.client.force_login(nguoi_van_thu.user)
        response = self.client.get(reverse("duyet_van_ban"))

        self.assertEqual(response.status_code, 302)

    def test_nguoi_co_vai_tro_thuoc_nhom_phong_ban_to_chuc_duoc_truy_cap_quan_ly_cong_viec(self):
        nhom_to_chuc = Group.objects.create(name="Phong/ban / to chuc")
        vai_tro_bi_thu = VaiTro.objects.create(
            ten_vai_tro="Bi thu doan thanh nien",
            nhom_quyen=nhom_to_chuc,
        )
        nguoi_to_chuc = GiaoVien.objects.create(ma_gv="GVTC001", ho_ten="Bi Thu Doan")
        set_giao_vien_roles(nguoi_to_chuc, vai_tro_bi_thu)

        self.client.force_login(nguoi_to_chuc.user)
        response = self.client.get(reverse("duyet_van_ban"))

        self.assertEqual(response.status_code, 200)

    def test_home_redirects_ban_giam_hieu_to_incoming_documents(self):
        nhom_bgh_user = Group.objects.create(name="Ban giam hieu")
        vai_tro_bgh_user = VaiTro.objects.create(ten_vai_tro="Pho hieu truong home", nhom_quyen=nhom_bgh_user)
        nguoi_bgh = GiaoVien.objects.create(ma_gv="GVBGH998", ho_ten="BGH Home")
        set_giao_vien_roles(nguoi_bgh, vai_tro_bgh_user)

        self.client.force_login(nguoi_bgh.user)
        response = self.client.get(reverse("home"))

        self.assertRedirects(response, reverse("danh_sach_van_ban_den"))

    def test_phan_cong_xu_ly_view_creates_multiple_assignments(self):
        van_ban_di = self.tao_van_ban_cho_duyet()

        response = self.client.post(
            reverse("phan_cong_xu_ly_van_ban_di", args=[van_ban_di.so_vb_di]),
            data={
                "assigned_ids[]": [self.nguoi_tao.pk, self.nguoi_khac.pk],
                "chi_dao": "Xu ly va bao cao lai.",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(PhanCongXuLy.objects.filter(so_vb_di=van_ban_di).count(), 2)
        self.assertEqual(
            set(PhanCongXuLy.objects.filter(so_vb_di=van_ban_di).values_list("nguoi_xu_ly_id", flat=True)),
            {self.nguoi_tao.pk, self.nguoi_khac.pk},
        )
        self.assertEqual(
            set(PhanCongXuLy.objects.filter(so_vb_di=van_ban_di).values_list("nguoi_phan_cong_id", flat=True)),
            {self.nguoi_duyet.pk},
        )
        self.assertEqual(response.json()["document"]["tinh_trang_phan_cong"], "Da phan cong")

    def test_duyet_van_ban_action_marks_current_approval_done(self):
        van_ban_di = self.tao_van_ban_cho_duyet()

        response = self.client.post(reverse("duyet_van_ban_di_action", args=[van_ban_di.so_vb_di]))

        self.assertEqual(response.status_code, 200)
        van_ban_di.refresh_from_db()
        xu_ly = XuLy.objects.get(ma_vb_di=van_ban_di, ma_gv=self.nguoi_duyet)
        self.assertEqual(xu_ly.trang_thai_ky, XuLy.TRANG_THAI_DA_DUYET)
        self.assertIsNotNone(xu_ly.thoi_gian_ky)
        self.assertEqual(van_ban_di.trang_thai_vb_di, "Cho dang ky")

    def test_duyet_van_ban_action_request_revision_moves_document_to_returned_list(self):
        van_ban_di = self.tao_van_ban_cho_duyet()

        response = self.client.post(
            reverse("duyet_van_ban_di_action", args=[van_ban_di.so_vb_di]),
            data={"action": "request_revision", "yc_chinh_sua": "Bo sung noi dung theo gop y."},
        )

        self.assertEqual(response.status_code, 200)
        van_ban_di.refresh_from_db()
        xu_ly = XuLy.objects.get(ma_vb_di=van_ban_di, ma_gv=self.nguoi_duyet)
        nhat_ky = NhatKyVanBan.objects.get(ma_vb_di=van_ban_di)
        self.assertEqual(xu_ly.trang_thai_ky, XuLy.TRANG_THAI_CHO_CHINH_SUA)
        self.assertEqual(van_ban_di.trang_thai_vb_di, "Dang chinh sua")
        self.assertEqual(nhat_ky.trang_thai, "Cho chinh sua")

        self.client.force_login(self.nguoi_tao.user)
        returned_response = self.client.get(reverse("van_ban_tra_lai"))
        self.assertEqual(returned_response.status_code, 200)
        self.assertContains(returned_response, van_ban_di.so_vb_di)

    def test_duyet_van_ban_action_delegate_creates_waiting_record_for_pho_hieu_truong(self):
        nhom_bgh = Group.objects.create(name="Ban giam hieu delegate")
        vai_tro_hieu_truong = VaiTro.objects.create(ten_vai_tro="Hieu truong", nhom_quyen=nhom_bgh)
        vai_tro_pho_hieu_truong = VaiTro.objects.create(ten_vai_tro="Pho hieu truong", nhom_quyen=nhom_bgh)
        hieu_truong = GiaoVien.objects.create(ma_gv="GVHT8888", ho_ten="Hieu Truong Delegate")
        set_giao_vien_roles(hieu_truong, vai_tro_hieu_truong)
        pho_hieu_truong = GiaoVien.objects.create(ma_gv="GVPHT888", ho_ten="Pho Hieu Truong Delegate")
        set_giao_vien_roles(pho_hieu_truong, vai_tro_pho_hieu_truong)
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban uy quyen duyet",
            nguoi_ky=hieu_truong,
            ngay_ky="2026-03-20",
            noi_nhan="Phong chuyen mon",
            ban_du_thao=SimpleUploadedFile("uy-quyen.pdf", b"%PDF-1.4 delegate", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="88/KH-THPTND",
        )
        XuLy.objects.create(
            ma_vb_di=van_ban_di,
            ma_gv=hieu_truong,
            vai_tro_ky=XuLy.VAI_TRO_KY_CHINH,
            trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
        )

        self.client.force_login(hieu_truong.user)
        response = self.client.post(
            reverse("duyet_van_ban_di_action", args=[van_ban_di.so_vb_di]),
            data={"action": "delegate", "delegate_id": pho_hieu_truong.pk},
        )

        self.assertEqual(response.status_code, 200)
        current_record = XuLy.objects.get(ma_vb_di=van_ban_di, ma_gv=hieu_truong)
        delegated_record = XuLy.objects.get(ma_vb_di=van_ban_di, ma_gv=pho_hieu_truong)
        self.assertEqual(current_record.trang_thai_ky, XuLy.TRANG_THAI_DA_UY_QUYEN)
        self.assertIsNotNone(current_record.thoi_gian_ky)
        self.assertEqual(delegated_record.vai_tro_ky, XuLy.VAI_TRO_KY_THAY)
        self.assertEqual(delegated_record.trang_thai_ky, XuLy.TRANG_THAI_CHO_DUYET)

    def test_hoan_thanh_chinh_sua_van_ban_updates_type_summary_and_draft(self):
        loai_moi = LoaiVanBan.objects.create(ten_loai_vb="Thong bao sua", ten_viet_tat="TB")
        van_ban_di = self.tao_van_ban_cho_duyet()
        self.client.post(
            reverse("duyet_van_ban_di_action", args=[van_ban_di.so_vb_di]),
            data={"action": "request_revision", "yc_chinh_sua": "Sua lai trich yeu va file."},
        )

        self.client.force_login(self.nguoi_tao.user)
        response = self.client.post(
            reverse("hoan_thanh_chinh_sua_van_ban", args=[van_ban_di.so_vb_di]),
            data={
                "ma_loai_vb": loai_moi.pk,
                "trich_yeu": "Trich yeu da duoc chinh sua",
                "ban_du_thao": SimpleUploadedFile(
                    "du-thao-da-sua.pdf",
                    b"%PDF-1.4 revised draft",
                    content_type="application/pdf",
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        van_ban_di.refresh_from_db()
        nhat_ky = NhatKyVanBan.objects.get(ma_vb_di=van_ban_di)
        xu_ly = XuLy.objects.get(ma_vb_di=van_ban_di, ma_gv=self.nguoi_duyet)
        self.assertEqual(van_ban_di.ma_loai_vb, loai_moi)
        self.assertEqual(van_ban_di.trich_yeu, "Trich yeu da duoc chinh sua")
        self.assertEqual(van_ban_di.trang_thai_vb_di, VanBanDi.TrangThai.CHO_DUYET)
        self.assertTrue(van_ban_di.ban_du_thao.name.endswith("du-thao-da-sua.pdf"))
        self.assertEqual(nhat_ky.trang_thai, NhatKyVanBan.TrangThai.DA_CHINH_SUA)
        self.assertEqual(xu_ly.trang_thai_ky, XuLy.TRANG_THAI_CHO_DUYET)

    def test_hoan_thanh_chinh_sua_van_ban_updates_summary_without_reuploading_file(self):
        loai_moi = LoaiVanBan.objects.create(ten_loai_vb="Loai khong tai lai file", ten_viet_tat="LKF")
        van_ban_di = self.tao_van_ban_cho_duyet()
        ten_file_cu = van_ban_di.ban_du_thao.name
        self.client.post(
            reverse("duyet_van_ban_di_action", args=[van_ban_di.so_vb_di]),
            data={"action": "request_revision", "yc_chinh_sua": "Chi sua trich yeu."},
        )

        self.client.force_login(self.nguoi_tao.user)
        response = self.client.post(
            reverse("hoan_thanh_chinh_sua_van_ban", args=[van_ban_di.so_vb_di]),
            data={
                "ma_loai_vb": loai_moi.pk,
                "trich_yeu": "Trich yeu chi sua noi dung",
            },
        )

        self.assertEqual(response.status_code, 200)
        van_ban_di.refresh_from_db()
        self.assertEqual(van_ban_di.trich_yeu, "Trich yeu chi sua noi dung")
        self.assertEqual(van_ban_di.ma_loai_vb, loai_moi)
        self.assertEqual(van_ban_di.ban_du_thao.name, ten_file_cu)

    def test_duyet_van_ban_action_forward_from_to_truong_to_hieu_truong(self):
        nhom_bgh = Group.objects.create(name="Ban giam hieu forward")
        vai_tro_hieu_truong = VaiTro.objects.create(ten_vai_tro="Hieu truong", nhom_quyen=nhom_bgh)
        hieu_truong = GiaoVien.objects.create(ma_gv="GVHT7777", ho_ten="Hieu Truong Forward")
        set_giao_vien_roles(hieu_truong, vai_tro_hieu_truong)
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban hai cap can trinh duyet",
            nguoi_ky=hieu_truong,
            ngay_ky="2026-03-20",
            noi_nhan="Phong chuyen mon",
            ban_du_thao=SimpleUploadedFile("hai-cap.pdf", b"%PDF-1.4 forward", content_type="application/pdf"),
            trang_thai_vb_di="Cho duyet",
            ngay_ban_hanh="2026-03-21",
            ma_muc_do=self.muc_do,
            so_ky_hieu="77/KH-THPTND",
        )
        XuLy.objects.create(
            ma_vb_di=van_ban_di,
            ma_gv=self.nguoi_duyet,
            vai_tro_ky=XuLy.VAI_TRO_KY_NHAY,
            trang_thai_ky=XuLy.TRANG_THAI_CHO_DUYET,
        )

        response = self.client.post(
            reverse("duyet_van_ban_di_action", args=[van_ban_di.so_vb_di]),
            data={"action": "forward"},
        )

        self.assertEqual(response.status_code, 200)
        van_ban_di.refresh_from_db()
        to_truong_record = XuLy.objects.get(ma_vb_di=van_ban_di, ma_gv=self.nguoi_duyet)
        hieu_truong_record = XuLy.objects.get(ma_vb_di=van_ban_di, ma_gv=hieu_truong)
        self.assertEqual(to_truong_record.trang_thai_ky, XuLy.TRANG_THAI_DA_DUYET)
        self.assertEqual(hieu_truong_record.vai_tro_ky, XuLy.VAI_TRO_KY_CHINH)
        self.assertEqual(hieu_truong_record.trang_thai_ky, XuLy.TRANG_THAI_CHO_DUYET)
        self.assertEqual(van_ban_di.trang_thai_vb_di, "Cho duyet")

    def test_get_document_signers_display_returns_approved_signers_with_roles(self):
        van_ban_di = self.tao_van_ban_cho_duyet()
        hieu_truong = GiaoVien.objects.create(ma_gv="GVHT6666", ho_ten="Hieu Truong Signed")
        XuLy.objects.filter(ma_vb_di=van_ban_di, ma_gv=self.nguoi_duyet).update(
            vai_tro_ky=XuLy.VAI_TRO_KY_NHAY,
            trang_thai_ky=XuLy.TRANG_THAI_DA_DUYET,
            thoi_gian_ky=timezone.now(),
        )
        XuLy.objects.create(
            ma_vb_di=van_ban_di,
            ma_gv=hieu_truong,
            vai_tro_ky=XuLy.VAI_TRO_KY_CHINH,
            trang_thai_ky=XuLy.TRANG_THAI_DA_DUYET,
            thoi_gian_ky=timezone.now(),
        )
        van_ban_di.trang_thai_vb_di = VanBanDi.TrangThai.DA_HOAN_THANH
        van_ban_di.save(update_fields=["trang_thai_vb_di"])

        display = get_document_signers_display(VanBanDi.objects.prefetch_related("xu_lys__ma_gv").get(pk=van_ban_di.pk))

        self.assertEqual(display, "Nguoi Duyet (Ky nhay), Hieu Truong Signed (Ky chinh)")

    def test_get_document_signers_display_returns_blank_until_document_is_published(self):
        van_ban_di = self.tao_van_ban_cho_duyet()
        XuLy.objects.filter(ma_vb_di=van_ban_di, ma_gv=self.nguoi_duyet).update(
            trang_thai_ky=XuLy.TRANG_THAI_DA_DUYET,
            thoi_gian_ky=timezone.now(),
        )

        display = get_document_signers_display(VanBanDi.objects.prefetch_related("xu_lys__ma_gv").get(pk=van_ban_di.pk))

        self.assertEqual(display, "")

    def test_can_phan_cong_view_returns_pending_incoming_and_outgoing_documents(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="25/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban den can phan cong",
            file_van_ban=SimpleUploadedFile("van-ban-den.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban di can phan cong",
            nguoi_ky=self.nguoi_duyet,
            ngay_ky="2026-03-22",
            noi_nhan="Phong chuyen mon",
            ban_du_thao=SimpleUploadedFile("du-thao-can-phan-cong.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            ban_chinh_thuc=SimpleUploadedFile(
                "ban-chinh-thuc.pdf",
                b"%PDF-1.4 official",
                content_type="application/pdf",
            ),
            trang_thai_vb_di=VanBanDi.TrangThai.DA_DANG_KY,
            ngay_ban_hanh="2026-03-23",
            ma_muc_do=self.muc_do,
            so_ky_hieu="03/KH-THPTND",
        )
        PhanCongXuLy.objects.create(
            so_vb_di=van_ban_di,
            nguoi_xu_ly=self.nguoi_duyet,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Cho phan cong van ban",
            thoi_han="2026-03-23",
            trang_thai_xl=PhanCongXuLy.TrangThaiXuLy.CHO_XU_LY,
        )
        van_ban_di.da_gui_phan_cong = True
        van_ban_di.save(update_fields=["da_gui_phan_cong"])

        response = self.client.get(reverse("can_phan_cong"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["documents"]), 2)
        self.assertEqual({item["record_id"] for item in response.context["documents"]}, {van_ban_den.so_vb_den, van_ban_di.so_vb_di})

    def test_luu_phan_cong_xu_ly_view_creates_assignments_for_incoming_document(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="26/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban den de phan cong",
            file_van_ban=SimpleUploadedFile("incoming-assign.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )

        response = self.client.post(
            reverse("luu_phan_cong_xu_ly"),
            data={
                "loai": "den",
                "record_id": van_ban_den.so_vb_den,
                "assignment_payload": json.dumps(
                    [
                        {"id": self.nguoi_tao.pk, "instruction": "Xu ly va bao cao cap 1."},
                        {"id": self.nguoi_khac.pk, "instruction": "Tong hop va phan hoi cap 2."},
                    ]
                ),
                "thoi_han": "2026-03-31",
            },
        )

        self.assertEqual(response.status_code, 200)
        van_ban_den.refresh_from_db()
        self.assertEqual(van_ban_den.trang_thai_vb_den, "Cho xu ly")
        self.assertEqual(PhanCongXuLy.objects.filter(so_vb_den=van_ban_den).count(), 2)
        self.assertEqual(
            set(PhanCongXuLy.objects.filter(so_vb_den=van_ban_den).values_list("nguoi_phan_cong_id", flat=True)),
            {self.nguoi_duyet.pk},
        )
        self.assertEqual(
            {
                assignment.nguoi_xu_ly_id: assignment.noi_dung_cd
                for assignment in PhanCongXuLy.objects.filter(so_vb_den=van_ban_den)
            },
            {
                self.nguoi_tao.pk: "Xu ly va bao cao cap 1.",
                self.nguoi_khac.pk: "Tong hop va phan hoi cap 2.",
            },
        )

    def test_luu_phan_cong_xu_ly_view_creates_assignments_for_outgoing_document(self):
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban di de phan cong",
            nguoi_ky=self.nguoi_duyet,
            ngay_ky="2026-03-22",
            noi_nhan="Phong chuyen mon",
            ban_du_thao=SimpleUploadedFile("draft-assign.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            ban_chinh_thuc=SimpleUploadedFile("official-assign.pdf", b"%PDF-1.4 official", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.DA_DANG_KY,
            ngay_ban_hanh="2026-03-23",
            ma_muc_do=self.muc_do,
            so_ky_hieu="04/KH-THPTND",
        )
        PhanCongXuLy.objects.create(
            so_vb_di=van_ban_di,
            nguoi_xu_ly=self.nguoi_duyet,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Cho phan cong van ban",
            thoi_han="2026-03-23",
            trang_thai_xl=PhanCongXuLy.TrangThaiXuLy.CHO_XU_LY,
        )
        van_ban_di.da_gui_phan_cong = True
        van_ban_di.save(update_fields=["da_gui_phan_cong"])

        response = self.client.post(
            reverse("luu_phan_cong_xu_ly"),
            data={
                "loai": "di",
                "record_id": van_ban_di.so_vb_di,
                "assignment_payload": json.dumps(
                    [
                        {"id": self.nguoi_tao.pk, "instruction": "Xu ly ngay."},
                    ]
                ),
                "thoi_han": "2026-03-30",
            },
        )

        self.assertEqual(response.status_code, 200)
        van_ban_di.refresh_from_db()
        self.assertEqual(van_ban_di.trang_thai_vb_di, VanBanDi.TrangThai.DA_DANG_KY)
        self.assertEqual(PhanCongXuLy.objects.filter(so_vb_di=van_ban_di).count(), 1)
        self.assertEqual(PhanCongXuLy.objects.get(so_vb_di=van_ban_di).nguoi_phan_cong, self.nguoi_duyet)
        self.assertEqual(PhanCongXuLy.objects.get(so_vb_di=van_ban_di).noi_dung_cd, "Xu ly ngay.")

    def test_luu_phan_cong_xu_ly_view_requires_instruction_for_each_selected_person(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="26A/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban den thieu noi dung chi dao",
            file_van_ban=SimpleUploadedFile("incoming-invalid.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )

        response = self.client.post(
            reverse("luu_phan_cong_xu_ly"),
            data={
                "loai": "den",
                "record_id": van_ban_den.so_vb_den,
                "assignment_payload": json.dumps(
                    [
                        {"id": self.nguoi_tao.pk, "instruction": "Xu ly ho so."},
                        {"id": self.nguoi_khac.pk, "instruction": ""},
                    ]
                ),
                "thoi_han": "2026-03-31",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["message"],
            "Vui long nhap noi dung chi dao cho tung nguoi xu ly.",
        )
        self.assertFalse(PhanCongXuLy.objects.filter(so_vb_den=van_ban_den).exists())

    def test_da_phan_cong_view_only_returns_assigned_documents(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="27/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban den da phan cong",
            file_van_ban=SimpleUploadedFile("incoming-done.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Da phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban di da phan cong",
            nguoi_ky=self.nguoi_duyet,
            ngay_ky="2026-03-22",
            noi_nhan="Phong chuyen mon",
            ban_du_thao=SimpleUploadedFile("draft-done.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            ban_chinh_thuc=SimpleUploadedFile("official-done.pdf", b"%PDF-1.4 official", content_type="application/pdf"),
            trang_thai_vb_di="Da phan cong",
            ngay_ban_hanh="2026-03-23",
            ma_muc_do=self.muc_do,
            so_ky_hieu="05/KH-THPTND",
        )
        VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="28/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban den chua phan cong",
            file_van_ban=SimpleUploadedFile("incoming-pending.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Cho phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_den,
            nguoi_xu_ly=self.nguoi_tao,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Xu ly van ban den.",
            thoi_han="2026-03-31",
            trang_thai_xl="Dang xu ly",
        )
        PhanCongXuLy.objects.create(
            so_vb_di=van_ban_di,
            nguoi_xu_ly=self.nguoi_khac,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Xu ly van ban di.",
            thoi_han="2026-03-31",
            trang_thai_xl="Dang xu ly",
        )

        response = self.client.get(reverse("da_phan_cong"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["assignment_list_mode"], "assigned")
        self.assertEqual({item["record_id"] for item in response.context["documents"]}, {van_ban_den.so_vb_den, van_ban_di.so_vb_di})

    def test_da_phan_cong_view_hides_documents_assigned_by_other_users(self):
        van_ban_cua_minh = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="30/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban cua minh",
            file_van_ban=SimpleUploadedFile("mine.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Da phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        van_ban_nguoi_khac = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="31/SGD",
            ngay_ky="2026-03-20",
            trich_yeu="Van ban nguoi khac phan cong",
            file_van_ban=SimpleUploadedFile("other.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Da phan cong",
            ngay_nhan="2026-03-21",
            ma_muc_do=self.muc_do,
        )
        nguoi_phan_cong_khac = GiaoVien.objects.create(ma_gv="GV100099", ho_ten="Nguoi Phan Cong Khac")
        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_cua_minh,
            nguoi_xu_ly=self.nguoi_tao,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Cua minh",
            thoi_han="2026-03-31",
            trang_thai_xl="Dang xu ly",
        )
        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_nguoi_khac,
            nguoi_xu_ly=self.nguoi_tao,
            nguoi_phan_cong=nguoi_phan_cong_khac,
            noi_dung_cd="Cua nguoi khac",
            thoi_han="2026-03-31",
            trang_thai_xl="Dang xu ly",
        )

        response = self.client.get(reverse("da_phan_cong"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["record_id"] for item in response.context["documents"]}, {van_ban_cua_minh.so_vb_den})

    def test_theo_doi_tien_do_view_only_returns_documents_assigned_by_current_user(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="29/SGD",
            ngay_ky="2026-03-24",
            trich_yeu="Van ban den theo doi tien do",
            file_van_ban=SimpleUploadedFile("incoming-progress.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Da phan cong",
            ngay_nhan="2026-03-25",
            ma_muc_do=self.muc_do,
        )
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.nguoi_tao,
            trich_yeu="Van ban di theo doi tien do",
            nguoi_ky=self.nguoi_duyet,
            ngay_ky="2026-03-25",
            noi_nhan="Phong chuyen mon",
            ban_du_thao=SimpleUploadedFile("draft-progress.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            ban_chinh_thuc=SimpleUploadedFile("official-progress.pdf", b"%PDF-1.4 official", content_type="application/pdf"),
            trang_thai_vb_di="Da phan cong",
            ngay_ban_hanh="2026-03-26",
            ma_muc_do=self.muc_do,
            so_ky_hieu="06/KH-THPTND",
        )
        van_ban_khac = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="Phong GD",
            so_ky_hieu="30/PGD",
            ngay_ky="2026-03-24",
            trich_yeu="Van ban cua nguoi khac phan cong",
            file_van_ban=SimpleUploadedFile("incoming-other.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Da phan cong",
            ngay_nhan="2026-03-25",
            ma_muc_do=self.muc_do,
        )

        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_den,
            nguoi_xu_ly=self.nguoi_tao,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Tiep nhan va xu ly.",
            thoi_han="2026-03-31",
            trang_thai_xl="Chua xu ly",
        )
        PhanCongXuLy.objects.create(
            so_vb_di=van_ban_di,
            nguoi_xu_ly=self.nguoi_khac,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Dang xu ly van ban di.",
            thoi_han="2026-04-01",
            trang_thai_xl="Dang xu ly",
        )
        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_khac,
            nguoi_xu_ly=self.nguoi_tao,
            nguoi_phan_cong=self.nguoi_khac,
            noi_dung_cd="Khong thuoc nguoi dang nhap.",
            thoi_han="2026-03-31",
            trang_thai_xl="Da hoan thanh",
        )

        response = self.client.get(reverse("theo_doi_tien_do"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["documents"]), 2)
        self.assertEqual(
            {item["record_id"] for item in response.context["documents"]},
            {van_ban_den.so_vb_den, van_ban_di.so_vb_di},
        )
        self.assertNotContains(response, van_ban_khac.so_vb_den)

    def test_theo_doi_tien_do_view_builds_detail_rows_and_aggregate_status(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="31/SGD",
            ngay_ky="2026-03-24",
            trich_yeu="Van ban den co nhieu nguoi xu ly",
            file_van_ban=SimpleUploadedFile("incoming-many.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Da phan cong",
            ngay_nhan="2026-03-25",
            ma_muc_do=self.muc_do,
        )

        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_den,
            nguoi_xu_ly=self.nguoi_tao,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Tiep nhan ho so.",
            thoi_han="2026-03-31",
            trang_thai_xl="Chua xu ly",
        )
        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_den,
            nguoi_xu_ly=self.nguoi_khac,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Dang xu ly bao cao.",
            thoi_han="2026-04-02",
            trang_thai_xl="Dang xu ly",
        )

        response = self.client.get(reverse("theo_doi_tien_do"))

        self.assertEqual(response.status_code, 200)
        document = response.context["documents"][0]
        self.assertEqual(document["so_van_ban"], van_ban_den.so_vb_den)
        self.assertEqual(document["trang_thai_hien_thi"], "Dang xu ly")
        self.assertEqual(document["trang_thai_css_class"], "status-processing")
        self.assertEqual(len(document["details"]), 2)
        self.assertEqual({item["trang_thai"] for item in document["details"]}, {"Cho xu ly", "Dang xu ly"})

    def test_chi_tiet_tien_do_view_reads_assignments_from_phan_cong_xu_ly(self):
        van_ban_den = VanBanDen.objects.create(
            ma_loai_vb=self.loai_van_ban,
            co_quan_ban_hanh="So GD&DT",
            so_ky_hieu="32/SGD",
            ngay_ky="2026-03-24",
            trich_yeu="Van ban den lay chi tiet tu bang phan cong",
            file_van_ban=SimpleUploadedFile("incoming-detail.pdf", b"%PDF-1.4 incoming", content_type="application/pdf"),
            trang_thai_vb_den="Da phan cong",
            ngay_nhan="2026-03-25",
            ma_muc_do=self.muc_do,
        )

        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_den,
            nguoi_xu_ly=self.nguoi_tao,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Xu ly muc 1.",
            thoi_han="2026-03-31",
            trang_thai_xl="Chua xu ly",
        )
        PhanCongXuLy.objects.create(
            so_vb_den=van_ban_den,
            nguoi_xu_ly=self.nguoi_khac,
            nguoi_phan_cong=self.nguoi_duyet,
            noi_dung_cd="Xu ly muc 2.",
            thoi_han="2026-04-02",
            trang_thai_xl="Dang xu ly",
        )

        response = self.client.get(
            reverse("chi_tiet_tien_do"),
            data={"loai": "den", "record_id": van_ban_den.so_vb_den},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["success"])
        self.assertEqual(len(payload["details"]), 2)
        self.assertEqual(
            {item["nguoi_xu_ly"] for item in payload["details"]},
            {self.nguoi_tao.ho_ten, self.nguoi_khac.ho_ten},
        )
        self.assertEqual(
            {item["noi_dung_cd"] for item in payload["details"]},
            {"Xu ly muc 1.", "Xu ly muc 2."},
        )


class QuanLyTaiKhoanViewTests(TestCase):
    def setUp(self):
        self.nhom_van_thu = Group.objects.create(name="Van thu")
        self.nhom_bgh = Group.objects.create(name="Ban giam hieu")
        self.nhom_to_chuc = Group.objects.create(name="Nguoi dung to chuc trong truong")
        self.vai_tro_van_thu = VaiTro.objects.create(ten_vai_tro="Van thu", nhom_quyen=self.nhom_van_thu)
        self.vai_tro_bgh = VaiTro.objects.create(ten_vai_tro="Pho hieu truong", nhom_quyen=self.nhom_bgh)
        self.vai_tro_to_chuc = VaiTro.objects.create(
            ten_vai_tro="Nguoi dung to chuc",
            nhom_quyen=self.nhom_to_chuc,
        )
        self.van_thu = GiaoVien.objects.create(ma_gv="GVVT888", ho_ten="Nguoi Van Thu")
        self.giao_vien = GiaoVien.objects.create(ma_gv="GV000888", ho_ten="Nguyen Van Giao Vien")
        set_giao_vien_roles(self.van_thu, self.vai_tro_van_thu)
        set_giao_vien_roles(self.giao_vien, self.vai_tro_bgh)
        self.client.force_login(self.van_thu.user)

    def test_van_thu_can_xem_danh_sach_nguoi_dung(self):
        response = self.client.get(reverse("danh_sach_nguoi_dung"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Danh sách người dùng")
        self.assertContains(response, self.giao_vien.ho_ten)

    def test_cap_nhat_tai_khoan_giao_vien_co_the_khoa_tai_khoan(self):
        response = self.client.post(
            reverse("cap_nhat_tai_khoan_giao_vien", args=[self.giao_vien.ma_gv]),
            data={
                "ho_ten": self.giao_vien.ho_ten,
                "chuc_vu": "Pho hieu truong",
                "trang_thai_tk": GiaoVien.TrangThaiTaiKhoan.NGUNG_HOAT_DONG,
                "ma_to": "",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.giao_vien.refresh_from_db()
        self.assertEqual(self.giao_vien.trang_thai_tk, GiaoVien.TrangThaiTaiKhoan.NGUNG_HOAT_DONG)
        self.assertFalse(self.giao_vien.user.is_active)

        self.client.logout()
        locked_login_response = self.client.post(
            reverse("login"),
            data={"username": self.giao_vien.ma_gv, "password": "giaovien123"},
            follow=True,
        )
        self.assertContains(locked_login_response, "Tai khoan da bi khoa.")

    def test_them_giao_vien_view_tao_giao_vien_moi(self):
        response = self.client.post(
            reverse("them_giao_vien"),
            data={
                "ma_gv": "GV000999",
                "ho_ten": "Giao Vien Moi",
                "chuc_vu": "Giao vien",
                "ma_to": "",
                "trang_thai_tk": GiaoVien.TrangThaiTaiKhoan.HOAT_DONG,
            },
        )

        self.assertEqual(response.status_code, 200)
        giao_vien_moi = GiaoVien.objects.get(ma_gv="GV000999")
        self.assertEqual(giao_vien_moi.ho_ten, "Giao Vien Moi")
        self.assertTrue(giao_vien_moi.user.check_password("giaovien123"))
        self.assertIn("Giao Vien Moi", response.json()["row_html"])

    def test_reset_mat_khau_giao_vien_updates_user_password(self):
        response = self.client.post(
            reverse("reset_mat_khau_giao_vien", args=[self.giao_vien.ma_gv]),
            data={"password": "MatKhauMoi123", "confirm_password": "MatKhauMoi123"},
        )

        self.assertEqual(response.status_code, 200)
        self.giao_vien.refresh_from_db()
        self.assertTrue(self.giao_vien.user.check_password("MatKhauMoi123"))

    def test_phan_quyen_nguoi_dung_cap_nhat_nhom_quyen(self):
        response = self.client.post(
            reverse("cap_nhat_phan_quyen_nguoi_dung", args=[self.giao_vien.ma_gv]),
            data={"nhom_quyen": [self.nhom_to_chuc.pk]},
        )

        self.assertEqual(response.status_code, 200)
        self.giao_vien.refresh_from_db()
        self.assertEqual(
            list(self.giao_vien.user.groups.values_list("name", flat=True)),
            ["Nguoi dung to chuc trong truong"],
        )


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class NoiNhanAndExternalPublishTests(TestCase):
    def setUp(self):
        self.nhom_van_thu = Group.objects.create(name="Van thu")
        self.vai_tro_van_thu = VaiTro.objects.create(ten_vai_tro="Van thu", nhom_quyen=self.nhom_van_thu)
        self.van_thu = GiaoVien.objects.create(ma_gv="GVVT900", ho_ten="Van Thu Ngoai")
        set_giao_vien_roles(self.van_thu, self.vai_tro_van_thu)
        self.loai_van_ban = LoaiVanBan.objects.create(ten_loai_vb="Cong van ngoai", ten_viet_tat="CV")
        self.muc_do = MucDoUuTien.objects.create(muc_do="Thuong")
        self.client.force_login(self.van_thu.user)

    def test_them_noi_nhan_view_creates_recipient(self):
        response = self.client.post(
            reverse("them_noi_nhan"),
            data={
                "ten_noi_nhan": "So Giao duc",
                "dia_chi": "1 Nguyen Trai",
                "so_dien_thoai": "0909000001",
                "gmail": "sgd@example.com",
                "thong_tin_khac": "Noi nhan cap tren",
            },
        )

        self.assertEqual(response.status_code, 200)
        recipient = NoiNhan.objects.get()
        self.assertEqual(recipient.ten_noi_nhan, "So Giao duc")
        self.assertIn("So Giao duc", response.json()["row_html"])

    def test_danh_sach_noi_nhan_view_renders_management_screen(self):
        NoiNhan.objects.create(
            ten_noi_nhan="So Giao duc",
            dia_chi="1 Nguyen Trai",
            so_dien_thoai="0909000001",
            gmail="sgd@example.com",
        )

        response = self.client.get(reverse("danh_sach_noi_nhan"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Danh sach noi nhan")
        self.assertContains(response, "So Giao duc")

    def test_phat_hanh_ben_ngoai_creates_multiple_records_for_selected_recipients(self):
        recipient_one = NoiNhan.objects.create(ten_noi_nhan="So Giao duc")
        recipient_two = NoiNhan.objects.create(ten_noi_nhan="Phong Giao duc")
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.van_thu,
            trich_yeu="Van ban phat hanh ben ngoai",
            nguoi_ky=self.van_thu,
            ngay_ky="2026-04-10",
            noi_nhan="So Giao duc; Phong Giao duc",
            ban_du_thao=SimpleUploadedFile("draft-outbound.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            ban_chinh_thuc=SimpleUploadedFile("official-outbound.pdf", b"%PDF-1.4 official", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.DA_DANG_KY,
            ngay_ban_hanh="2026-04-11",
            ma_muc_do=self.muc_do,
            so_ky_hieu="01/CV-THPTND",
        )

        response = self.client.post(
            reverse("phat_hanh_ben_ngoai_van_ban_di", args=[van_ban_di.so_vb_di]),
            data={"noi_nhan_ids[]": [recipient_one.pk, recipient_two.pk]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LuanChuyenBenNgoai.objects.filter(ma_vb_di=van_ban_di).count(), 2)
        van_ban_di.refresh_from_db()
        self.assertTrue(van_ban_di.da_phat_hanh_ben_ngoai)
        self.assertEqual(
            set(LuanChuyenBenNgoai.objects.filter(ma_vb_di=van_ban_di).values_list("ma_noi_nhan_id", flat=True)),
            {recipient_one.pk, recipient_two.pk},
        )
        self.assertEqual(
            set(LuanChuyenBenNgoai.objects.filter(ma_vb_di=van_ban_di).values_list("nguoi_thuc_hien_id", flat=True)),
            {self.van_thu.pk},
        )

    def test_external_published_view_lists_document_and_recipient_details(self):
        recipient = NoiNhan.objects.create(
            ten_noi_nhan="Uy ban nhan dan",
            dia_chi="2 Le Loi",
            so_dien_thoai="0909000002",
            gmail="ubnd@example.com",
            thong_tin_khac="Tiep nhan van ban hanh chinh",
        )
        van_ban_di = VanBanDi.objects.create(
            ma_loai_vb=self.loai_van_ban,
            nguoi_tao=self.van_thu,
            trich_yeu="Van ban da phat hanh ben ngoai",
            nguoi_ky=self.van_thu,
            ngay_ky="2026-04-10",
            noi_nhan="Uy ban nhan dan",
            ban_du_thao=SimpleUploadedFile("draft-external.pdf", b"%PDF-1.4 draft", content_type="application/pdf"),
            ban_chinh_thuc=SimpleUploadedFile("official-external.pdf", b"%PDF-1.4 official", content_type="application/pdf"),
            trang_thai_vb_di=VanBanDi.TrangThai.DA_DANG_KY,
            ngay_ban_hanh="2026-04-11",
            ma_muc_do=self.muc_do,
            so_ky_hieu="02/CV-THPTND",
        )
        LuanChuyenBenNgoai.objects.create(
            ma_vb_di=van_ban_di,
            ma_noi_nhan=recipient,
            nguoi_thuc_hien=self.van_thu,
            trang_thai_gui=LuanChuyenBenNgoai.TrangThaiGui.DA_GUI,
        )
        van_ban_di.da_phat_hanh_ben_ngoai = True
        van_ban_di.save(update_fields=["da_phat_hanh_ben_ngoai"])

        response = self.client.get(reverse("van_ban_phat_hanh_ben_ngoai"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, van_ban_di.so_vb_di)
        self.assertContains(response, "Uy ban nhan dan")
        self.assertContains(response, "CHI TIET PHAT HANH BEN NGOAI")
