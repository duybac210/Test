from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max, Q
from django.utils import timezone
import unicodedata


def generate_prefixed_code(model_class, field_name, prefix, width):
    last_object = model_class.objects.order_by(f"-{field_name}").first()
    last_value = getattr(last_object, field_name, "") if last_object else ""

    try:
        last_number = int(last_value.replace(prefix, ""))
    except ValueError:
        last_number = 0

    while True:
        last_number += 1
        candidate = f"{prefix}{last_number:0{width}d}"
        if not model_class.objects.filter(**{field_name: candidate}).exists():
            return candidate


def _get_year_for_registration(document):
    return (document.ngay_ban_hanh or timezone.localdate()).year


def _get_type_code_for_registration(document):
    code = (getattr(document.ma_loai_vb, "ten_viet_tat", "") or "").strip()
    if not code:
        raise ValueError("Loai van ban chua co ten viet tat de cap so.")
    return code


def _get_org_code_for_registration():
    return getattr(settings, "DON_VI_CAP_SO_VAN_BAN", "THPTND").strip() or "THPTND"


def generate_so_thu_tu(van_ban_di_model, document):
    year = _get_year_for_registration(document)
    max_serial = (
        van_ban_di_model.objects.exclude(pk=document.pk)
        .filter(
            ma_loai_vb=document.ma_loai_vb,
            ngay_ban_hanh__year=year,
        )
        .aggregate(max_so_thu_tu=Max("so_thu_tu"))
        .get("max_so_thu_tu")
    )
    return (max_serial or 0) + 1


def build_so_ky_hieu(document, so_thu_tu):
    return f"{so_thu_tu:02d}/{_get_type_code_for_registration(document)}-{_get_org_code_for_registration()}"


def generate_so_ky_hieu(van_ban_di_model, document):
    so_thu_tu = generate_so_thu_tu(van_ban_di_model, document)
    return build_so_ky_hieu(document, so_thu_tu)


def generate_registration_number(van_ban_di_model, document):
    so_thu_tu = generate_so_thu_tu(van_ban_di_model, document)
    return so_thu_tu, build_so_ky_hieu(document, so_thu_tu)


DEFAULT_GIAO_VIEN_PASSWORD = "giaovien123"


class ToChuyenMon(models.Model):
    ma_to = models.CharField(max_length=10, primary_key=True, blank=True)
    ten_to = models.CharField(max_length=100, unique=True)
    to_truong = models.OneToOneField(
        "GiaoVien",
        on_delete=models.PROTECT,
        related_name="to_chuyen_mon_phu_trach",
    )

    class Meta:
        db_table = "ToChuyenMon"
        verbose_name = "Tổ chuyên môn"
        verbose_name_plural = "Tổ chuyên môn"
        ordering = ["ten_to"]

    def __str__(self):
        return self.ten_to

    def clean(self):
        super().clean()
        if not self.to_truong_id:
            raise ValidationError({"to_truong": "Vui long chon to truong."})

        existing_department = ToChuyenMon.objects.exclude(pk=self.pk).filter(to_truong_id=self.to_truong_id).first()
        if existing_department is not None:
            raise ValidationError({"to_truong": "Moi giao vien chi duoc lam to truong cua mot to chuyen mon."})
        current_position = (
            unicodedata.normalize("NFD", self.to_truong.chuc_vu or "")
            .encode("ascii", "ignore")
            .decode("ascii")
            .strip()
            .lower()
        )
        if current_position and current_position != "to truong":
            raise ValidationError(
                {"to_truong": "To truong khong duoc kiem nhiem chuc vu khac ngoai To truong."}
            )

    def save(self, *args, **kwargs):
        if not self.ma_to:
            with transaction.atomic():
                self.ma_to = generate_prefixed_code(ToChuyenMon, "ma_to", "TCM", 7)
                self.full_clean()
                super().save(*args, **kwargs)
                return
        self.full_clean()
        super().save(*args, **kwargs)


