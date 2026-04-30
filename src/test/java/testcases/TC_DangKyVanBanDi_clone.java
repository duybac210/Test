package testcases;

import common.Utilities;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
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

public class TC_DangKyVanBanDi_clone {
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

    @Test(description = "TC_01_SEC: Chặn truy cập với tài khoản không có quyền Văn thư")
    public void TC_01_SEC_BlockNonClerkAccess() {
        System.out.println(">>> BẮT ĐẦU TC_01_SEC");
        Utilities.loginAs(TEACHER_USER, TEACHER_PASS);
        driver.get("http://127.0.0.1:8000/van-ban-di/dang-ky/");
        String pageSource = driver.getPageSource();
        // Sửa: Kiểm tra nội dung chặn truy cập cụ thể, không chỉ URL
        boolean hasAccessError = pageSource.contains("Ban khong co quyen truy cap")
                || pageSource.contains("Permission Denied")
                || !driver.findElements(By.xpath("//*[contains(text(), '403') or contains(text(), '404')]")).isEmpty();

        System.out.println("  [CHECK] Mong đợi: Tài khoản không có quyền Văn thư phải bị chặn (Redirect hoặc báo lỗi).");
        System.out.println("  [CHECK] Thực tế: URL=" + driver.getCurrentUrl() + ", hasAccessError=" + hasAccessError);
        Assert.assertTrue(hasAccessError, "Tài khoản không có quyền Văn thư phải thấy thông báo bị chặn.");
        System.out.println(">>> KẾT THÚC TC_01_SEC: PASS");
    }

    @Test(description = "TC_02_SEC: Chặn đăng ký văn bản chưa được duyệt")
    public void TC_02_SEC_BlockUnapprovedDocRegistration() {
        System.out.println(">>> BẮT ĐẦU TC_02_SEC");
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
        System.out.println(">>> KẾT THÚC TC_02_SEC: PASS");
    }

    @Test(description = "TC_03_SEC: Chặn đăng ký cho văn bản đã đăng ký hoặc đang chờ duyệt")
    public void TC_03_SEC_BlockRegistrationForInvalidStatus() {
        System.out.println(">>> BẮT ĐẦU TC_03_SEC");
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

        System.out.println(">>> KẾT THÚC TC_03_SEC: PASS");
    }

    // ==========================================
    // NHÓM 2: LUỒNG NGHIỆP VỤ CHÍNH
    // ==========================================

    @Test(description = "TC_04_FLOW: Đăng ký thành công văn bản từ dự thảo (Luồng 1)")
    public void TC_04_FLOW_RegisterFromDraftSuccess() {
        System.out.println(">>> BẮT ĐẦU TC_04_FLOW");
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
        System.out.println(">>> KẾT THÚC TC_04_FLOW: PASS");
    }

    @Test(description = "TC_05_FLOW: Đăng ký mới văn bản trực tiếp (Luồng 2)")
    public void TC_05_FLOW_DirectRegistrationSuccess() {
        System.out.println(">>> BẮT ĐẦU TC_05_FLOW");
        loginAndOpenRegistration();
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
        System.out.println(">>> KẾT THÚC TC_05_FLOW: PASS");
    }

    @Test(description = "TC_06_FLOW: Chỉ nhập các trường bắt buộc và nhấn Lưu")
    public void TC_06_FLOW_RequiredFieldsOnly() {
        System.out.println(">>> BẮT ĐẦU TC_06_FLOW");
        loginAndOpenRegistration();

        String trichYeu = "Auto-RequiredOnly-" + System.currentTimeMillis();
        fillValidDataExceptFile(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("required.pdf", "Content"));

        dangKyPage.clickLuu();
        dangKyPage.waitForRegistrationSuccess();

        String actualMsg = dangKyPage.getSuccessMessage();
        
        // SỬA Ở ĐÂY: Thêm vế check không dấu "da dang ky" hoặc "thanh cong"
        boolean isSuccess = actualMsg.toLowerCase().contains("thành công") 
                         || actualMsg.toLowerCase().contains("đã đăng ký")
                         || actualMsg.toLowerCase().contains("thanh cong")
                         || actualMsg.toLowerCase().contains("da dang ky");
                         
        Assert.assertTrue(isSuccess, "Lưu không thành công: " + actualMsg);
        System.out.println(">>> KẾT THÚC TC_06_FLOW: PASS");
    }

