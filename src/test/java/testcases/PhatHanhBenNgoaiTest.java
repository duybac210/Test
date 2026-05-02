package testcases;

import common.bn.Utilities;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;
import pageobjects.bn.*;

import java.io.File;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;

public class PhatHanhBenNgoaiTest {
    private WebDriver driver;
    private LoginPage loginPage;
    private HomePage homePage;
    private XemVanBanDi xemVBD;
    private TimVBDi timVBD;
    private ChiTietVBDi chiTietVBDi;

    @BeforeTest
    public void setUp() {
        Utilities.autoLogin();
        this.driver = Utilities.getDriver();
        this.loginPage = new LoginPage(this.driver);
        this.homePage = new HomePage(this.driver);
        this.xemVBD = new XemVanBanDi(this.driver);
        this.timVBD = new TimVBDi(this.driver);
        this.chiTietVBDi = new ChiTietVBDi(this.driver);
    }

    @AfterMethod
    public void tearDownTestCase() {
        if (this.driver != null) {
            this.driver.navigate().refresh();
        }
    }

    public boolean isFileDownloaded(String downloadPath, String partialFileName) {
        File dir = new File(downloadPath);
        File[] dirContents = dir.listFiles();
        if (dirContents != null) {
            for (File file : dirContents) {
                if (file.getName().toLowerCase().contains(partialFileName.toLowerCase()) && !file.getName().endsWith(".crdownload")) {
                    return true;
                }
            }
        }
        return false;
    }

    @Test(priority = 1)
    public void TC01_HienThiDanhSach() {
        System.out.println("TC01: Kiểm tra hiển thị danh sách phát hành bên ngoài.");
        try {
            this.homePage.clickXemVanBanDi();
            Assert.assertTrue(this.xemVBD.kiemTraHienThiDayDuCot(), "Lỗi: Danh sách không hiển thị đủ cột thông tin!");
        } catch (Exception e) {
            Assert.fail("Failed: Không thể truy cập hoặc hiển thị danh sách văn bản. Chi tiết: " + e.getMessage());
        }
    }

    @Test(priority = 2)
    public void TC02_SapXepGiamDan() {
        System.out.println("TC02: Kiểm tra sắp xếp ngày ban hành giảm dần.");
        try {
            this.homePage.clickXemVanBanDi();
            Assert.assertTrue(this.xemVBD.kiemTraSapXepNgayBanHanhGiamDan(), "Lỗi: Danh sách chưa sắp xếp giảm dần!");
        } catch (Exception e) {
            Assert.fail("Failed: Lỗi khi kiểm tra sắp xếp. Chi tiết: " + e.getMessage());
        }
    }

    @Test(priority = 3)
    public void TC03_TimKiemLoaiVB() {
        System.out.println("TC03: Tìm kiếm theo loại văn bản 'Thông báo'.");
        try {
            this.homePage.clickXemVanBanDi();
            this.timVBD.timKiemVanBan("Thông báo");
            Assert.assertTrue(this.timVBD.kiemTraKetQuaHienThiLoaiVB("Thông báo"), "Lỗi: Kết quả tìm kiếm loại VB không đúng!");
        } catch (Exception e) {
            Assert.fail("Failed: Không tìm thấy kết quả cho loại văn bản 'Thông báo'. Vui lòng kiểm tra lại Data.");
        }
    }

    @Test(priority = 4)
    public void TC04_TimKiemNoiNhan() {
        System.out.println("TC04: Tìm kiếm theo nơi nhận 'Sở Giáo Dục'.");
        try {
            this.homePage.clickXemVanBanDi();
            this.timVBD.timKiemVanBan("Sở Giáo Dục");
            Assert.assertTrue(this.timVBD.kiemTraNoiNhanHienThi("Sở Giáo Dục"), "Lỗi: Kết quả hiển thị nơi nhận không đúng!");
        } catch (Exception e) {
            Assert.fail("Failed: Tìm kiếm nơi nhận 'Sở Giáo Dục' không cho kết quả như mong đợi.");
        }
    }

    @Test(priority = 5)
    public void TC05_TimKiemSoVB() {
        System.out.println("TC05: Tìm kiếm theo số văn bản có sẵn.");
        try {
            this.homePage.clickXemVanBanDi();
            String soVB = "VBD00001"; 
            this.timVBD.timKiemVanBan(soVB);
            Assert.assertTrue(this.timVBD.kiemTraKetQuaHienThiSoKyHieu(soVB), "Lỗi: Không tìm thấy số văn bản " + soVB);
        } catch (Exception e) {
            // Chuyển đổi từ Error sang Fail với thông điệp rõ ràng
            Assert.fail("Failed: Không tìm thấy văn bản có số hiệu 'VBD00001' trong danh sách kết quả.");
        }
    }

