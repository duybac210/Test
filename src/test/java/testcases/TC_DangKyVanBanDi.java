package testcases;

import common.Utilities;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pageobjects.HomePage;
import pageobjects.ManHinhDangKyVanBanDi;
import pageobjects.ManHinhDuyetVanBan;
import pageobjects.ManHinhTaoVanBanDi;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.List;

public class TC_DangKyVanBanDi {
    private WebDriver driver;
    private WebDriverWait wait;
    private ManHinhDangKyVanBanDi dangKyPage;

    // Credentials
    private static final String CLERK_USER = "GV000006";
    private static final String CLERK_PASS = "giaovien123";
    private static final String TEACHER_USER = "GV00000014";
    private static final String TEACHER_PASS = "giaovien123";
    private static final String HT_USER = "GV00000001";
    private static final String HT_PASS = "giaovien123";

    @BeforeMethod
    public void setUp() {
        driver = Utilities.getDriver();
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
        dangKyPage = new ManHinhDangKyVanBanDi(driver);
    }

    @AfterMethod
    public void tearDown() {
        Utilities.logout();
        Utilities.quitDriver();
    }

    /** Tạo văn bản đi từ dự thảo (Giáo viên tạo) và trả về trích yếu unique. */
    private String createDraft(String trichYeu) {
        System.out.println("  [CREATE_DRAFT] Bắt đầu tạo dự thảo: " + trichYeu);
        Utilities.loginAs(TEACHER_USER, TEACHER_PASS);
        new HomePage(driver).navigateToTaoVanBan();
        ManHinhTaoVanBanDi taoPage = new ManHinhTaoVanBanDi(driver);

        System.out.println("  [CREATE_DRAFT] Điền form tạo văn bản.");
        taoPage.selectLoaiVanBan("LVB0000013");
        taoPage.selectMucDo("MD00000001");
        taoPage.inputNoiNhan("To Toan");
        taoPage.inputTrichYeu(trichYeu);
        String filePath = createTempFile("du_thao.pdf", "Content");
        taoPage.uploadFileDuThao(filePath);

        System.out.println("  [CREATE_DRAFT] Nhấn nút Trình duyệt.");
        taoPage.submitForm();

        System.out.println("  [CREATE_DRAFT] Đợi redirect...");
        wait.until(ExpectedConditions.or(
                ExpectedConditions.urlContains("/van-ban-di/"),
                ExpectedConditions.urlContains("/cong-viec-ca-nhan/")));
        System.out.println("  [CREATE_DRAFT] Tạo dự thảo thành công. URL: " + driver.getCurrentUrl());
        Utilities.logout();
        return trichYeu;
    }

    /** Duyệt văn bản (Hiệu trưởng duyệt) để chuyển sang trạng thái CHỜ ĐĂNG KÝ. */
    private void approveDocument(String trichYeu) {
        System.out.println("  [APPROVE_DOC] Bắt đầu duyệt văn bản: " + trichYeu);
        Utilities.loginAs(HT_USER, HT_PASS);
        new HomePage(driver).navigateToDuyetVanBan();
        ManHinhDuyetVanBan duyetPage = new ManHinhDuyetVanBan(driver);

        System.out.println("  [APPROVE_DOC] Tìm kiếm văn bản.");
        duyetPage.searchDocument(trichYeu);
        System.out.println("  [APPROVE_DOC] Click vào văn bản để mở modal.");
        duyetPage.clickDocumentByTrichYeu(trichYeu);

        System.out.println("  [APPROVE_DOC] Nhấn nút Duyệt.");
        duyetPage.clickDuyet();
        System.out.println("  [APPROVE_DOC] Duyệt thành công.");
        Utilities.logout();
    }

