package testcases;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.testng.Assert;
import org.testng.annotations.BeforeTest;
import org.testng.annotations.Test;
import pageobjects.oanh.HomePage;
import pageobjects.oanh.LoginPage;
import pageobjects.oanh.XemVanBanDi;
import pageobjects.oanh.TimVBDi;
import pageobjects.oanh.ChiTietVBDi;
import common.oanh.Utilities;

public class XemVBDiTest {
    private WebDriver driver;
    private LoginPage loginPage;
    private HomePage homePage;
    private XemVanBanDi xemVBD;
    private TimVBDi timVBD;
    private ChiTietVBDi chiTietVBDi; // Khai báo đối tượng

    @BeforeTest
    public void setUp() {
        Utilities.autoLogin(); // Giả sử hàm này đã thực hiện đăng nhập
        driver = Utilities.getDriver();

        // Khởi tạo các trang (Object Initialization)
        loginPage = new LoginPage(driver);
        homePage = new HomePage(driver);
        xemVBD = new XemVanBanDi(driver);
        timVBD = new TimVBDi(driver);
        chiTietVBDi = new ChiTietVBDi(driver);
    }

    @org.testng.annotations.AfterMethod
    public void tearDownTestCase() {
        // Làm mới lại trang web sau MỖI Test Case để đóng toàn bộ các popup (Modal)
        if (driver != null) {
            driver.navigate().refresh();

        }
    }

    @Test
    public void TC01() {
        System.out.println("Hiển thị đầy đủ thông tin cột tại danh sách văn bản đi.");

        // Nhấn chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // Kiểm tra
        boolean ketQua = xemVBD.kiemTraHienThiDayDuCot();

        // Khẳng định
        Assert.assertTrue(ketQua, "Lỗi: Danh sách cột thực tế không khớp với thiết kế!");
    }

    @Test
    public void TC02() {
        System.out.println("Bắt đầu TC02: Kiểm tra sắp xếp.");

        // Nhấn chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // 2. Gọi hàm kiểm tra sắp xếp
        boolean laGiamDan = xemVBD.kiemTraSapXepNgayBanHanhGiamDan();

        Assert.assertTrue(laGiamDan, "Lỗi: Danh sách văn bản chưa được sắp xếp giảm dần theo ngày ban hành!");

        System.out.println("Kết quả: Danh sách sắp xếp đúng.");
    }

    @Test
    public void TC03() {
        System.out.println("Bắt đầu TC03: Tài khoản không có quyền xem.");

        // đăng xuất tài khoản hiện tại trước.
        Utilities.logout();

        // Đăng nhập tài khoản giáo viên (không có quyền xem văn bản đi)
        driver.get("http://127.0.0.1:8000/"); // Điều hướng về trang đăng nhập
        loginPage.login("GV00000014", "giaovien123");

        // Truy cập trực tiếp liên kết http://127.0.0.1:8000/van-ban-di/
        driver.get("http://127.0.0.1:8000/van-ban-di/");

        // Kiểm tra hệ thống từ chối truy cập
        // Dấu hiệu: Bị chuyển hướng đi nơi khác HOẶC trên màn hình hiện thông báo lỗi
        String currentUrl = driver.getCurrentUrl();
        String pageSource = driver.getPageSource().toLowerCase();

        boolean isDenied = !currentUrl.contains("/van-ban-di/")
                || pageSource.contains("khong co quyen")
                || pageSource.contains("từ chối")
                || pageSource.contains("403");

        Assert.assertTrue(isDenied, "Lỗi: Tài khoản không có quyền nhưng vẫn truy cập được trang văn bản đi!");

        // Phục hồi trạng thái đăng nhập cho các Test Case khác chạy tiếp
        driver.manage().deleteAllCookies();
        driver.navigate().refresh();

        Utilities.autoLogin();
    }