class GiaoVien(models.Model):
    class TrangThaiTaiKhoan(models.TextChoices):
        HOAT_DONG = "Hoat dong", "Hoạt động"
        DA_KHOA = "Da khoa", "Đã khóa"
        NGUNG_HOAT_DONG = "Ngung hoat dong", "Ngưng hoạt động"
        VO_HIEU_HOA = "Vo hieu hoa", "Vô hiệu hóa"

    ma_gv = models.CharField(max_length=10, primary_key=True, blank=True)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="ho_so_giao_vien",
        null=True,
        blank=True,
    )
    ho_ten = models.CharField(max_length=150)
    chuc_vu = models.CharField(max_length=100, blank=True, default="")
    ma_to = models.ForeignKey(
        ToChuyenMon,
        on_delete=models.PROTECT,
        related_name="giao_viens",
        null=True,
        blank=True,
    )
    trang_thai_tk = models.CharField(max_length=50, default="Hoạt động")

    class Meta:
        db_table = "GiaoVien"
        verbose_name = "Giáo viên"
        verbose_name_plural = "Giáo viên"
        ordering = ["ho_ten"]

    def __str__(self):
        return f"{self.ma_gv} - {self.ho_ten}"

    @property
    def ten_vai_tro_hien_thi(self):
        return (self.chuc_vu or "").strip()

    @property
    def ten_nhom_quyen_hien_thi(self):
        if not self.user_id:
            return ""
        return ", ".join(self.user.groups.order_by("name").values_list("name", flat=True))

    def clean(self):
        super().clean()
        if not self.ma_gv:
            return
        user_model = get_user_model()
        duplicated_user = user_model.objects.filter(username=self.ma_gv).exclude(pk=self.user_id).exists()
        if duplicated_user:
            raise ValidationError(
                {"ma_gv": "Mã giáo viên đã được dùng làm username của tài khoản khác."}
            )

    def is_active_account(self):
        trang_thai = (self.trang_thai_tk or "").strip().lower()
        return trang_thai not in {
            self.TrangThaiTaiKhoan.DA_KHOA.lower(),
            self.TrangThaiTaiKhoan.NGUNG_HOAT_DONG.lower(),
            self.TrangThaiTaiKhoan.VO_HIEU_HOA.lower(),
        }

    def ensure_user_account(self):
        user_model = get_user_model()
        user = self.user

        if user is None:
            user, created = user_model.objects.get_or_create(
                username=self.ma_gv,
                defaults={
                    "is_staff": True,
                    "is_active": self.is_active_account(),
                },
            )
            if created:
                user.set_password(DEFAULT_GIAO_VIEN_PASSWORD)
        else:
            user.username = self.ma_gv

        user.is_staff = True
        user.is_active = self.is_active_account()
        user.first_name = self.ho_ten
        user.save()
        self.user = user

    def save(self, *args, **kwargs):
        with transaction.atomic():
            if not self.ma_gv:
                self.ma_gv = generate_prefixed_code(GiaoVien, "ma_gv", "GV", 6)
            self.ensure_user_account()
            super().save(*args, **kwargs)