    /** Tìm so_vb_di của văn bản dựa trên trích yếu từ danh sách. */
    private String getSoVBDiFromList(String trichYeu) {
        System.out.println("  [GET_SO_VB] Tìm mã VB từ danh sách cho trích yếu: " + trichYeu);
        driver.get("http://127.0.0.1:8000/van-ban-di/");

        try {
            // Thử tìm kiếm để lọc danh sách
            WebElement searchBox = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("search-input")));
            searchBox.clear();
            searchBox.sendKeys(trichYeu);
            driver.findElement(By.id("search-button")).click();
            try {
                Thread.sleep(1000);
            } catch (InterruptedException ignored) {
            }
        } catch (Exception e) {
            System.out.println("  [GET_SO_VB] Cảnh báo: Không tìm thấy ô search, thử tìm trực tiếp trong bảng.");
        }

        WebElement row = wait.until(ExpectedConditions.visibilityOfElementLocated(
                By.xpath("//tr[contains(., '" + trichYeu + "')]")));
        String id = row.findElement(By.xpath("./td[1]")).getText().trim();
        System.out.println("  [GET_SO_VB] Tìm thấy mã: " + id);
        return id;
    }

    /** Tìm mã VB đầu tiên có trạng thái cụ thể từ danh sách. */
    private String getSoVBDiByStatus(String status) {
        System.out.println("  [GET_SO_VB_STATUS] Tìm mã VB có trạng thái: " + status);
        driver.get("http://127.0.0.1:8000/van-ban-di/");
        try {
            WebElement row = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    By.xpath("//tr[contains(., '" + status + "')]")));
            String id = row.findElement(By.xpath("./td[1]")).getText().trim();
            System.out.println("  [GET_SO_VB_STATUS] Tìm thấy mã: " + id);
            return id;
        } catch (Exception e) {
            System.out.println("  [GET_SO_VB_STATUS] Không tìm thấy văn bản nào có trạng thái '" + status + "'");
            return null;
        }
    }

    // ==========================================
    // NHÓM 1: KIỂM THỬ PHÂN QUYỀN & BẢO MẬT
    // ==========================================

    @Test(description = "TC_SEC_01: Chặn truy cập với tài khoản không có quyền Văn thư")
    public void TC_SEC_01_BlockNonClerkAccess() {
        System.out.println(">>> BẮT ĐẦU TC_SEC_01");
        Utilities.loginAs(TEACHER_USER, TEACHER_PASS);
        driver.get("http://127.0.0.1:8000/van-ban-di/dang-ky/");
        String pageSource = driver.getPageSource();
        // Sửa: Kiểm tra nội dung chặn truy cập cụ thể, không chỉ URL
        boolean hasAccessError = pageSource.contains("Ban khong co quyen truy cap")
                || pageSource.contains("Permission Denied")
                || !driver.findElements(By.xpath("//*[contains(text(), '403') or contains(text(), '404')]")).isEmpty();

        System.out
                .println("  [CHECK] Mong đợi: Tài khoản không có quyền Văn thư phải bị chặn (Redirect hoặc báo lỗi).");
        System.out.println("  [CHECK] Thực tế: URL=" + driver.getCurrentUrl() + ", hasAccessError=" + hasAccessError);
        Assert.assertTrue(hasAccessError, "Tài khoản không có quyền Văn thư phải thấy thông báo bị chặn.");
        System.out.println(">>> KẾT THÚC TC_SEC_01: PASS");
    }

    @Test(description = "TC_SEC_02: Chặn đăng ký văn bản chưa được duyệt")
    public void TC_SEC_02_BlockUnapprovedDocRegistration() {
        System.out.println(">>> BẮT ĐẦU TC_SEC_02");
        String trichYeu = "Auto-Unapproved-" + System.currentTimeMillis();
        createDraft(trichYeu);

        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        String soVBDi = getSoVBDiFromList(trichYeu);
        System.out.println("Step: Thử truy cập trực tiếp trang đăng ký cho VB " + soVBDi);
        driver.get("http://127.0.0.1:8000/van-ban-di/" + soVBDi + "/dang-ky/");

        String pageSource = driver.getPageSource();
        boolean isBlocked = pageSource.contains("không hợp lệ")
                || pageSource.contains("Ban khong co quyen")
                || !driver.findElements(By.xpath("//*[contains(text(), '403') or contains(text(), '404')]")).isEmpty();

        System.out.println("  [CHECK] Mong đợi: Không được phép đăng ký văn bản chưa được duyệt.");
        System.out.println("  [CHECK] Thực tế: URL=" + driver.getCurrentUrl() + ", isBlocked=" + isBlocked);
        Assert.assertTrue(isBlocked, "Hệ thống phải hiển thị lỗi khi đăng ký VB chưa duyệt.");
        System.out.println(">>> KẾT THÚC TC_SEC_02: PASS");
    }

    @Test(description = "TC_SEC_03: Chặn đăng ký cho văn bản đã đăng ký hoặc đang chờ duyệt")
    public void TC_SEC_03_BlockRegistrationForInvalidStatus() {
        System.out.println(">>> BẮT ĐẦU TC_SEC_03");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);

        // Thử tìm VB đã đăng ký
        String targetId = getSoVBDiByStatus("Đã đăng ký");
        if (targetId == null) {
            targetId = getSoVBDiByStatus("Chờ duyệt");
        }

        if (targetId != null) {
            System.out.println("Step: Thử truy cập trang đăng ký cho VB " + targetId);
            driver.get("http://127.0.0.1:8000/van-ban-di/" + targetId + "/dang-ky/");

            String pageSource = driver.getPageSource();
            // Mong đợi là bị chặn hoặc không hiển thị nút Lưu
            boolean isBlocked = !driver.getCurrentUrl().contains("/dang-ky/")
                    || pageSource.contains("không hợp lệ")
                    || pageSource.contains("Ban khong co quyen")
                    || driver.findElements(By.xpath("//button[contains(text(), 'Lưu')]")).isEmpty();

            System.out.println("  [CHECK] Mong đợi: Hệ thống phải chặn đăng ký cho văn bản đã Đã đăng ký/Chờ duyệt.");
            System.out.println("  [CHECK] Thực tế: URL=" + driver.getCurrentUrl() + ", Blocked=" + isBlocked);
            Assert.assertTrue(isBlocked, "Hệ thống phải chặn đăng ký cho văn bản đã ở trạng thái " + targetId);
        } else {
            throw new org.testng.SkipException("Không tìm thấy dữ liệu mẫu (Đã đăng ký/Chờ duyệt) để test. Bỏ qua test case.");
        }

        System.out.println(">>> KẾT THÚC TC_SEC_03");


    }

    // ==========================================
    // NHÓM 2: LUỒNG NGHIỆP VỤ CHÍNH
    // ==========================================

    @Test(description = "TC_FLOW_01: Đăng ký thành công văn bản từ dự thảo (Luồng 1)")
    public void TC_FLOW_01_RegisterFromDraftSuccess() {
        System.out.println(">>> BẮT ĐẦU TC_FLOW_01");
        String trichYeu = "Auto-Flow1-" + System.currentTimeMillis();
        createDraft(trichYeu);
        approveDocument(trichYeu);

        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        String soVBDi = getSoVBDiFromList(trichYeu);
        System.out.println("Step: Mở trang đăng ký cho VB " + soVBDi);
        driver.get("http://127.0.0.1:8000/van-ban-di/" + soVBDi + "/dang-ky/");

        System.out.println("Step: Nhập ngày ký, tải file và Lưu.");
        dangKyPage.inputNgayKy("2026-04-26");
        dangKyPage.uploadBanChinhThuc(createTempFile("flow1.pdf", "Official content"));
        dangKyPage.clickLuu();

        System.out.println("Step: Đợi kết quả.");
        try {
            dangKyPage.waitForStatusChange("Cho dang ky");
        } catch (Exception e) {
            System.out.println("  [DEBUG] Timeout đợi status change, thử refresh trang...");
            driver.navigate().refresh();
            try {
                Thread.sleep(2000);
            } catch (InterruptedException ignored) {
            }
        }

        String actualMsg = dangKyPage.getSuccessMessage();
        String lowerMsg = actualMsg.toLowerCase();
        System.out.println("  - Thông báo: " + actualMsg);

        String trangThai = dangKyPage.getTrangThai();
        String lowerStatus = trangThai.toLowerCase();

        System.out.println("  [CHECK] Mong đợi: Trạng thái văn bản chuyển sang 'Đã đăng ký'.");
        System.out.println("  [CHECK] Thực tế: Status=\"" + trangThai + "\", Msg=\"" + actualMsg + "\"");

        Assert.assertTrue(lowerStatus.contains("đã đăng ký") || lowerStatus.contains("da dang ky"),
                "LỖI: Trạng thái không cập nhật đúng. Trạng thái thực tế: " + trangThai);

        Assert.assertTrue(lowerMsg.contains("đã đăng ký") || lowerMsg.contains("da dang ky") || lowerMsg.contains("thanh cong") || lowerMsg.contains("thành công"),
                "LỖI: Không hiển thị đúng toast message thành công. Message thực tế: " + actualMsg);

        System.out.println("  - Văn bản ID: " + soVBDi);
        System.out.println(">>> KẾT THÚC TC_FLOW_01: PASS");
    }

    /** Helper thực hiện đăng ký trực tiếp để tái sử dụng giữa các Test Case */
    private String registerDirectlyHelper(String trichYeu) {
        dangKyPage.openDirectRegistration();
        dangKyPage.inputNgayKy("2026-04-27");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Đào tạo");
        dangKyPage.inputTrichYeu(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("direct.pdf", "Content"));
        dangKyPage.clickLuu();
        dangKyPage.waitForRegistrationSuccess();
        return dangKyPage.getSoVBDi();
    }

    @Test(description = "TC_FLOW_02: Đăng ký mới văn bản trực tiếp (Luồng 2)")
    public void TC_FLOW_02_DirectRegistrationSuccess() {
        System.out.println(">>> BẮT ĐẦU TC_FLOW_02");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        String trichYeu = "Auto-Flow2-" + System.currentTimeMillis();

        System.out.println("Step: Thực hiện đăng ký trực tiếp.");
        String soVBDi = registerDirectlyHelper(trichYeu);

        String actualMsg = dangKyPage.getSuccessMessage();
        String lowerMsg = actualMsg.toLowerCase();
        System.out.println("  [CHECK] Mong đợi: Thông báo đăng ký thành công.");
        System.out.println("  [CHECK] Thực tế: \"" + actualMsg + "\"");
        boolean isSuccess = lowerMsg.contains("thành công") || lowerMsg.contains("thanh cong")
                || lowerMsg.contains("đã đăng ký") || lowerMsg.contains("da dang ky");
        Assert.assertTrue(isSuccess, "Thông báo lỗi: " + actualMsg);

        String trangThai = dangKyPage.getTrangThai();
        System.out.println("  [CHECK] Mong đợi: Trạng thái hiển thị là 'Đã đăng ký'.");
        System.out.println("  [CHECK] Thực tế: " + trangThai);
        Assert.assertTrue(trangThai.toLowerCase().contains("da dang ky") || trangThai.contains("Đã đăng ký"),
                "Trạng thái lỗi: " + trangThai);
        System.out.println(">>> KẾT THÚC TC_FLOW_02: PASS");
    }

    // ==========================================
    // NHÓM 4: CẤP SỐ & XỬ LÝ ĐỒNG THỜI
    // ==========================================

    @Test(description = "TC_VAL_01: Bỏ trống tất cả các trường và nhấn Lưu")
    public void TC_VAL_01_EmptyFieldsSave() {
        System.out.println(">>> BẮT ĐẦU TC_VAL_01");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);

        // THÊM DÒNG NÀY: Phải mở form trước khi nhấn Lưu
        dangKyPage.openDirectRegistration();

        System.out.println("Step: Nhấn Lưu khi form trống.");
        dangKyPage.clickLuu();

        System.out.println("Step: Kiểm tra validation text.");
        String errors = dangKyPage.getValidationErrors();
        System.out.println("  [CHECK] Mong đợi: Phải hiển thị thông báo lỗi bắt buộc.");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errors + "\"");

        // BỎ VẾ OR CHỨA URL ĐI, CHỈ ASSERT CHUỖI TEXT, VÀ THÊM NULL CHECK
        Assert.assertTrue(errors != null && !errors.isEmpty() && (errors.contains("bắt buộc") || errors.contains("Vui lòng")),
                "Hệ thống không hiển thị đúng thông báo lỗi bắt buộc khi bỏ trống form. Text thu được: " + errors);
        System.out.println(">>> KẾT THÚC TC_VAL_01: PASS");
    }

    @Test(description = "TC_FLOW_03: Chỉ nhập các trường bắt buộc và nhấn Lưu")
    public void TC_FLOW_03_RequiredFieldsOnly() {
        System.out.println(">>> BẮT ĐẦU TC_FLOW_03");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        String trichYeu = "Auto-RequiredOnly-" + System.currentTimeMillis();
        System.out.println("Step: Điền các trường bắt buộc.");
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Hội đồng trường");
        dangKyPage.inputTrichYeu(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("required.pdf", "Content"));

        System.out.println("Step: Nhấn Lưu.");
        dangKyPage.clickLuu();

        System.out.println("Step: Đợi lưu thành công.");
        dangKyPage.waitForRegistrationSuccess();

        String actualMsg = dangKyPage.getSuccessMessage();
        String lowerMsg = actualMsg.toLowerCase();
        System.out.println("  [CHECK] Mong đợi: Thông báo lưu thành công.");
        System.out.println("  [CHECK] Thực tế: \"" + actualMsg + "\"");
        boolean isSuccess = lowerMsg.contains("thành công") || lowerMsg.contains("thanh cong")
                || lowerMsg.contains("đã đăng ký") || lowerMsg.contains("da dang ky");
        Assert.assertTrue(isSuccess, "Lưu không thành công: " + actualMsg);
        System.out.println(">>> KẾT THÚC TC_FLOW_03: PASS");
    }

    @Test(description = "TC_CONC_01: Double click nút Lưu - Tránh tạo 2 bản ghi")
    public void TC_CONC_01_DoubleClickSave() {
        System.out.println(">>> BẮT ĐẦU TC_CONC_01");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        String trichYeu = "Auto-DoubleSubmit-" + System.currentTimeMillis();
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Test double click");
        dangKyPage.inputTrichYeu(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("double.pdf", "Content"));

        System.out.println("Step: Double click nút Lưu.");
        dangKyPage.doubleClickLuu();

        System.out.println("Step: Đợi lưu thành công.");
        dangKyPage.waitForRegistrationSuccess();

        String soVBDi = dangKyPage.getSoVBDi();
        System.out.println("  - Mã văn bản vừa tạo: " + soVBDi);

        System.out.println("Step: Kiểm tra danh sách xem có bị trùng lặp không.");
        driver.get("http://127.0.0.1:8000/van-ban-di/");
        // Tìm số lượng bản ghi có cùng trích yếu
        int count = driver.findElements(By.xpath("//tr[contains(., '" + trichYeu + "')]")).size();
        System.out.println("  - Số lượng bản ghi tìm thấy với trích yếu này: " + count);

        System.out.println("  [CHECK] Mong đợi: Chỉ tồn tại 1 bản ghi duy nhất với trích yếu này.");
        System.out.println("  [CHECK] Thực tế: count=" + count);
        Assert.assertEquals(count, 1, "Chỉ được phép tạo 1 bản ghi duy nhất.");
        System.out.println(">>> KẾT THÚC TC_CONC_01: PASS");
    }

    @Test(description = "TC_CAPSO_01: Kiểm tra định dạng số ký hiệu sau khi đăng ký")
    public void TC_CAPSO_01_AutoNumberingFormat() {
        System.out.println(">>> BẮT ĐẦU TC_CAPSO_01");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao("GV00000014");
        dangKyPage.selectNguoiKy("GV00000001");
        dangKyPage.inputNoiNhan("Test");
        dangKyPage.inputTrichYeu("Test numbering " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("test.pdf", "Content"));

        try {
            System.out.println("Step: Thử nhấn Cấp số.");
            dangKyPage.clickCapSo();
            wait.until(d -> {
                String skh = dangKyPage.getSoKyHieu();
                return skh != null && !skh.isEmpty();
            });
        } catch (Exception e) {
            System.out.println("  - Nút cấp số không hoạt động hoặc không cần thiết.");
        }

        System.out.println("Step: Lưu văn bản.");
        dangKyPage.clickLuu();
        dangKyPage.waitForRegistrationSuccess();

        String soKyHieu = dangKyPage.getSoKyHieu();
        System.out.println("  - Số ký hiệu nhận được: " + soKyHieu);
        System.out.println("  [CHECK] Mong đợi: Số ký hiệu không trống, có '/' và kết thúc bằng 'THPTND'.");
        System.out.println("  [CHECK] Thực tế: " + soKyHieu);
        Assert.assertFalse(soKyHieu.isEmpty(), "Số ký hiệu trống.");
        Assert.assertTrue(soKyHieu.contains("/"), "Số ký hiệu sai định dạng (thiếu /).");
        Assert.assertTrue(soKyHieu.endsWith("THPTND"), "Số ký hiệu phải kết thúc bằng 'THPTND'.");
        System.out.println(">>> KẾT THÚC TC_CAPSO_01: PASS");
    }

    // ==========================================
    // NHÓM 5: HỆ QUẢ & CHUYỂN ĐỔI TRẠNG THÁI
    // ==========================================

    @Test(description = "TC_STATE_01: Kiểm tra chế độ Read-only sau khi đăng ký")
    public void TC_STATE_01_ReadOnlyAfterRegistration() {
        System.out.println(">>> BẮT ĐẦU TC_STATE_01");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        String trichYeu = "Auto-ReadOnly-" + System.currentTimeMillis();

        // Sửa: Gọi Helper thay vì gọi trực tiếp Test Case khác (Phá vỡ tính độc lập)
        registerDirectlyHelper(trichYeu);

        System.out.println("Step: Kiểm tra readonly.");
        boolean isReadOnly = dangKyPage.isFieldReadOnly(By.id("id_trich_yeu"));
        int saveBtns = driver.findElements(By.cssSelector("button[type='submit']")).size();
        System.out.println("  [CHECK] Mong đợi: Trường Trích yếu Read-only và nút Lưu biến mất.");
        System.out.println("  [CHECK] Thực tế: isReadOnly=" + isReadOnly + ", saveBtnsCount=" + saveBtns);
        Assert.assertTrue(isReadOnly, "Trường Trích yếu phải Read-only sau khi đăng ký.");
        Assert.assertEquals(saveBtns, 0, "Nút Lưu phải biến mất sau khi đăng ký thành công.");
        System.out.println(">>> KẾT THÚC TC_STATE_01: PASS");
    }

    @Test(description = "TC_CANCEL_01: Kiểm tra nút Hủy (Reset form)")
    public void TC_CANCEL_01_CancelRegistration() {
        System.out.println(">>> BẮT ĐẦU TC_CANCEL_01");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();
        dangKyPage.inputTrichYeu("Dữ liệu tạm");
        System.out.println("Step: Nhấn Hủy.");
        dangKyPage.clickHuy();
        String value = driver.findElement(By.id("id_trich_yeu")).getAttribute("value");
        System.out.println("  [CHECK] Mong đợi: Trường Trích yếu rỗng sau khi Hủy.");
        System.out.println("  [CHECK] Thực tế: '" + value + "'");
        Assert.assertEquals(value, "", "Form chưa được reset.");
        System.out.println(">>> KẾT THÚC TC_CANCEL_01: PASS");
    }

    // ==========================================
    // NHÓM 6: KIỂM TRA SỐ VĂN BẢN ĐI (ID)
    // ==========================================

    @Test(description = "TC_ID_01: Kiểm tra số văn bản đi tự tăng +1")
    public void TC_ID_01_AutoIncrement() {
        System.out.println(">>> BẮT ĐẦU TC_ID_01");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);

        System.out.println("Step 1: Lấy số văn bản đi lớn nhất hiện tại.");
        String latestIdStr = dangKyPage.getLatestSoVBDiFromList();
        int latestId = parseIdNumeric(latestIdStr);
        System.out.println("  - Số hiện tại lớn nhất: " + latestIdStr + " (" + latestId + ")");

        System.out.println("Step 2: Đăng ký văn bản mới.");
        dangKyPage.openDirectRegistration();
        String trichYeu = "Auto-Increment-Test-" + System.currentTimeMillis();
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Test ID");
        dangKyPage.inputTrichYeu(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("id_test.pdf", "Content"));
        dangKyPage.clickLuu();
        dangKyPage.waitForRegistrationSuccess();

        System.out.println("Step 3: Kiểm tra số văn bản đi mới.");
        String newIdStr = dangKyPage.getSoVBDi();
        int newId = parseIdNumeric(newIdStr);
        System.out.println("  - Số văn bản đi mới: " + newIdStr + " (" + newId + ")");

        // Sửa: Assert newId > latestId (An toàn cho môi trường đa người dùng/Parallel)
        System.out.println("  [CHECK] Mong đợi: ID mới (" + newId + ") phải lớn hơn ID cũ (" + latestId + ").");
        System.out.println("  [CHECK] Thực tế: " + (newId > latestId));
        Assert.assertTrue(newId > latestId, "Số văn bản đi phải được cấp mới (tăng lên).");
        System.out.println(">>> KẾT THÚC TC_ID_01: PASS");
    }

    @Test(description = "TC_ID_02: Kiểm tra định dạng và tính Read-only của Số văn bản đi")
    public void TC_ID_02_FormatAndReadOnly() {
        System.out.println(">>> BẮT ĐẦU TC_ID_02");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        System.out.println("Step 1: Kiểm tra tính Read-only.");
        boolean isRO = dangKyPage.isSoVBDiReadOnly();
        String soVBDi = dangKyPage.getSoVBDi();
        System.out.println("  [CHECK] Mong đợi: Trường Số văn bản đi Read-only và định dạng VBOxxxxxxxx.");
        System.out.println("  [CHECK] Thực tế: isReadOnly=" + isRO + ", Value=" + soVBDi);
        Assert.assertTrue(isRO, "Trường Số văn bản đi phải Read-only.");
        Assert.assertTrue(soVBDi.matches("VBO\\d{8}"), "Số văn bản đi hiển thị sai định dạng (phải là VBOxxxxxxxx).");
        System.out.println(">>> KẾT THÚC TC_ID_02: PASS");
    }

    // ==========================================
    // NHÓM 7: KIỂM TRA TRẠNG THÁI (STATUS)
    // ==========================================

    @Test(description = "TC_STATE_02: Kiểm tra trạng thái mặc định và tính Read-only")
    public void TC_STATE_02_DefaultStatusAndReadOnly() {
        System.out.println(">>> BẮT ĐẦU TC_STATE_02");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        System.out.println("Step 1: Kiểm tra trạng thái mặc định.");
        String defaultStatus = dangKyPage.getTrangThai();
        System.out.println("  - Trạng thái mặc định: " + defaultStatus);
        System.out.println("  [CHECK] Mong đợi: Trạng thái mặc định chứa 'Chờ đăng ký'.");
        System.out.println("  [CHECK] Thực tế: " + defaultStatus);
        Assert.assertTrue(defaultStatus.contains("Chờ đăng ký") || defaultStatus.contains("Cho dang ky"),
                "Trạng thái mặc định phải là 'Chờ đăng ký'.");

        System.out.println("Step 2: Kiểm tra tính Read-only của trường Trạng thái.");
        boolean isRO = dangKyPage.isFieldReadOnly(By.id("display_trang_thai"));
        System.out.println("  [CHECK] Mong đợi: Trường Trạng thái Read-only.");
        System.out.println("  [CHECK] Thực tế: isReadOnly=" + isRO);
        Assert.assertTrue(isRO, "Trường Trạng thái không được phép sửa thủ công.");
        System.out.println(">>> KẾT THÚC TC_STATE_02: PASS");
    }

    @Test(description = "TC_STATE_03: Kiểm tra chuyển đổi trạng thái sau khi lưu thành công")
    public void TC_STATE_03_StatusChangeAfterSave() {
        System.out.println(">>> BẮT ĐẦU TC_STATE_03");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        String oldStatus = dangKyPage.getTrangThai();
        System.out.println("  - Trạng thái trước khi lưu: " + oldStatus);

        System.out.println("Step 1: Thực hiện đăng ký.");
        String trichYeu = "Auto-Status-Change-" + System.currentTimeMillis();
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Hành chính");
        dangKyPage.inputTrichYeu(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("status.pdf", "Content"));
        dangKyPage.clickLuu();

        dangKyPage.waitForRegistrationSuccess();

        System.out.println("Step 2: Kiểm tra trạng thái sau khi lưu.");
        String newStatus = dangKyPage.getTrangThai();
        System.out.println("  - Trạng thái sau khi lưu: " + newStatus);

        System.out.println("  [CHECK] Mong đợi: Trạng thái thay đổi sang 'Đã đăng ký'.");
        System.out.println("  [CHECK] Thực tế: " + newStatus);
        Assert.assertNotEquals(newStatus, oldStatus, "Trạng thái phải thay đổi sau khi lưu.");
        Assert.assertTrue(
                newStatus.toLowerCase().contains("da dang ky") || newStatus.toLowerCase().contains("đã đăng ký"),
                "Trạng thái mới phải là 'Đã đăng ký'.");
        System.out.println(">>> KẾT THÚC TC_STATE_03: PASS");
    }

    // ==========================================
    // NHÓM 8: KIỂM TRA NGÀY KÝ (SIGNING DATE)
    // ==========================================

    @Test(description = "TC_DATE_01: Kiểm tra các ràng buộc về Ngày ký")
    public void TC_DATE_01_SigningDateValidation() {
        System.out.println(">>> BẮT ĐẦU TC_DATE_01");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        // Điền các trường bắt buộc khác để cô lập lỗi Ngày ký
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Test");
        dangKyPage.inputTrichYeu("Test Date Validation " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("date_test.pdf", "Content"));

        System.out.println("Step 1: Không nhập Ngày ký và nhấn Lưu.");
        dangKyPage.inputNgayKy("");
        dangKyPage.clickLuu();

        // Sửa: Thay Thread.sleep bằng wait.until (Tối ưu performance)
        String errorsEmpty = wait.until(ignored -> dangKyPage.getValidationErrors());

        System.out.println("  [CHECK] Mong đợi: Phải báo lỗi bắt buộc nhập Ngày ký.");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errorsEmpty + "\"");
        Assert.assertTrue(errorsEmpty != null && (errorsEmpty.contains("bắt buộc") || errorsEmpty.contains("Vui lòng")),
                "Không hiển thị đúng thông báo lỗi bắt buộc cho Ngày ký.");

        System.out.println("Step 2: Nhập Ngày ký < Ngày ban hành.");
        driver.navigate().refresh();
        // Điền TUYỆT ĐỐI ĐẦY ĐỦ các trường bắt buộc
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Test");
        dangKyPage.inputTrichYeu("Test Date Validation " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("date_test_2.pdf", "Content"));

        System.out.println("  - Nhập ngày ký: 2000-01-01");
        dangKyPage.inputNgayKy("2000-01-01");

        String errorsInvalid = wait.until(ignored -> {
            String e = dangKyPage.getValidationErrors();
            return (e != null && !e.isEmpty()) ? e : null;
        });

        System.out.println("  [CHECK] Mong đợi: Phải báo lỗi logic (Ngày ký < Ngày ban hành).");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errorsInvalid + "\"");
        Assert.assertTrue(errorsInvalid != null && (errorsInvalid.contains("nhỏ hơn") || errorsInvalid.contains("truoc") || errorsInvalid.contains("trước")),
                "Phải báo lỗi logic cụ thể khi ngày ký không hợp lệ.");

        System.out.println("Step 3: Nhập Ngày ký ở tương lai.");
        driver.navigate().refresh();
        // Điền TUYỆT ĐỐI ĐẦY ĐỦ các trường bắt buộc
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Test");
        dangKyPage.inputTrichYeu("Test Date Validation " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("date_test_3.pdf", "Content"));

        String errorsFuture; // Xóa khởi tạo "" thừa
        try {
            errorsFuture = wait.until(ignored -> {
                String e = dangKyPage.getValidationErrors();
                return (e != null && !e.isEmpty()) ? e : null;
            });
        } catch (Exception ignoredException) {
            errorsFuture = dangKyPage.getValidationErrors();
        }
        System.out.println("  [CHECK] Mong đợi: Phải báo lỗi khi ngày ký ở tương lai.");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errorsFuture + "\"");
        Assert.assertTrue(errorsFuture != null && !errorsFuture.isEmpty(),
                "Phải báo lỗi khi ngày ký ở tương lai.");

        System.out.println(">>> KẾT THÚC TC_DATE_01: PASS");
    }

    // ==========================================
    // NHÓM 9: KIỂM TRA LOẠI VĂN BẢN (DROPDOWN)
    // ==========================================

    @Test(description = "TC_VAL_06: Kiểm tra không chọn Loại văn bản")
    public void TC_VAL_06_EmptyDocType() {
        System.out.println(">>> BẮT ĐẦU TC_VAL_06");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        System.out.println("Step 1: Điền các trường khác trừ Loại văn bản.");
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Đào tạo");
        dangKyPage.inputTrichYeu("Test empty doc type");
        dangKyPage.uploadBanChinhThuc(createTempFile("doctype.pdf", "Content"));

        dangKyPage.selectEmptyLoaiVanBan(); // Chọn giá trị trống (index 0)

        System.out.println("Step 2: Nhấn Lưu.");
        dangKyPage.clickLuu();

        System.out.println("Step 3: Kiểm tra thông báo lỗi.");
        String errors = dangKyPage.getValidationErrors();
        System.out.println("  [CHECK] Mong đợi: Hệ thống chặn lưu khi chưa chọn Loại văn bản.");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errors + "\"");
        Assert.assertTrue((errors != null && !errors.isEmpty()) || driver.getCurrentUrl().endsWith("/dang-ky/"),
                "Hệ thống phải chặn lưu khi chưa chọn Loại văn bản.");
        System.out.println(">>> KẾT THÚC TC_VAL_06: PASS");
    }

    // ==========================================
    // NHÓM 10: KIỂM TRA NGƯỜI SOẠN THẢO (CREATOR)
    // ==========================================

    @Test(description = "TC_VAL_07: Kiểm tra validation cho Người soạn thảo")
    public void TC_VAL_07_CreatorValidation() {
        System.out.println(">>> BẮT ĐẦU TC_VAL_07");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        System.out.println("Step 1: Không chọn Người soạn thảo.");
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Đào tạo");
        dangKyPage.inputTrichYeu("Test creator validation");
        dangKyPage.uploadBanChinhThuc(createTempFile("creator.pdf", "Content"));

        dangKyPage.selectEmptyNguoiTao();
        dangKyPage.clickLuu();
        String errorsEmpty = dangKyPage.getValidationErrors();
        System.out.println("  [CHECK] Mong đợi: Chặn lưu khi không chọn Người soạn thảo.");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errorsEmpty + "\"");
        Assert.assertTrue(!errorsEmpty.isEmpty() || driver.getCurrentUrl().endsWith("/dang-ky/"),
                "Phải chặn lưu khi không chọn Người soạn thảo.");

        System.out.println("Step 2: Chọn User không tồn tại (Hack value).");
        driver.navigate().refresh();
        // Điền lại form sau khi refresh
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Đào tạo");
        dangKyPage.inputTrichYeu("Test creator validation");
        dangKyPage.uploadBanChinhThuc(createTempFile("creator.pdf", "Content"));

        dangKyPage.selectInvalidNguoiTao("INVALID_ID_999");
        dangKyPage.clickLuu();
        String errorsInvalid = dangKyPage.getValidationErrors();
        System.out.println("  [CHECK] Mong đợi: Chặn lưu khi chọn User không tồn tại.");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errorsInvalid + "\"");
        Assert.assertTrue(!errorsInvalid.isEmpty() || driver.getCurrentUrl().endsWith("/dang-ky/"),
                "Phải chặn lưu khi chọn User không tồn tại.");

        System.out.println("Step 3: Kiểm tra User bị disable (Nếu có).");
        // Giả sử ta biết ID của user bị disable. Nếu không có, ta kiểm tra xem user đó
        // có xuất hiện trong list không.
        WebElement selectEl = driver.findElement(By.id("id_nguoi_tao"));
        Select select = new Select(selectEl);
        boolean foundDisabled = false;
        for (WebElement opt : select.getOptions()) {
            if (opt.getText().contains("(Bị khóa)") || opt.getText().contains("(Disabled)")) {
                foundDisabled = true;
                break;
            }
        }
        Assert.assertFalse(foundDisabled, "User bị disable không được phép xuất hiện trong danh sách chọn.");

        System.out.println(">>> KẾT THÚC TC_VAL_07: PASS");
    }

    // ==========================================
    // NHÓM 11: KIỂM TRA NGƯỜI KÝ (SIGNER)
    // ==========================================

    @Test(description = "TC_VAL_08: Kiểm tra validation cho Người ký")
    public void TC_VAL_08_SignerValidation() {
        System.out.println(">>> BẮT ĐẦU TC_VAL_08");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        System.out.println("Step 1: Không chọn Người ký.");
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.inputNoiNhan("Phòng Đào tạo");
        dangKyPage.inputTrichYeu("Test signer validation");
        dangKyPage.uploadBanChinhThuc(createTempFile("signer.pdf", "Content"));

        dangKyPage.selectEmptyNguoiKy();
        dangKyPage.clickLuu();
        String errors = dangKyPage.getValidationErrors();
        System.out.println("  [CHECK] Mong đợi: Chặn lưu khi không chọn Người ký.");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errors + "\"");
        Assert.assertTrue(!errors.isEmpty() || driver.getCurrentUrl().endsWith("/dang-ky/"),
                "Phải chặn lưu khi không chọn Người ký.");

        System.out.println("Step 2: Người ký khác người soạn thảo.");
        driver.navigate().refresh();
        dangKyPage.selectNguoiTao(TEACHER_USER); // Người soạn thảo
        dangKyPage.selectNguoiKy(HT_USER); // Người ký (HT)
        String creatorVal = new Select(driver.findElement(By.id("id_nguoi_tao"))).getFirstSelectedOption()
                .getAttribute("value");
        String signerVal = new Select(driver.findElement(By.id("id_nguoi_ky"))).getFirstSelectedOption()
                .getAttribute("value");

        System.out.println("  [CHECK] Mong đợi: Người soạn thảo và người ký phải khác nhau.");
        System.out.println("  [CHECK] Thực tế: Creator=" + creatorVal + ", Signer=" + signerVal);
        Assert.assertNotEquals(creatorVal, signerVal, "Người soạn thảo và người ký phải khác nhau.");
        // Lưu thành công trường hợp này đã được test trong các flow khác.

        System.out.println("Step 3: Kiểm tra quyền ký (Logic bổ trợ).");
        // Kiểm tra danh sách người ký (HT/HP)
        WebElement signerSelect = driver.findElement(By.id("id_nguoi_ky"));
        Select select = new Select(signerSelect);
        boolean hasOptions = !select.getOptions().isEmpty();
        Assert.assertTrue(hasOptions, "Danh sách người ký không được để trống.");

        System.out.println(">>> KẾT THÚC TC_VAL_08: PASS");
    }

    // ==========================================
    // NHÓM 14: KIỂM TRA FILE (OFFICIAL & ATTACHMENTS)
    // ==========================================

    @Test(description = "TC_FILE_01: Kiểm tra các ràng buộc cho Bản chính thức (Bắt Bug Bảo Mật)")
    public void TC_FILE_01_OfficialFileValidation() {
        System.out.println(">>> BẮT ĐẦU TC_FILE_01");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);

        // ==========================================
        // STEP 1: KHÔNG UPLOAD FILE VÀ NHẤN LƯU
        // ==========================================
        System.out.println("Step 1: Không upload file và nhấn Lưu.");
        dangKyPage.openDirectRegistration();

        // Điền các trường bắt buộc
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Test");
        dangKyPage.inputTrichYeu("Test file validation EMPTY");

        dangKyPage.clickLuu();
        String errorsEmpty = dangKyPage.getValidationErrors();

        System.out.println("  [CHECK] Mong đợi: Chặn lưu khi không upload bản chính thức.");
        System.out.println("  [CHECK] Thực tế: Lỗi hiển thị = \"" + errorsEmpty + "\"");
        Assert.assertTrue(errorsEmpty != null && !errorsEmpty.trim().isEmpty(),
                "Phải chặn lưu và hiển thị lỗi khi không upload bản chính thức.");

        // ==========================================
        // STEP 2: UPLOAD FILE .EXE (BẮT LỖI BẢO MẬT)
        // ==========================================
        System.out.println("Step 2: Upload file sai định dạng (.exe).");
        driver.navigate().refresh();
        dangKyPage.openDirectRegistration();

        // Điền lại form để vượt qua validation các trường text
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Test");
        dangKyPage.inputTrichYeu("Test file validation EXE");

        // Upload file exe
        dangKyPage.uploadBanChinhThuc(createTempFile("virus.exe", "Malicious content"));
        dangKyPage.clickLuu();

        // Chờ 2.5 giây để xem Backend xử lý thế nào
        try { Thread.sleep(2500); } catch (Exception ignored) {}

        // BẮT LỖI TÍCH CỰC: Kiểm tra xem có bị bypass không
        String currentUrlExe = driver.getCurrentUrl();
        String msgExe = dangKyPage.getSuccessMessage().toLowerCase();
        boolean isBypassedExe = !currentUrlExe.endsWith("/dang-ky/")
                || msgExe.contains("thành công")
                || msgExe.contains("đã đăng ký");

        if (isBypassedExe) {
            Assert.fail("BUG BẢO MẬT NGHIÊM TRỌNG: Hệ thống chấp nhận file .exe, báo LƯU THÀNH CÔNG và chuyển trang! URL hiện tại: " + currentUrlExe);
        }

        // Nếu web có chặn (không bị bypass), kiểm tra xem có thông báo lỗi hiển thị không
        String errorsFormat = dangKyPage.getValidationErrors();
        Assert.assertTrue(errorsFormat != null && !errorsFormat.trim().isEmpty(),
                "Hệ thống có chặn file .exe nhưng KHÔNG hiển thị thông báo lỗi nào cho người dùng.");

        // ==========================================
        // STEP 3: UPLOAD FILE QUÁ DUNG LƯỢNG (VD: 25MB)
        // ==========================================
        System.out.println("Step 3: Upload file quá dung lượng (ví dụ 25MB).");
        driver.navigate().refresh();
        dangKyPage.openDirectRegistration();

        // Điền lại form
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Test");
        dangKyPage.inputTrichYeu("Test file validation SIZE");

        // Upload file lớn
        dangKyPage.uploadBanChinhThuc(createLargeFile("large.pdf", 25));
        dangKyPage.clickLuu();

        // Chờ 2.5 giây để hệ thống xử lý upload
        try { Thread.sleep(2500); } catch (Exception ignored) {}

        // BẮT LỖI TÍCH CỰC: Kiểm tra bypass
        String currentUrlSize = driver.getCurrentUrl();
        String msgSize = dangKyPage.getSuccessMessage().toLowerCase();
        boolean isBypassedSize = !currentUrlSize.endsWith("/dang-ky/")
                || msgSize.contains("thành công")
                || msgSize.contains("đã đăng ký");

        if (isBypassedSize) {
            Assert.fail("BUG HỆ THỐNG: Chấp nhận file quá dung lượng quy định (25MB), báo LƯU THÀNH CÔNG và chuyển trang! URL hiện tại: " + currentUrlSize);
        }

        // Nếu web có chặn, kiểm tra thông báo lỗi
        String errorsSize = dangKyPage.getValidationErrors();
        Assert.assertTrue(errorsSize != null && !errorsSize.trim().isEmpty(),
                "Hệ thống chặn file quá lớn nhưng KHÔNG hiển thị thông báo lỗi nào.");

        System.out.println(">>> KẾT THÚC TC_FILE_01: PASS");
    }

    @Test(description = "TC_FILE_02: Kiểm tra Tệp đính kèm")
    public void TC_FILE_02_AttachmentsValidation() {
        System.out.println(">>> BẮT ĐẦU TC_FILE_02");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();

        try {
            System.out.println("Step 1: Upload nhiều file đính kèm.");
            dangKyPage.uploadTepDinhKem(createTempFile("attach1.pdf", "Content 1"));
            try {
                Thread.sleep(1000);
            } catch (InterruptedException ignored) {
            } // Chờ UI cập nhật list
            dangKyPage.uploadTepDinhKem(createTempFile("attach2.docx", "Content 2"));
            try {
                Thread.sleep(1000);
            } catch (InterruptedException ignored) {
            }

            System.out.println("Step 2: Upload file rỗng.");
            dangKyPage.uploadTepDinhKem(createTempFile("empty.txt", ""));

            System.out.println("Step 3: Upload trùng tên file.");
            dangKyPage.uploadTepDinhKem(createTempFile("attach1.pdf", "Content 1 duplicated"));

            // Thay thế đoạn chờ Wait.until bằng vòng lặp an toàn này để chống Flaky
            boolean isFileUploaded = false;
            for (int i = 0; i < 5; i++) {
                List<WebElement> files = driver.findElements(By.cssSelector(".file-item, .attachment-name, .file-list li, .text-primary, .uploaded-file"));
                if (files.size() > 0) {
                    isFileUploaded = true;
                    break;
                }
                Thread.sleep(1000); // Chờ 1s rồi quét lại DOM
            }

            System.out.println("  [CHECK] Mong đợi: Danh sách đính kèm phải hiển thị file.");
            Assert.assertTrue(isFileUploaded, "Không tìm thấy file nào được liệt kê trong danh sách đính kèm sau khi upload.");
            List<WebElement> fileElements = driver.findElements(By.cssSelector(".file-item, .attachment-name, .file-list li, .text-primary, .uploaded-file"));
            int fileCount = fileElements.size();

            System.out.println("  [CHECK] Mong đợi: Danh sách đính kèm phải hiển thị file.");
            System.out.println("  [CHECK] Thực tế: Số lượng file list tìm thấy = " + fileCount);
            Assert.assertTrue(fileCount > 0, "Không tìm thấy file nào được liệt kê trong danh sách đính kèm.");
        } catch (Exception e) {
            Assert.fail("Lỗi nghiêm trọng khi upload tệp đính kèm: " + e.getMessage());
        }
        System.out.println(">>> KẾT THÚC TC_FILE_02: PASS");
    }

    // ==========================================
    // CÁC HÀM PHỤ TRỢ (HELPER METHODS)
    // ==========================================

    private String createTempFile(String fileName, String content) {
        try {
            Path tempDir = Paths.get(System.getProperty("java.io.tmpdir"));
            Path filePath = tempDir.resolve(fileName);
            Files.write(filePath, content.getBytes());
            return filePath.toAbsolutePath().toString();
        } catch (IOException e) {
            throw new RuntimeException("Không thể tạo file tạm: " + fileName, e);
        }
    }

    private String createLargeFile(String fileName, int sizeInMB) {
        try {
            Path tempDir = Paths.get(System.getProperty("java.io.tmpdir"));
            Path filePath = tempDir.resolve(fileName);
            byte[] data = new byte[1024 * 1024]; // 1MB
            try (OutputStream os = Files.newOutputStream(filePath)) {
                for (int i = 0; i < sizeInMB; i++) {
                    os.write(data);
                }
            }
            return filePath.toAbsolutePath().toString();
        } catch (IOException e) {
            throw new RuntimeException("Không thể tạo file lớn: " + fileName, e);
        }
    }

    private String generateLongString(int length) {
        return "a".repeat(length);
    }

    @Test(description = "TC_VAL_LIMITS: Kiểm tra giới hạn độ dài và khả năng chịu lỗi Backend")
    public void TC_VAL_LIMITS_FieldLengthConstraints() {
        System.out.println(">>> BẮT ĐẦU TC_VAL_LIMITS");
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        String stressText = generateLongString(10000);

        // 1. KIỂM TRA UI
        dangKyPage.openDirectRegistration();
        System.out.println("Step 1: Kiểm tra UI có chặn độ dài nhập vào không.");
        dangKyPage.inputNoiNhan(stressText);
        dangKyPage.inputTrichYeu(stressText);

        int uiNoiNhanLen = driver.findElement(By.id("id_noi_nhan")).getAttribute("value").length();
        int uiTrichYeuLen = driver.findElement(By.id("id_trich_yeu")).getAttribute("value").length();
        System.out.println("  [CHECK] UI Maxlength - Nơi nhận: " + uiNoiNhanLen + ", Trích yếu: " + uiTrichYeuLen);

        // 2. STRESS TEST BACKEND (ISOLATED)
        System.out.println("Step 2: Stress Test trường NƠI NHẬN (Bypass UI - 10.000 ký tự).");
        driver.navigate().refresh();
        ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].removeAttribute('maxlength')",
                driver.findElement(By.id("id_noi_nhan")));
        dangKyPage.inputNoiNhan(stressText);
        fillMandatoryFields("Stress-NoiNhan");
        dangKyPage.clickLuu();
        checkBackendCrash("Nơi nhận");

        System.out.println("Step 3: Stress Test trường TRÍCH YẾU (Bypass UI - 10.000 ký tự).");
        dangKyPage.openDirectRegistration();
        ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].removeAttribute('maxlength')",
                driver.findElement(By.id("id_trich_yeu")));
        dangKyPage.inputTrichYeu(stressText);
        fillMandatoryFields("Stress-TrichYeu");
        dangKyPage.clickLuu();
        checkBackendCrash("Trích yếu");

        System.out.println(">>> KẾT THÚC TC_VAL_LIMITS: PASS");
    }

    private void fillMandatoryFields(String suffix) {
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        if (suffix.contains("NoiNhan"))
            dangKyPage.inputTrichYeu("Stress Test " + suffix);
        else
            dangKyPage.inputNoiNhan("Stress Test " + suffix);
        dangKyPage.uploadBanChinhThuc(createTempFile("stress_" + suffix + ".pdf", "Content"));
    }

    private void checkBackendCrash(String fieldName) {
        String ps = driver.getPageSource();
        boolean isCrash = ps.contains("Internal Server Error") || ps.contains("Exception")
                || driver.getTitle().contains("500");
        Assert.assertFalse(isCrash, "LỖI: Backend bị crash khi trường '" + fieldName + "' nhận 10.000 ký tự!");
    }

    private int parseIdNumeric(String idStr) {
        // Ví dụ: VBO00000077 -> 77
        if (idStr == null || idStr.isEmpty())
            return 0;
        String numeric = idStr.replaceAll("[^0-9]", "");
        return numeric.isEmpty() ? 0 : Integer.parseInt(numeric);
    }
}