    // ==========================================
    // NHÓM 3: VALIDATION CƠ BẢN & ĐỒNG THỜI
    // ==========================================

    @Test(description = "TC_07_VAL: Bỏ trống tất cả các trường và nhấn Lưu")
    public void TC_07_VAL_EmptyFieldsSave() {
        System.out.println(">>> BẮT ĐẦU TC_07_VAL");
        loginAndOpenRegistration();

        System.out.println("Step: Nhấn Lưu khi form trống.");
        dangKyPage.clickLuu();

        System.out.println("Step: Kiểm tra validation text.");
        String errors = dangKyPage.getValidationErrors();
        Assert.assertTrue(errors != null && !errors.isEmpty() && (errors.contains("bắt buộc") || errors.contains("Vui lòng")),
                "Hệ thống không hiển thị đúng thông báo lỗi bắt buộc khi bỏ trống form.");
        System.out.println(">>> KẾT THÚC TC_07_VAL: PASS");
    }

    @Test(description = "TC_08_CONC: Double click nút Lưu - Tránh tạo 2 bản ghi")
    public void TC_08_CONC_DoubleClickSave() {
        System.out.println(">>> BẮT ĐẦU TC_08_CONC");
        loginAndOpenRegistration();

        String trichYeu = "Auto-DoubleSubmit-" + System.currentTimeMillis();
        fillValidDataExceptFile(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("double.pdf", "Content"));

        dangKyPage.doubleClickLuu();
        dangKyPage.waitForRegistrationSuccess();

        // Đã thay thế driver.findElement lằng nhằng bằng 1 hàm gọi duy nhất
        int count = dangKyPage.countDocumentsInList(trichYeu);
        Assert.assertEquals(count, 1, "Chỉ được phép tạo 1 bản ghi duy nhất.");
        System.out.println(">>> KẾT THÚC TC_08_CONC: PASS");
    }

    // ==========================================
    // NHÓM 4: CẤP SỐ, ID & TRẠNG THÁI
    // ==========================================

    @Test(description = "TC_09_CAPSO: Kiểm tra định dạng số ký hiệu sau khi đăng ký")
    public void TC_09_CAPSO_AutoNumberingFormat() {
        System.out.println(">>> BẮT ĐẦU TC_09_CAPSO");
        loginAndOpenRegistration();
        
        fillValidDataExceptFile("Test numbering " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("test.pdf", "Content"));

        try { dangKyPage.clickCapSo(); } catch (Exception e) {}
        
        dangKyPage.clickLuu();
        dangKyPage.waitForRegistrationSuccess();

        String soKyHieu = dangKyPage.getSoKyHieu();
        Assert.assertFalse(soKyHieu.isEmpty(), "Số ký hiệu trống.");
        Assert.assertTrue(soKyHieu.contains("/") && soKyHieu.endsWith("THPTND"), "Số ký hiệu sai định dạng.");
        System.out.println(">>> KẾT THÚC TC_09_CAPSO: PASS");
    }

    @Test(description = "TC_10_ID: Kiểm tra số văn bản đi tự tăng +1")
    public void TC_10_ID_AutoIncrement() {
        System.out.println(">>> BẮT ĐẦU TC_10_ID");
        loginAndOpenRegistration();

        System.out.println("Step 1: Lấy số văn bản đi lớn nhất hiện tại.");
        String latestIdStr = dangKyPage.getLatestSoVBDiFromList();
        int latestId = parseIdNumeric(latestIdStr);

        System.out.println("Step 2: Đăng ký văn bản mới.");
        String trichYeu = "Auto-Increment-Test-" + System.currentTimeMillis();
        
        // SỬA Ở ĐÂY: Phải mở lại trang Đăng ký vì hàm getLatestSoVBDiFromList đã điều hướng đi nơi khác
        dangKyPage.openDirectRegistration(); 
        
        fillValidDataExceptFile(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("id_test.pdf", "Content"));
        dangKyPage.clickLuu();
        dangKyPage.waitForRegistrationSuccess();

        System.out.println("Step 3: Kiểm tra số văn bản đi mới.");
        String newIdStr = dangKyPage.getSoVBDi();
        int newId = parseIdNumeric(newIdStr);
        Assert.assertTrue(newId > latestId, "Số văn bản đi phải được cấp mới.");
        System.out.println(">>> KẾT THÚC TC_10_ID: PASS");
    }