class LoaiVanBan(models.Model):
    AP_DUNG_CHOICES = (
        (0, "Van ban di"),
        (1, "Van ban den"),
        (2, "Ca hai"),
    )
    TWO_CAP_MOT_CAP = 0
    TWO_CAP_HAI_CAP = 1
    TWO_CAP_CHOICES = (
        (TWO_CAP_MOT_CAP, "1 cap"),
        (TWO_CAP_HAI_CAP, "2 cap"),
    )

    ma_loai_vb = models.CharField(max_length=10, primary_key=True, blank=True)
    ten_loai_vb = models.CharField(max_length=100, unique=True)
    ten_viet_tat = models.CharField(max_length=20, blank=True)
    ap_dung = models.IntegerField(choices=AP_DUNG_CHOICES, default=2)
    twocap = models.IntegerField(choices=TWO_CAP_CHOICES, default=TWO_CAP_MOT_CAP)

    class Meta:
        db_table = "LoaiVanBan"
        verbose_name = "Loại văn bản"
        verbose_name_plural = "Loại văn bản"
        ordering = ["ten_loai_vb"]

    def __str__(self):
        return self.ten_loai_vb

    def save(self, *args, **kwargs):
        if not self.ma_loai_vb:
            with transaction.atomic():
                self.ma_loai_vb = generate_prefixed_code(LoaiVanBan, "ma_loai_vb", "LVB", 7)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class MauVanBan(models.Model):
    class TrangThai(models.TextChoices):
        DANG_SU_DUNG = "Dang su dung", "Đang sử dụng"
        DUNG_SU_DUNG = "Dung su dung", "Dừng sử dụngg"
        DU_THAO = "Du thao", "Dự thảo"

    TRANG_THAI_DANG_SU_DUNG = TrangThai.DANG_SU_DUNG
    TRANG_THAI_DUNG_SU_DUNG = TrangThai.DUNG_SU_DUNG
    TRANG_THAI_DU_THAO = TrangThai.DU_THAO
    TRANG_THAI_CHOICES = TrangThai.choices

    ma_mau_vb = models.CharField(max_length=10, primary_key=True, blank=True)
    ngay_tao = models.DateField(default=timezone.localdate)
    ten_mau = models.CharField(max_length=100)
    ma_loai_vb = models.ForeignKey(
        LoaiVanBan,
        on_delete=models.PROTECT,
        related_name="mau_van_bans",
    )
    muc_dich = models.TextField(blank=True)
    file_mau = models.FileField(upload_to="mau_van_ban/")
    trang_thai = models.CharField(max_length=100, choices=TRANG_THAI_CHOICES, default=TRANG_THAI_DANG_SU_DUNG)

    class Meta:
        db_table = "MauVanBan"
        verbose_name = "Mẫu văn bản"
        verbose_name_plural = "Mẫu văn bản"
        ordering = ["ten_mau"]

    def __str__(self):
        return self.ten_mau

    def save(self, *args, **kwargs):
        if not self.ma_mau_vb:
            with transaction.atomic():
                self.ma_mau_vb = generate_prefixed_code(MauVanBan, "ma_mau_vb", "MVB", 7)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class MucDoUuTien(models.Model):
    ma_muc_do = models.CharField(max_length=10, primary_key=True, blank=True)
    muc_do = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = "Mucdouutien"
        verbose_name = "Mức độ ưu tiên"
        verbose_name_plural = "Mức độ ưu tiên"
        ordering = ["ma_muc_do"]

    def __str__(self):
        return self.muc_do

    def save(self, *args, **kwargs):
        if not self.ma_muc_do:
            with transaction.atomic():
                self.ma_muc_do = generate_prefixed_code(MucDoUuTien, "ma_muc_do", "MD", 8)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class NoiNhan(models.Model):
    ma_noi_nhan = models.CharField(max_length=10, primary_key=True, blank=True)
    ten_noi_nhan = models.CharField(max_length=200, unique=True)
    dia_chi = models.CharField(max_length=255, blank=True)
    so_dien_thoai = models.CharField(max_length=20, blank=True)
    gmail = models.EmailField(blank=True)
    thong_tin_khac = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "NoiNhan"
        ordering = ["ten_noi_nhan"]

    def __str__(self):
        return self.ten_noi_nhan

    def save(self, *args, **kwargs):
        if not self.ma_noi_nhan:
            with transaction.atomic():
                self.ma_noi_nhan = generate_prefixed_code(NoiNhan, "ma_noi_nhan", "NN", 8)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class VanBanDen(models.Model):
    class TrangThai(models.TextChoices):
        CHO_PHAN_CONG = "Cho phan cong", "Chờ phân công"
        CHO_XU_LY = "Cho xu ly", "Chờ xử lý"
        DA_HOAN_THANH = "Da hoan thanh", "Đã hoàn thành"
        DA_BAN_HANH = "Da ban hanh", "Đã ban hành"

    so_vb_den = models.CharField(max_length=10, primary_key=True, blank=True)
    ma_loai_vb = models.ForeignKey(
        LoaiVanBan,
        on_delete=models.PROTECT,
        related_name="van_ban_dens",
    )
    co_quan_ban_hanh = models.CharField(max_length=100)
    so_ky_hieu = models.CharField(max_length=15)
    ngay_ky = models.DateField()
    trich_yeu = models.CharField(max_length=500)
    file_van_ban = models.FileField(upload_to="van_ban_den/", null=True, blank=True)
    trang_thai_vb_den = models.CharField(max_length=100, default="Mới tiếp nhận")
    da_ban_hanh_noi_bo = models.BooleanField(default=False)
    ngay_nhan = models.DateField()
    ma_muc_do = models.ForeignKey(
        MucDoUuTien,
        on_delete=models.PROTECT,
        related_name="van_ban_dens",
    )

    class Meta:
        db_table = "VanBanDen"
        verbose_name = "Văn bản đến"
        verbose_name_plural = "Văn bản đến"
        ordering = ["-ngay_nhan", "-ngay_ky"]

    def __str__(self):
        return self.so_vb_den

    def save(self, *args, **kwargs):
        if not self.so_vb_den:
            with transaction.atomic():
                self.so_vb_den = generate_prefixed_code(VanBanDen, "so_vb_den", "VBD", 7)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)

    def get_file_attachments(self):
        return list(self.tep_dinh_kems.order_by("thu_tu", "ngay_tao", "ma_tep"))

    def get_primary_file(self):
        return self.file_van_ban