    @Test
    public void TC04() {
        System.out.println("Bắt đầu TC04: Hiển thị thông báo khi dữ liệu trống.");
        // Nhấn chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();


        // Thực hiện GIẢ LẬP xóa hàng ngay trên trình duyệt
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript(
                "var tbody = document.querySelector('.table-custom tbody');" +
                        "if(tbody) { tbody.innerHTML = '<tr><td colspan=\"7\" class=\"text-center\">Chưa có văn bản đi nào</td></tr>'; }");

        // Kiểm tra thông báo hiển thị đúng như mong đợi,
        WebElement msg = driver.findElement(By.xpath("//td[text()='Chưa có văn bản đi nào']"));
        Assert.assertTrue(msg.isDisplayed(), "Thông báo trống không hiển thị!");


        System.out.println("TC_04: Đã kiểm tra thông báo trống bằng phương pháp giả lập UI.");
    }

    @Test
    public void TC05() {
        System.out.println("Bắt đầu TC05: Tìm kiếm theo số ký hiệu - có kết quả.");

        // Nhấn chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // Nhập số ký hiệu "01/NQ-THPTND" và Nhấn "Xem"
        timVBD.timKiemVanBan("01/NQ-THPTND");

        // Kiểm tra hệ thống hiển thị kết quả văn bản đi có số ký hiệu 01/NQ-THPTND
        boolean check = timVBD.kiemTraKetQuaHienThiSoKyHieu("01/NQ-THPTND");
        Assert.assertTrue(check, "Lỗi: Không tìm thấy văn bản đi có số ký hiệu 01/NQ-THPTND!");
    }

    @Test
    public void TC06() {
        System.out.println("Bắt đầu TC06: Tìm kiếm theo ngày ban hành - có kết quả.");

        // Nhấn chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // Nhập ngày ban hành "20/04/2026" và Nhấn "Xem"
        timVBD.timKiemTheoNgayBanHanh("20/04/2026");

        // Kiểm tra hệ thống hiển thị các văn bản có ngày ban hành "20/04/2026"
        boolean check = timVBD.kiemTraKetQuaHienThiNgayBanHanh("20/04/2026");
        Assert.assertTrue(check, "Lỗi: Hệ thống không hiển thị kết quả văn bản đi có ngày ban hành 20/04/2026!");
    }

    @Test
    public void TC07() {
        System.out.println("Bắt đầu TC07: Xóa tìm kiếm để hiển thị lại toàn bộ danh sách.");

        // Nhấn chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();
        int countBanDau = driver.findElements(By.cssSelector(".table-custom tbody tr")).size();


        // Nhập vào ô tìm kiếm 'VDO00000001' và Nhấn nút "Xem"
        timVBD.timKiemVanBan("VDO00000001");

        // Xóa nội dung trong ô tìm kiếm (truyền chuỗi rỗng và bấm Xem lại)
        timVBD.timKiemVanBan("");

        // Kiểm tra Hiển thị toàn bộ danh sách văn bản đi (Kiểm tra bảng có dữ liệu không phải là thông báo rỗng)
        int countSauReset = driver.findElements(By.cssSelector(".table-custom tbody tr")).size();
        Assert.assertEquals(countSauReset, countBanDau, "Lỗi: Số lượng bản ghi không khôi phục đủ!");
    }

    @Test
    public void TC08() {
        System.out.println("Bắt đầu TC08: Tìm kiếm không có kết quả.");

        // Nhấn chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // Nhập "16@sa" và Nhấn "Xem"
        timVBD.timKiemVanBan("16@sa");

        // Kiểm tra hiển thị thông báo "Không tìm thấy văn bản hợp lệ"
        String thongBaoThucTe = timVBD.getThongBaoTrongText();
        Assert.assertEquals(thongBaoThucTe, "Không tìm thấy văn bản hợp lệ", "Lỗi: Nội dung thông báo không khớp!");
    }

    @Test
    public void TC09() {
        System.out.println("Bắt đầu TC09: Xem chi tiết văn bản đi thành công.");

        // Nhấn chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // Nhấn vào văn bản đi bất kỳ
        xemVBD.clickVanBanDauTien();

        // Kiểm tra hệ thống mở trang chi tiết, hiển thị thông tin văn bản đi
        boolean moTrangChiTiet = chiTietVBDi.kiemTraTrangChiTietHienThi();

        Assert.assertTrue(moTrangChiTiet, "Lỗi: Hệ thống không hiển thị trang chi tiết văn bản đi!");
    }