    @Test(description = "TC_11_ID: Kiểm tra định dạng và tính Read-only của Số văn bản đi")
    public void TC_11_ID_FormatAndReadOnly() {
        System.out.println(">>> BẮT ĐẦU TC_11_ID");
        loginAndOpenRegistration();

        boolean isRO = dangKyPage.isSoVBDiReadOnly();
        String soVBDi = dangKyPage.getSoVBDi();
        Assert.assertTrue(isRO, "Số văn bản đi phải Read-only.");
        Assert.assertTrue(soVBDi.matches("VBO\\d{8}"), "Sai định dạng VBOxxxxxxxx.");
        System.out.println(">>> KẾT THÚC TC_11_ID: PASS");
    }

    @Test(description = "TC_12_STATE: Kiểm tra trạng thái mặc định và tính Read-only")
    public void TC_12_STATE_DefaultStatusAndReadOnly() {
        System.out.println(">>> BẮT ĐẦU TC_12_STATE");
        loginAndOpenRegistration();

        String defaultStatus = dangKyPage.getTrangThai();
        Assert.assertTrue(defaultStatus.contains("Chờ đăng ký") || defaultStatus.contains("Cho dang ky"),
                "Trạng thái mặc định sai.");
        
        boolean isRO = dangKyPage.isFieldReadOnly(By.id("display_trang_thai"));
        Assert.assertTrue(isRO, "Trường Trạng thái phải Read-only.");
        System.out.println(">>> KẾT THÚC TC_12_STATE: PASS");
    }

    @Test(description = "TC_13_STATE: Kiểm tra chế độ Read-only sau khi đăng ký")
    public void TC_13_STATE_ReadOnlyAfterRegistration() {
        System.out.println(">>> BẮT ĐẦU TC_13_STATE");
        loginAndOpenRegistration();
        String trichYeu = "Auto-ReadOnly-" + System.currentTimeMillis();

        registerDirectlyHelper(trichYeu);

        boolean isReadOnly = dangKyPage.isFieldReadOnly(By.id("id_trich_yeu"));
        int saveBtns = driver.findElements(By.cssSelector("button[type='submit']")).size();
        Assert.assertTrue(isReadOnly, "Trường Trích yếu phải Read-only.");
        Assert.assertEquals(saveBtns, 0, "Nút Lưu phải biến mất.");
        System.out.println(">>> KẾT THÚC TC_13_STATE: PASS");
    }

    @Test(description = "TC_14_STATE: Kiểm tra chuyển đổi trạng thái sau khi lưu thành công")
    public void TC_14_STATE_StatusChangeAfterSave() {
        System.out.println(">>> BẮT ĐẦU TC_14_STATE");
        loginAndOpenRegistration();

        String oldStatus = dangKyPage.getTrangThai();
        fillValidDataExceptFile("Auto-Status-Change-" + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("status.pdf", "Content"));
        dangKyPage.clickLuu();
        dangKyPage.waitForRegistrationSuccess();

        String newStatus = dangKyPage.getTrangThai();
        Assert.assertNotEquals(newStatus, oldStatus, "Trạng thái phải thay đổi.");
        
        // SỬA Ở ĐÂY: Thêm vế check không dấu "da dang ky"
        boolean isValidStatus = newStatus.toLowerCase().contains("đã đăng ký") 
                             || newStatus.toLowerCase().contains("da dang ky");
                             
        Assert.assertTrue(isValidStatus, "Trạng thái mới phải là 'Đã đăng ký', nhưng thực tế là: " + newStatus);
        System.out.println(">>> KẾT THÚC TC_14_STATE: PASS");
    }

    @Test(description = "TC_15_CANCEL: Kiểm tra nút Hủy (Reset form)")
    public void TC_15_CANCEL_CancelRegistration() {
        System.out.println(">>> BẮT ĐẦU TC_15_CANCEL");
        loginAndOpenRegistration();
        dangKyPage.inputTrichYeu("Dữ liệu tạm");
        dangKyPage.clickHuy();
        
        // Cập nhật lại:
        String value = dangKyPage.getTrichYeuValue();
        Assert.assertEquals(value, "", "Form chưa được reset.");
        System.out.println(">>> KẾT THÚC TC_15_CANCEL: PASS");
    }

    // ==========================================
    // NHÓM 5: VALIDATION NGÀY THÁNG & DROPDOWN
    // ==========================================