class VanBanDi(models.Model):
    class TrangThai(models.TextChoices):
        DU_THAO = "Du thao", "Dự thảo"
        CHO_DUYET = "Cho duyet", "Chờ duyệt"
        DANG_CHINH_SUA = "Dang chinh sua", "Đang chỉnh sửa"
        CHO_DANG_KY = "Cho dang ky", "Chờ đăng ký"
        DA_DANG_KY = "Da dang ky", "Đã đăng ký"
        CHO_LUAN_CHUYEN = "Cho luan chuyen", "Chờ luân chuyển"
        CHO_PHAN_CONG = "Cho phan cong", "Chờ phân công"
        DA_HOAN_THANH = "Da hoan thanh", "Đã hoàn thành"
        DA_BAN_HANH = "Da ban hanh", "Đã ban hành"

    so_vb_di = models.CharField(max_length=10, primary_key=True, blank=True)
    so_thu_tu = models.PositiveIntegerField(null=True, blank=True)
    so_ky_hieu = models.CharField(max_length=50)
    ma_loai_vb = models.ForeignKey(
        LoaiVanBan,
        on_delete=models.PROTECT,
        related_name="van_ban_dis",
    )
    nguoi_tao = models.ForeignKey(
        GiaoVien,
        on_delete=models.PROTECT,
        related_name="van_ban_da_tao",
    )
    trich_yeu = models.CharField(max_length=500)
    nguoi_ky = models.ForeignKey(
        GiaoVien,
        on_delete=models.PROTECT,
        related_name="van_ban_da_ky",
    )
    ngay_ky = models.DateField(null=True, blank=True)
    noi_nhan = models.CharField(max_length=100)
    ban_du_thao = models.FileField(upload_to="van_ban_di/du_thao/", null=True, blank=True)
    ban_chinh_thuc = models.FileField(
        upload_to="van_ban_di/chinh_thuc/",
        null=True,
        blank=True,
    )
    trang_thai_vb_di = models.CharField(max_length=50, default="Soạn thảo")
    da_phat_hanh_ben_ngoai = models.BooleanField(default=False)
    da_ban_hanh_noi_bo = models.BooleanField(default=False)
    da_gui_phan_cong = models.BooleanField(default=False)
    ngay_ban_hanh = models.DateField(null=True, blank=True)
    ma_muc_do = models.ForeignKey(
        MucDoUuTien,
        on_delete=models.PROTECT,
        related_name="van_ban_dis",
    )

    class Meta:
        db_table = "VanBanDi"
        verbose_name = "Văn bản đi"
        verbose_name_plural = "Văn bản đi"
        ordering = ["-ngay_ban_hanh", "-ngay_ky"]

    def __str__(self):
        return self.so_vb_di

    def save(self, *args, **kwargs):
        if not self.so_vb_di:
            with transaction.atomic():
                self.so_vb_di = generate_prefixed_code(VanBanDi, "so_vb_di", "VBO", 8)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)

    def get_file_attachments(self, loai_tep):
        return list(self.tep_dinh_kem_dis.filter(loai_tep=loai_tep).order_by("thu_tu", "ngay_tao", "ma_tep"))

    def get_draft_attachments(self):
        return self.get_file_attachments(TepDinhKemVanBanDi.LoaiTep.DU_THAO)

    def get_official_attachments(self):
        return self.get_file_attachments(TepDinhKemVanBanDi.LoaiTep.CHINH_THUC)

    def get_primary_draft_file(self):
        return self.ban_du_thao

    def get_primary_official_file(self):
        return self.ban_chinh_thuc