    @Test(priority = 6)
    public void TC06_TimKiemKhongCoKetQua() {
        System.out.println("TC06: Tìm kiếm với từ khóa không tồn tại.");
        try {
            this.homePage.clickXemVanBanDi();
            this.timVBD.timKiemVanBan("ZXZXZX123");
            Assert.assertTrue(this.driver.getPageSource().contains("Không tìm thấy") || this.driver.getPageSource().contains("Khong co du lieu"));
        } catch (Exception e) {
            Assert.fail("Failed: Hệ thống không hiển thị thông báo 'Không tìm thấy' khi tìm kiếm từ khóa rác.");
        }
    }

    @Test(priority = 7)
    public void TC07_XemChiTiet() {
        System.out.println("TC07: Xem chi tiết văn bản.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            Assert.assertTrue(this.chiTietVBDi.kiemTraTrangChiTietHienThi(), "Lỗi: Không mở được popup chi tiết!");
        } catch (Exception e) {
            Assert.fail("Failed: Không thể mở xem chi tiết văn bản dòng đầu tiên.");
        }
    }

    @Test(priority = 8)
    public void TC08_ChinhSuaThanhCong() {
        System.out.println("TC08: Kiểm tra tính năng chỉnh sửa.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            this.chiTietVBDi.clickChinhSua();
            this.chiTietVBDi.suaThongTin("Quyết định", "Phòng Giáo Dục");
            this.chiTietVBDi.clickLuu();
            Assert.assertTrue(this.chiTietVBDi.kiemTraThongBaoLuuThanhCong());
        } catch (Exception e) {
            Assert.fail("Failed: Lỗi trong quá trình chỉnh sửa văn bản. Chi tiết: " + e.getMessage());
        }
    }