    @Test(description = "TC_16_DATE: Bỏ trống Ngày ký")
    public void TC_16_DATE_EmptySigningDate() {
        System.out.println(">>> BẮT ĐẦU TC_16_DATE");
        loginAndOpenRegistration();
        
        fillValidDataExceptFile("Test Date Empty - " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("date1.pdf", "Content"));
        dangKyPage.inputNgayKy(""); // Cố tình bỏ trống
        dangKyPage.clickLuu();

        String errors = wait.until(ignored -> dangKyPage.getValidationErrors());
        Assert.assertTrue(errors != null && (errors.contains("bắt buộc") || errors.contains("Vui lòng")),
                "Không hiển thị đúng thông báo lỗi bắt buộc cho Ngày ký.");
        System.out.println(">>> KẾT THÚC TC_16_DATE: PASS");
    }

    @Test(description = "TC_17_DATE: Ngày ký < Ngày ban hành (Logic lỗi)")
    public void TC_17_DATE_PastSigningDate() {
        System.out.println(">>> BẮT ĐẦU TC_17_DATE");
        loginAndOpenRegistration();

        fillValidDataExceptFile("Test Date Past - " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("date2.pdf", "Content"));
        dangKyPage.inputNgayKy("2000-01-01"); // Cố tình nhập quá khứ
        dangKyPage.clickLuu();

        // SỬA Ở ĐÂY: Bắt lỗi Timeout bằng Try-Catch để báo cáo Bug Backend
        String errors = null;
        try {
            errors = wait.until(ignored -> {
                String e = dangKyPage.getValidationErrors();
                return (e != null && !e.isEmpty()) ? e : null;
            });
        } catch (org.openqa.selenium.TimeoutException ex) {
            String actualMsg = dangKyPage.getSuccessMessage();
            Assert.fail("BUG LOGIC NGHIÊM TRỌNG: Hệ thống chấp nhận Ngày ký trong quá khứ! Báo cáo từ web: '" + actualMsg + "'");
        }

        Assert.assertTrue(errors != null && (errors.contains("nhỏ hơn") || errors.contains("trước")),
                "Phải báo lỗi logic cụ thể khi ngày ký không hợp lệ.");
        System.out.println(">>> KẾT THÚC TC_17_DATE: PASS");
    }

    @Test(description = "TC_18_DATE: Ngày ký ở tương lai")
    public void TC_18_DATE_FutureSigningDate() {
        System.out.println(">>> BẮT ĐẦU TC_18_DATE");
        loginAndOpenRegistration();

        fillValidDataExceptFile("Test Date Future - " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("date3.pdf", "Content"));
        dangKyPage.inputNgayKy("2099-12-31"); // Cố tình nhập tương lai
        dangKyPage.clickLuu();

        // SỬA Ở ĐÂY: Tương tự như TC_17
        String errors = null;
        try {
            errors = wait.until(ignored -> {
                String e = dangKyPage.getValidationErrors();
                return (e != null && !e.isEmpty()) ? e : null;
            });
        } catch (org.openqa.selenium.TimeoutException ex) {
            String actualMsg = dangKyPage.getSuccessMessage();
            Assert.fail("BUG LOGIC NGHIÊM TRỌNG: Hệ thống chấp nhận Ngày ký ở tương lai! Báo cáo từ web: '" + actualMsg + "'");
        }

        Assert.assertTrue(errors != null && !errors.isEmpty(), "Phải báo lỗi khi ngày ký ở tương lai.");
        System.out.println(">>> KẾT THÚC TC_18_DATE: PASS");
    }

    @Test(description = "TC_19_VAL: Kiểm tra không chọn Loại văn bản")
    public void TC_19_VAL_EmptyDocType() {
        System.out.println(">>> BẮT ĐẦU TC_19_VAL");
        loginAndOpenRegistration();

        fillValidDataExceptFile("Test empty doc type");
        dangKyPage.uploadBanChinhThuc(createTempFile("doctype.pdf", "Content"));
        
        dangKyPage.selectEmptyLoaiVanBan(); 
        dangKyPage.clickLuu();

        String errors = dangKyPage.getValidationErrors();
        Assert.assertTrue((errors != null && !errors.isEmpty()) || driver.getCurrentUrl().endsWith("/dang-ky/"),
                "Hệ thống phải chặn lưu khi chưa chọn Loại văn bản.");
        System.out.println(">>> KẾT THÚC TC_19_VAL: PASS");
    }