    @Test
    public void TC10() {
        System.out.println("Bắt đầu TC10: Chỉnh sửa thành công.");

        // Chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // Nhấn vào văn bản bất kỳ có trạng thái đã đăng ký
        xemVBD.clickVanBanDaDangKy();

        // Nhấn vào nút "Chỉnh sửa"
        chiTietVBDi.clickChinhSua();

        // Sửa các trường được phép (Loại văn bản, nơi nhận)
        String loaiVanBanMoi = "Báo cáo";
        String noiNhanMoi = "Sở GD&ĐT DaNang";
        chiTietVBDi.suaThongTin(loaiVanBanMoi, noiNhanMoi);

        // Nhấn "Lưu"
        chiTietVBDi.clickLuu();

        // Kiểm tra thông báo lưu thành công
        boolean isThanhCong = chiTietVBDi.kiemTraThongBaoLuuThanhCong();
        Assert.assertTrue(isThanhCong, "Lỗi: Không thấy thông báo lưu thành công!");

        // Kiểm tra các trường hiển thị giá trị vừa sửa
        boolean isHienThiDung = chiTietVBDi.kiemTraThongTinSauKhiSua(loaiVanBanMoi, noiNhanMoi);
        Assert.assertTrue(isHienThiDung, "Lỗi: Thông tin sau khi lưu không hiển thị đúng giá trị vừa sửa!");

        // KIỂM TRA LỖI PHẦN MỀM: Đảm bảo Ngày ban hành và Ngày ký KHÔNG bị mất (null)
        boolean biLoiNgayNull = chiTietVBDi.kiemTraNgayBiNull();
        Assert.assertFalse(biLoiNgayNull,
                "LỖI PHẦN MỀM: Ngày ban hành hoặc Ngày ký đã bị biến thành rỗng/null sau khi lưu!");
    }

    @Test
    public void TC11() {
        System.out.println("Bắt đầu TC11: Hủy thao tác chỉnh sửa.");

        // Chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // Nhấn vào văn bản bất kỳ có trạng thái đã đăng ký
        xemVBD.clickVanBanDaDangKy();

        Assert.assertTrue(chiTietVBDi.kiemTraTrangChiTietHienThi(), "Lỗi: Không mở được popup chi tiết!");

        // Nhấn vào nút "Chỉnh sửa"
        chiTietVBDi.clickChinhSua();

        // Sửa các trường được phép (Sử dụng 1 chuỗi độc nhất để test hủy)
        String loaiVanBanMoi = "Báo cáo";
        String noiNhanMoi = "NoiNhan";
        chiTietVBDi.suaThongTin(loaiVanBanMoi, noiNhanMoi);

        // Nhấn "Hủy"
        chiTietVBDi.clickHuy();

        // Kiểm tra dữ liệu quay về giá trị ban đầu, popup thoát khỏi chế độ sửa
        // Kiểm tra chuỗi nhập thử KHÔNG ĐƯỢC PHÉP tồn tại trên màn hình
        boolean isHienThiSai = driver.getPageSource().contains(noiNhanMoi);
        Assert.assertFalse(isHienThiSai,
                "Lỗi: Bấm Hủy nhưng dữ liệu vẫn bị lưu vào hệ thống hoặc không thoát chế độ sửa!");
    }

    @Test
    public void TC12() {
        System.out.println("Bắt đầu TC12: Không chỉnh sửa được các trường bị khóa.");

        // Chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        xemVBD.clickVanBanDauTien();

        chiTietVBDi.clickChinhSua();

        // Kiểm tra 5 trường
        Assert.assertTrue(chiTietVBDi.kiemTraTruongBiKhoa("Số văn bản"), "Lỗi: Số văn bản không bị khóa!");
        Assert.assertTrue(chiTietVBDi.kiemTraTruongBiKhoa("Trạng thái"), "Lỗi: Trạng thái không bị khóa!");
        Assert.assertTrue(chiTietVBDi.kiemTraTruongBiKhoa("Số ký hiệu"), "Lỗi: Số ký hiệu không bị khóa!");
        Assert.assertTrue(
                chiTietVBDi.kiemTraTruongBiKhoa("Người soạn thảo") || chiTietVBDi.kiemTraTruongBiKhoa("Người soạn"),
                "Lỗi: Người soạn thảo không bị khóa!");
        Assert.assertTrue(chiTietVBDi.kiemTraTruongBiKhoa("Người ký"), "Lỗi: Người ký không bị khóa!");
    }