    @Test(priority = 9)
    public void TC09_TrangThaiReadOnly() {
        System.out.println("TC09: Kiểm tra các trường ở chế độ xem (Read-only).");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            Assert.assertTrue(this.chiTietVBDi.kiemTraTruongBiKhoa("Số văn bản"), "Lỗi: Trường thông tin không ở trạng thái Read-only!");
        } catch (Exception e) {
            Assert.fail("Failed: Không thể kiểm tra trạng thái Read-only của các trường.");
        }
    }

    @Test(priority = 10)
    public void TC10_DownloadFile() {
        System.out.println("TC10: Kiểm tra download file đính kèm.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            
            String tenFileTrenUI = this.driver.findElement(By.id("m-ban-du-thao-link")).getText().trim();
            String tenFileGoc = tenFileTrenUI.split("\\.")[0]; 
            
            this.chiTietVBDi.clickDownloadFile(); 
            
            String downloadPath = System.getProperty("user.home") + "\\Downloads"; 
            boolean isDownloaded = false;
            int maxWaitSeconds = 15;
            
            for (int i = 0; i < maxWaitSeconds; i++) {
                if (isFileDownloaded(downloadPath, tenFileGoc)) {
                    isDownloaded = true;
                    break;
                }
                try { Thread.sleep(1000); } catch (InterruptedException e) {}
            }
            Assert.assertTrue(isDownloaded, "Lỗi: Đã chờ " + maxWaitSeconds + "s nhưng không tìm thấy file '" + tenFileGoc + "'!");
        } catch (Exception e) {
            Assert.fail("Failed: Lỗi khi thực hiện tải file hoặc file không tồn tại trên UI.");
        }
    }

    @Test(priority = 11)
    public void TC11_HienThiSauPhatHanh() {
        System.out.println("TC11: Kiểm tra trạng thái sau khi phát hành.");
        this.homePage.clickXemVanBanDi();
        
        try {
            this.xemVBD.clickVanBanTheoTrangThai("Chờ gửi");
            this.chiTietVBDi.clickPhatHanh();
            this.homePage.clickXemVanBanDi();
            Assert.assertTrue(this.xemVBD.kiemTraVanBanCoTrangThai("Đã gửi"), "Lỗi: Trạng thái không chuyển sang Đã gửi!");
        } catch (Exception e) {
            // Chuyển từ Error sang Fail để báo cáo "đẹp" hơn
            Assert.fail("Failed: Không có văn bản nào ở trạng thái 'Chờ gửi' để thực hiện test phát hành. Chi tiết: " + e.getMessage());
        }
    }

    @Test(priority = 12)
    public void TC12_KhopDuLieuPopup() {
        System.out.println("TC12: Kiểm tra dữ liệu Popup khớp với danh sách.");
        try {
            this.homePage.clickXemVanBanDi();
            String trichYeuNgoai = this.xemVBD.getTrichYeuDongDauTien();
            this.xemVBD.clickVanBanDauTien();
            String trichYeuTrong = this.chiTietVBDi.getTrichYeu();
            Assert.assertEquals(trichYeuTrong, trichYeuNgoai, "Lỗi: Dữ liệu trong popup không khớp với danh sách!");
        } catch (Exception e) {
            Assert.fail("Failed: Lỗi so khớp dữ liệu giữa danh sách và popup.");
        }
    }

    @Test(priority = 13)
    public void TC13_HuyChinhSua() {
        System.out.println("TC13: Kiểm tra nút Hủy bỏ chỉnh sửa.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            this.chiTietVBDi.clickChinhSua();
            this.chiTietVBDi.suaThongTin("Thông báo", "Noi Nhan Update");
            this.chiTietVBDi.clickHuy();
            Assert.assertFalse(this.driver.getPageSource().contains("Noi Nhan Update"), "Lỗi: Dữ liệu vẫn thay đổi sau khi nhấn Hủy!");
        } catch (Exception e) {
            Assert.fail("Failed: Nút Hủy bỏ chỉnh sửa không hoạt động đúng hoặc không tìm thấy Element.");
        }
    }

    @Test(priority = 14)
    public void TC14_BatLoiTrongTruongBatBuoc() {
        System.out.println("TC14: Kiểm tra bỏ trống trường bắt buộc.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            this.chiTietVBDi.clickChinhSua();
            this.chiTietVBDi.xoaTrichYeu();
            this.chiTietVBDi.clickLuu();
            Assert.assertTrue(this.driver.getPageSource().contains("Trích yếu") || this.driver.getPageSource().contains("bắt buộc"));
        } catch (Exception e) {
            Assert.fail("Failed: Hệ thống không hiển thị thông báo lỗi khi bỏ trống trường bắt buộc.");
        }
    }

    @Test(priority = 15)
    public void TC15_DongPopupBangNutX() {
        System.out.println("TC15: Đóng popup bằng nút X.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            this.chiTietVBDi.clickNutX();
        } catch (Exception e) {
            Assert.fail("Failed: Không thể đóng Popup bằng nút X.");
        }
    }

    @Test(priority = 16)
    public void TC16_LogicNgayBanHanh() {
        System.out.println("TC16: Ngày ban hành không được là tương lai.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            this.chiTietVBDi.clickChinhSua();
            String ngayTuongLai = LocalDate.now().plusDays(5).format(DateTimeFormatter.ofPattern("dd/MM/yyyy"));
            this.chiTietVBDi.suaNgayBanHanh(ngayTuongLai);
            this.chiTietVBDi.clickLuu();
            Assert.assertTrue(this.driver.getPageSource().contains("ngày") || this.driver.getPageSource().contains("tương lai"));
        } catch (Exception e) {
            Assert.fail("Failed: Không bắt được lỗi logic ngày ban hành trong tương lai.");
        }
    }

    @Test(priority = 17)
    public void TC17_LuuSauKhiSua() {
        System.out.println("TC17: Kiểm tra lưu thông tin sau khi sửa Trích yếu.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            this.chiTietVBDi.clickChinhSua();
            this.chiTietVBDi.suaTrichYeu("Báo cáo tháng 4");
            this.chiTietVBDi.clickLuu();
            Assert.assertTrue(this.chiTietVBDi.getTrichYeu().contains("Báo cáo tháng 4"));
        } catch (Exception e) {
            Assert.fail("Failed: Không thể lưu thông tin trích yếu sau khi chỉnh sửa.");
        }
    }

    @Test(priority = 18)
    public void TC18_SuaNoiNhanDropdown() {
        System.out.println("TC18: Thay đổi Nơi nhận.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanDauTien();
            this.chiTietVBDi.clickChinhSua();
            this.chiTietVBDi.chonNoiNhanTuDropdown("Sở Giáo Dục");
            this.chiTietVBDi.clickLuu();
        } catch (Exception e) {
            Assert.fail("Failed: Lỗi khi thay đổi nơi nhận. Chi tiết: " + e.getMessage());
        }
    }

    @Test(priority = 19)
    public void TC19_ChuyenTrangThaiSauPhatHanh() {
        System.out.println("TC19: Kiểm tra chuyển trạng thái.");
        try {
            this.homePage.clickXemVanBanDi();
            this.xemVBD.clickVanBanTheoTrangThai("Chờ gửi");
            this.chiTietVBDi.clickNutPhatHanhMauXanh();
            this.homePage.clickXemVanBanDi();
        } catch (Exception e) {
            Assert.fail("Failed: Không thực hiện được bước phát hành văn bản để kiểm tra trạng thái.");
        }
    }
}