    @Test(description = "TC_20_VAL: Kiểm tra validation cho Người soạn thảo")
    public void TC_20_VAL_CreatorValidation() {
        System.out.println(">>> BẮT ĐẦU TC_20_VAL");
        loginAndOpenRegistration();

        fillValidDataExceptFile("Test creator validation");
        dangKyPage.uploadBanChinhThuc(createTempFile("creator.pdf", "Content"));
        
        dangKyPage.selectEmptyNguoiTao();
        dangKyPage.clickLuu();
        
        String errorsEmpty = dangKyPage.getValidationErrors();
        Assert.assertTrue(!errorsEmpty.isEmpty() || driver.getCurrentUrl().endsWith("/dang-ky/"),
                "Phải chặn lưu khi không chọn Người soạn thảo.");
        System.out.println(">>> KẾT THÚC TC_20_VAL: PASS");
    }

    @Test(description = "TC_21_VAL: Kiểm tra validation cho Người ký")
    public void TC_21_VAL_SignerValidation() {
        System.out.println(">>> BẮT ĐẦU TC_21_VAL");
        loginAndOpenRegistration();

        fillValidDataExceptFile("Test signer validation");
        dangKyPage.uploadBanChinhThuc(createTempFile("signer.pdf", "Content"));
        
        dangKyPage.selectEmptyNguoiKy();
        dangKyPage.clickLuu();
        
        String errors = dangKyPage.getValidationErrors();
        Assert.assertTrue(!errors.isEmpty() || driver.getCurrentUrl().endsWith("/dang-ky/"),
                "Phải chặn lưu khi không chọn Người ký.");
        System.out.println(">>> KẾT THÚC TC_21_VAL: PASS");
    }

    // ==========================================
    // NHÓM 6: XỬ LÝ TỆP (FILE UPLOAD)
    // ==========================================

    @Test(description = "TC_22_FILE: Bắt buộc upload Bản chính thức")
    public void TC_22_FILE_EmptyFileValidation() {
        System.out.println(">>> BẮT ĐẦU TC_22_FILE");
        loginAndOpenRegistration();

        fillValidDataExceptFile("Test file validation EMPTY - " + System.currentTimeMillis());
        dangKyPage.clickLuu();

        String errorsEmpty = dangKyPage.getValidationErrors();
        if (errorsEmpty == null || errorsEmpty.trim().isEmpty()) {
            Assert.fail("LỖI: Bỏ trống file nhưng hệ thống không chặn!");
        }
        System.out.println(">>> KẾT THÚC TC_22_FILE: PASS");
    }

    @Test(description = "TC_23_FILE: Chặn upload file thực thi (.exe) để bảo mật")
    public void TC_23_FILE_ExeFileSecurity() {
        System.out.println(">>> BẮT ĐẦU TC_23_FILE");
        loginAndOpenRegistration();

        fillValidDataExceptFile("Test Security EXE - " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createTempFile("virus.exe", "Malicious content"));
        dangKyPage.clickLuu();

        String errorsFormat = verifyNoBypassAndGetErrors("BẢO MẬT: Chấp nhận lưu file .exe");
        if (errorsFormat == null || errorsFormat.trim().isEmpty()) {
            Assert.fail("LỖI: Chặn file .exe nhưng KHÔNG báo lỗi.");
        }
        System.out.println(">>> KẾT THÚC TC_23_FILE: PASS");
    }

    @Test(description = "TC_24_FILE: Chặn upload file vượt quá dung lượng quy định (25MB)")
    public void TC_24_FILE_OversizedFile() {
        System.out.println(">>> BẮT ĐẦU TC_24_FILE");
        loginAndOpenRegistration();

        fillValidDataExceptFile("Test Size Limit - " + System.currentTimeMillis());
        dangKyPage.uploadBanChinhThuc(createLargeFile("large_test.pdf", 25));
        dangKyPage.clickLuu();

        String errorsSize = verifyNoBypassAndGetErrors("HỆ THỐNG: Chấp nhận file > 25MB");
        if (errorsSize == null || errorsSize.trim().isEmpty()) {
            Assert.fail("LỖI: Chặn file lớn nhưng KHÔNG báo lỗi cho User.");
        }
        System.out.println(">>> KẾT THÚC TC_24_FILE: PASS");
    }