class TepDinhKemVanBanDen(models.Model):
    ma_tep = models.CharField(max_length=10, primary_key=True, blank=True)
    so_vb_den = models.ForeignKey(
        VanBanDen,
        on_delete=models.CASCADE,
        related_name="tep_dinh_kems",
    )
    tep_tin = models.FileField(upload_to="van_ban_den/")
    thu_tu = models.PositiveIntegerField(default=0)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "TepDinhKemVanBanDen"
        ordering = ["thu_tu", "ngay_tao", "ma_tep"]

    def __str__(self):
        return f"{self.so_vb_den_id} - {self.tep_tin.name}"

    def save(self, *args, **kwargs):
        if not self.ma_tep:
            with transaction.atomic():
                self.ma_tep = generate_prefixed_code(TepDinhKemVanBanDen, "ma_tep", "TDK", 7)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class TepDinhKemVanBanDi(models.Model):
    class LoaiTep(models.TextChoices):
        DU_THAO = "du_thao", "Du thao"
        CHINH_THUC = "chinh_thuc", "Chinh thuc"

    ma_tep = models.CharField(max_length=10, primary_key=True, blank=True)
    so_vb_di = models.ForeignKey(
        VanBanDi,
        on_delete=models.CASCADE,
        related_name="tep_dinh_kem_dis",
    )
    loai_tep = models.CharField(max_length=20, choices=LoaiTep.choices)
    tep_tin = models.FileField(upload_to="van_ban_di/")
    thu_tu = models.PositiveIntegerField(default=0)
    ngay_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "TepDinhKemVanBanDi"
        ordering = ["loai_tep", "thu_tu", "ngay_tao", "ma_tep"]

    def __str__(self):
        return f"{self.so_vb_di_id} - {self.loai_tep} - {self.tep_tin.name}"

    def save(self, *args, **kwargs):
        if not self.ma_tep:
            with transaction.atomic():
                self.ma_tep = generate_prefixed_code(TepDinhKemVanBanDi, "ma_tep", "TDI", 7)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class XuLy(models.Model):
    VAI_TRO_KY_NHAY = "ky_nhay"
    VAI_TRO_KY_CHINH = "ky_chinh"
    VAI_TRO_KY_THAY = "ky_thay"
    class TrangThaiKy(models.TextChoices):
        CHO_DUYET = "Cho duyet", "Chờ duyệt"
        DA_DUYET = "Da duyet", "Đã duyệt"
        DA_UY_QUYEN = "Da uy quyen", "Đã uỷ quyền"
        CHO_CHINH_SUA = "Cho chinh sua", "Chờ chỉnh sửa"

    TRANG_THAI_CHO_DUYET = TrangThaiKy.CHO_DUYET
    TRANG_THAI_DA_DUYET = TrangThaiKy.DA_DUYET
    TRANG_THAI_DA_UY_QUYEN = TrangThaiKy.DA_UY_QUYEN
    TRANG_THAI_CHO_CHINH_SUA = TrangThaiKy.CHO_CHINH_SUA
    VAI_TRO_KY_CHOICES = (
        (VAI_TRO_KY_NHAY, "Ký nháy"),
        (VAI_TRO_KY_CHINH, "Ký chính"),
    )

    VAI_TRO_KY_CHOICES = (
        (VAI_TRO_KY_NHAY, "Ky nhay"),
        (VAI_TRO_KY_CHINH, "Ky chinh"),
        (VAI_TRO_KY_THAY, "Ky thay"),
    )

    ma_xu_ly = models.CharField(max_length=10, primary_key=True, blank=True)
    ma_vb_di = models.ForeignKey(
        VanBanDi,
        on_delete=models.CASCADE,
        related_name="xu_lys",
    )
    ma_gv = models.ForeignKey(
        GiaoVien,
        on_delete=models.PROTECT,
        related_name="xu_ly_ky_van_bans",
    )
    vai_tro_ky = models.CharField(max_length=20, choices=VAI_TRO_KY_CHOICES)
    thoi_gian_ky = models.DateTimeField(null=True, blank=True)
    trang_thai_ky = models.CharField(max_length=100)

    class Meta:
        db_table = "XuLy"
        verbose_name = "Xử lý"
        verbose_name_plural = "Xử lý"
        ordering = ["ma_vb_di_id", "thoi_gian_ky", "ma_xu_ly"]

    def __str__(self):
        return f"{self.ma_vb_di_id} - {self.ma_gv_id}"

    def save(self, *args, **kwargs):
        if not self.ma_xu_ly:
            with transaction.atomic():
                self.ma_xu_ly = generate_prefixed_code(XuLy, "ma_xu_ly", "XLK", 7)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class NhatKyVanBan(models.Model):
    class TrangThai(models.TextChoices):
        CHO_CHINH_SUA = "Cho chinh sua", "Chờ chỉnh sửa"
        DA_CHINH_SUA = "Da chinh sua", "Đã chỉnh sửa"

    ma_nhat_ky = models.CharField(max_length=10, primary_key=True, blank=True)
    ma_nguoi_tao = models.ForeignKey(
        GiaoVien,
        on_delete=models.PROTECT,
        related_name="nhat_kys",
    )
    ma_vb_den = models.ForeignKey(
        VanBanDen,
        on_delete=models.CASCADE,
        related_name="nhat_kys",
        null=True,
        blank=True,
    )
    ma_vb_di = models.ForeignKey(
        VanBanDi,
        on_delete=models.CASCADE,
        related_name="nhat_kys",
        null=True,
        blank=True,
    )
    yc_chinh_sua = models.CharField(max_length=500, blank=True)
    trang_thai = models.CharField(max_length=100)
    thoi_gian_tao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "NhatKyVanBan"
        verbose_name = "Nhật ký văn bản"
        verbose_name_plural = "Nhật ký văn bản"
        ordering = ["-thoi_gian_tao"]

    def __str__(self):
        return self.ma_nhat_ky

    def save(self, *args, **kwargs):
        if not self.ma_nhat_ky:
            with transaction.atomic():
                self.ma_nhat_ky = generate_prefixed_code(NhatKyVanBan, "ma_nhat_ky", "NK", 8)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class PhanCongXuLy(models.Model):
    class TrangThaiXuLy(models.TextChoices):
        CHO_XU_LY = "Cho xu ly", "Chờ xử lý"
        DANG_XU_LY = "Dang xu ly", "Đang xử lý"
        DA_HOAN_THANH = "Da hoan thanh", "Đã hoàn thành"

    ma_xu_ly = models.CharField(max_length=10, primary_key=True, blank=True)
    so_vb_den = models.ForeignKey(
        VanBanDen,
        on_delete=models.CASCADE,
        related_name="phan_congs",
        null=True,
        blank=True,
    )
    so_vb_di = models.ForeignKey(
        VanBanDi,
        on_delete=models.CASCADE,
        related_name="phan_congs",
        null=True,
        blank=True,
    )
    nguoi_xu_ly = models.ForeignKey(
        GiaoVien,
        on_delete=models.PROTECT,
        related_name="phan_cong_xu_lys",
    )
    nguoi_phan_cong = models.ForeignKey(
        GiaoVien,
        on_delete=models.PROTECT,
        related_name="phan_cong_da_giao",
        null=True,
        blank=True,
    )
    noi_dung_cd = models.CharField(max_length=500)
    thoi_han = models.DateField()
    thoi_gian_phan_cong = models.DateTimeField(default=timezone.now)
    trang_thai_xl = models.CharField(max_length=100, default="Chưa xử lý")

    class Meta:
        db_table = "PhanCongXuLy"
        verbose_name = "Phân công xử lý"
        verbose_name_plural = "Phân công xử lý"
        ordering = ["thoi_han"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (Q(so_vb_den__isnull=False) & Q(so_vb_di__isnull=True))
                    | (Q(so_vb_den__isnull=True) & Q(so_vb_di__isnull=False))
                ),
                name="phan_cong_exactly_one_document",
            ),
            models.UniqueConstraint(
                fields=["so_vb_den", "nguoi_xu_ly"],
                condition=Q(so_vb_den__isnull=False),
                name="uniq_phan_cong_vb_den_nguoi_xu_ly",
            ),
            models.UniqueConstraint(
                fields=["so_vb_di", "nguoi_xu_ly"],
                condition=Q(so_vb_di__isnull=False),
                name="uniq_phan_cong_vb_di_nguoi_xu_ly",
            ),
        ]

    def __str__(self):
        return self.ma_xu_ly

    def save(self, *args, **kwargs):
        if not self.ma_xu_ly:
            with transaction.atomic():
                self.ma_xu_ly = generate_prefixed_code(PhanCongXuLy, "ma_xu_ly", "XL", 8)
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)