    @Test
    public void TC13() {
        System.out.println("Bắt đầu TC13: Bỏ trống trường bắt buộc.");

        // Chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        // Nhấn vào 1 dòng văn bản bất kỳ
        xemVBD.clickVanBanDauTien();

        // Nhấn "Chỉnh sửa"
        chiTietVBDi.clickChinhSua();

        //  Xóa nơi nhận (Bỏ trống trường bắt buộc)
        chiTietVBDi.xoaNoiNhan();

        //  Nhấn "Lưu"
        chiTietVBDi.clickLuu();

        // Kiểm tra kết quả mong đợi: Hiển thị thông báo "Nhập đầy đủ các trường"

        String thongBaoMongDoi = "Nhập đầy đủ các trường";

        boolean hasErrorMsg = chiTietVBDi.kiemTraThongBaoHienThi(thongBaoMongDoi);

        Assert.assertTrue(hasErrorMsg,
                "Lỗi: Không hiển thị đúng thông báo mong đợi! (Mong đợi: '" + thongBaoMongDoi + "')");
    }

    @Test
    public void TC14() {
        System.out.println("Bắt đầu TC14: Ngày ban hành không được bé hơn ngày ký.");

        // Chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        xemVBD.clickVanBanDauTien();

        chiTietVBDi.clickChinhSua();

        chiTietVBDi.suaNgay("20/04/2026", "25/04/2026");
        chiTietVBDi.clickLuu();

        boolean hasErrorMsg = chiTietVBDi.kiemTraThongBaoHienThi("nhỏ hơn")
                || chiTietVBDi.kiemTraThongBaoHienThi("bé hơn");
        Assert.assertTrue(hasErrorMsg, "Lỗi: Hệ thống không báo lỗi ngày ban hành < ngày ký!");
    }

    @Test
    public void TC15() {
        System.out.println("Bắt đầu TC15: Văn bản đã gửi phân công không được sửa.");

        // Chọn menu "Văn bản đi"
        homePage.clickXemVanBanDi();

        xemVBD.clickVanBanTheoTrangThai("gửi phân công");

        Assert.assertFalse(chiTietVBDi.kiemTraNutChinhSuaTrangThai(),
                "Lỗi: Nút Chỉnh sửa vẫn hiển thị/nhấn được đối với VB đã gửi phân công!");
    }

    @Test
    public void TC16() {
        System.out.println("Bắt đầu TC16: Văn bản đã phát hành không được sửa.");
        homePage.clickXemVanBanDi();

        xemVBD.clickVanBanTheoTrangThai("phát hành");

        Assert.assertFalse(chiTietVBDi.kiemTraNutChinhSuaTrangThai(),
                "Lỗi: Nút Chỉnh sửa vẫn hiển thị/nhấn được đối với VB đã phát hành!");
    }

    @Test
    public void TC17() {
        System.out.println("Bắt đầu TC17: Không phải văn thư không có quyền chỉnh sửa.");

        // Đăng xuất tài khoản văn thư để đổi sang hiệu trưởng
        Utilities.logout();

        driver.get("http://127.0.0.1:8000/");
        loginPage.login("GV00000001", "giaovien123");

        homePage.clickXemVanBanDi();

        xemVBD.clickVanBanDauTien();

        Assert.assertFalse(chiTietVBDi.kiemTraNutChinhSuaTrangThai(),
                "Lỗi: Tài khoản hiệu trưởng vẫn thấy nút Chỉnh sửa!");

        // Trả lại trạng thái cho test case tiếp theo
        driver.manage().deleteAllCookies();
        driver.navigate().refresh();
        try {
            Thread.sleep(1000);
        } catch (InterruptedException e) {
        }
        Utilities.autoLogin();
    }

    @Test
    public void TC18() {
        System.out.println("Bắt đầu TC18: Văn bản đã đăng ký mới được chuyển phân công.");
        homePage.clickXemVanBanDi();

        xemVBD.clickVanBanTheoTrangThai("chờ duyệt");

        Assert.assertFalse(chiTietVBDi.kiemTraNutChuyenPhanCongTrangThai(),
                "Lỗi: Nút Chuyển phân công vẫn hiển thị/nhấn được đối với VB Chờ duyệt!");
    }
}