    @Test(description = "TC_25A_FILE: Đính kèm thành công nhiều file hợp lệ")
    public void TC_25A_FILE_MultipleAttachments() {
        System.out.println(">>> BẮT ĐẦU TC_25A_FILE");
        loginAndOpenRegistration();

        System.out.println("  [STEP 1] Upload nhiều file định dạng khác nhau CÙNG LÚC");
        String file1 = createTempFile("attach1.pdf", "Content 1");
        String file2 = createTempFile("attach2.docx", "Content 2");
        
        // SỬA Ở ĐÂY: Truyền 2 file vào cùng 1 lệnh sendKeys
        dangKyPage.uploadTepDinhKem(file1, file2);

        System.out.println("  [STEP 2] Kiểm tra danh sách hiển thị");
        int fileCount = dangKyPage.getUploadedFilesCount();
        Assert.assertTrue(fileCount >= 2, "LỖI: Không hiển thị đủ 2 file đính kèm.");
        System.out.println(">>> KẾT THÚC TC_25A_FILE: PASS");
    }

    @Test(description = "TC_25B_FILE: Xử lý khi upload tệp đính kèm rỗng (0 KB)")
    public void TC_25B_FILE_EmptyAttachment() {
        System.out.println(">>> BẮT ĐẦU TC_25B_FILE");
        loginAndOpenRegistration();

        System.out.println("  [STEP 1] Upload 1 file rỗng");
        dangKyPage.uploadTepDinhKem(createTempFile("empty.txt", ""));
        
        System.out.println("  [STEP 2] Đánh giá phản ứng của hệ thống");
        int fileCount = dangKyPage.getUploadedFilesCount();
        String errors = dangKyPage.getValidationErrors();
        
        // Assert: Nếu file không được thêm vào list (count == 0), HOẶC hệ thống văng text cảnh báo lỗi
        Assert.assertTrue(fileCount == 0 || (errors != null && !errors.isEmpty()), 
            "LỖI: Hệ thống chấp nhận file rỗng mà không có bất kỳ cảnh báo nào.");
        System.out.println(">>> KẾT THÚC TC_25B_FILE: PASS");
    }

    @Test(description = "TC_25C_FILE: Xử lý khi upload tệp đính kèm trùng tên")
    public void TC_25C_FILE_DuplicateAttachment() {
        System.out.println(">>> BẮT ĐẦU TC_25C_FILE");
        loginAndOpenRegistration();

        System.out.println("  [STEP 1] Upload cùng 1 file 2 lần CÙNG LÚC");
        String filePath = createTempFile("duplicate.pdf", "Content");
        
        // SỬA Ở ĐÂY: Truyền cùng 1 file vào 2 lần để giả lập tải file trùng tên
        dangKyPage.uploadTepDinhKem(filePath, filePath);

        System.out.println("  [STEP 2] Đánh giá phản ứng của hệ thống");
        int fileCount = dangKyPage.getUploadedFilesCount();
        String errors = dangKyPage.getValidationErrors();

        Assert.assertTrue(fileCount == 2 || (errors != null && !errors.isEmpty()), 
            "LỖI: Xử lý file trùng tên không hợp lý (Vừa không báo lỗi, vừa đè mất file).");
        System.out.println(">>> KẾT THÚC TC_25C_FILE: PASS");
    }

    // ==========================================
    // CÁC HÀM PHỤ TRỢ (HELPER METHODS)
    // ==========================================
    /** HELPER 1: Đăng nhập và mở nhanh trang Đăng ký */
    private void loginAndOpenRegistration() {
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        dangKyPage.openDirectRegistration();
    }

    /** HELPER 2: Thực hiện đăng ký trực tiếp để tái sử dụng giữa các Test Case */
    private String registerDirectlyHelper(String trichYeu) {
        if (!driver.getCurrentUrl().endsWith("/dang-ky/")) {
            dangKyPage.openDirectRegistration();
        }
        fillValidDataExceptFile(trichYeu);
        dangKyPage.uploadBanChinhThuc(createTempFile("direct.pdf", "Content"));
        dangKyPage.clickLuu();
        dangKyPage.waitForRegistrationSuccess();
        return dangKyPage.getSoVBDi();
    }