class LuanChuyenBenNgoai(models.Model):
    class TrangThaiGui(models.TextChoices):
        DA_GUI = "Da gui", "Da gui"
        GUI_LOI = "Gui loi", "Gui loi"
        CHO_GUI = "Cho gui", "Cho gui"

    ma_luan_chuyen = models.CharField(max_length=10, primary_key=True, blank=True)
    ma_vb_di = models.ForeignKey(
        VanBanDi,
        on_delete=models.CASCADE,
        related_name="luan_chuyen_ben_ngoais",
    )
    ma_noi_nhan = models.ForeignKey(
        NoiNhan,
        on_delete=models.PROTECT,
        related_name="luan_chuyen_ben_ngoais",
    )
    nguoi_thuc_hien = models.ForeignKey(
        GiaoVien,
        on_delete=models.PROTECT,
        related_name="luan_chuyen_ben_ngoai_da_tao",
    )
    thoi_gian_gui = models.DateTimeField(null=True, blank=True)
    trang_thai_gui = models.CharField(max_length=50, choices=TrangThaiGui.choices, default=TrangThaiGui.CHO_GUI)
    ghi_chu = models.CharField(max_length=500, blank=True)

    class Meta:
        db_table = "LuanChuyenBenNgoai"
        ordering = ["-thoi_gian_gui", "ma_luan_chuyen"]
        constraints = [
            models.UniqueConstraint(
                fields=["ma_vb_di", "ma_noi_nhan"],
                name="uniq_luan_chuyen_vb_di_noi_nhan",
            ),
        ]

    def __str__(self):
        return f"{self.ma_vb_di_id} - {self.ma_noi_nhan_id}"

    def save(self, *args, **kwargs):
        if not self.ma_luan_chuyen:
            with transaction.atomic():
                self.ma_luan_chuyen = generate_prefixed_code(
                    LuanChuyenBenNgoai,
                    "ma_luan_chuyen",
                    "LCN",
                    7,
                )
                super().save(*args, **kwargs)
                return
        super().save(*args, **kwargs)