    /** HELPER 3: Chờ 15s, kiểm tra Bypass file và trả về lỗi UI */
    private String verifyNoBypassAndGetErrors(String failMessage) {
        try {
            wait.until(d -> {
                String err = dangKyPage.getValidationErrors();
                return (err != null && !err.trim().isEmpty()) || !d.getCurrentUrl().endsWith("/dang-ky/");
            });
        } catch (org.openqa.selenium.TimeoutException e) {
            System.out.println("  [CẢNH BÁO] Đã hết 15s chờ đợi phản hồi từ Server.");
        }

        String currentUrl = driver.getCurrentUrl();
        String actualMsg = dangKyPage.getSuccessMessage();
        
        boolean isBypassed = !currentUrl.endsWith("/dang-ky/") 
                || actualMsg.toLowerCase().contains("thành công") 
                || actualMsg.toLowerCase().contains("đã đăng ký");

        if (isBypassed) {
            Assert.fail("BUG " + failMessage + "! Hệ thống báo: '" + actualMsg + "' | URL: " + currentUrl);
        }
        return dangKyPage.getValidationErrors();
    }

    /**
     * Helper: Điền toàn bộ thông tin hợp lệ vào form Đăng ký văn bản đi,
     * NGOẠI TRỪ tệp đính kèm (Bản chính thức).
     */
    private void fillValidDataExceptFile(String trichYeu) {
        dangKyPage.inputNgayKy("2026-04-28");
        dangKyPage.selectLoaiVanBan("LVB0000013");
        dangKyPage.selectMucDo("MD00000001");
        dangKyPage.selectNguoiTao(TEACHER_USER);
        dangKyPage.selectNguoiKy(HT_USER);
        dangKyPage.inputNoiNhan("Phòng Test Automation");
        dangKyPage.inputTrichYeu(trichYeu);
    }

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

    // ==========================================
    // NHÓM 7: KIỂM THỬ GIỚI HẠN (BOUNDARY / STRESS)
    // ==========================================

    @Test(description = "TC_26_LIMIT_UI: Kiểm tra UI có chặn độ dài nhập vào không (Maxlength)")
    public void TC_26_LIMIT_UI_Constraints() {
        System.out.println(">>> BẮT ĐẦU TC_26_LIMIT_UI");
        loginAndOpenRegistration();
        String stressText = generateLongString(10000);

        dangKyPage.inputNoiNhan(stressText);
        dangKyPage.inputTrichYeu(stressText);

        int uiNoiNhanLen = driver.findElement(By.id("id_noi_nhan")).getAttribute("value").length();
        int uiTrichYeuLen = driver.findElement(By.id("id_trich_yeu")).getAttribute("value").length();
        
        Assert.assertTrue(uiNoiNhanLen < 10000 && uiTrichYeuLen < 10000, "LỖI: UI không chặn Maxlength!");
        System.out.println(">>> KẾT THÚC TC_26_LIMIT_UI: PASS");
    }

    @Test(description = "TC_27_LIMIT_BACKEND: Stress Test Backend chống Crash (Error 500)")
    public void TC_27_LIMIT_BACKEND_AntiCrash() {
        System.out.println(">>> BẮT ĐẦU TC_27_LIMIT_BACKEND");
        loginAndOpenRegistration();
        String stressText = generateLongString(10000);

        // Bypass UI maxlength cho trường Nơi Nhận
        ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].removeAttribute('maxlength')",
                driver.findElement(By.id("id_noi_nhan")));
        
        fillValidDataExceptFile("Stress Test Backend");
        dangKyPage.inputNoiNhan(stressText); // Ghi đè chữ dài 10k ký tự
        dangKyPage.uploadBanChinhThuc(createTempFile("stress.pdf", "Content"));
        dangKyPage.clickLuu();

        String ps = driver.getPageSource();
        boolean isCrash = ps.contains("Internal Server Error") || ps.contains("Exception") || driver.getTitle().contains("500");
        Assert.assertFalse(isCrash, "LỖI TÀN KHỐC: Backend bị crash (Error 500) khi nhận chuỗi quá dài!");
        System.out.println(">>> KẾT THÚC TC_27_LIMIT_BACKEND: PASS");
    }

    private int parseIdNumeric(String idStr) {
        // Ví dụ: VBO00000077 -> 77
        if (idStr == null || idStr.isEmpty())
            return 0;
        String numeric = idStr.replaceAll("[^0-9]", "");
        return numeric.isEmpty() ? 0 : Integer.parseInt(numeric);
    }
}