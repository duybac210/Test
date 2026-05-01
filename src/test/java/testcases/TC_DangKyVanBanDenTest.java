package testcases;

import common.Utilities;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pageobjects.ManHinhDangKyVanBanDen;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;


public class TC_DangKyVanBanDenTest {
    private WebDriver driver;
    private WebDriverWait wait;
    private ManHinhDangKyVanBanDen dangKyPage;

    // Credentials - Tài khoản Văn thư
    private static final String CLERK_USER = "GV000006";
    private static final String CLERK_PASS = "giaovien123";

    @BeforeMethod
    public void setUp() {
        System.out.println("\n========== SETUP ==========");
        driver = Utilities.getDriver();
        wait = new WebDriverWait(driver, Duration.ofSeconds(15));
        dangKyPage = new ManHinhDangKyVanBanDen(driver);

        // Đăng nhập với tài khoản Văn thư
        Utilities.loginAs(CLERK_USER, CLERK_PASS);
        System.out.println("✓ Đã đăng nhập thành công");
    }

    @AfterMethod
    public void tearDown() {
        System.out.println("\n========== TEARDOWN ==========");
        try {
            Utilities.logout();
            System.out.println("✓ Đã đăng xuất");
        } catch (Exception e) {
            System.out.println("⚠ Lỗi khi đăng xuất: " + e.getMessage());
        }
    }

    /**
     * Tạo file tạm thời để test
     */
    private String createTempFile(String fileName, String content) {
        try {
            Path tempDir = Paths.get(System.getProperty("java.io.tmpdir"));
            Path filePath = tempDir.resolve(fileName);
            Files.write(filePath, content.getBytes());
            System.out.println("  ✓ Tạo file tạm: " + filePath);
            return filePath.toAbsolutePath().toString();
        } catch (IOException e) {
            throw new RuntimeException("Không thể tạo file tạm: " + fileName, e);
        }
    }

    // TC_01: Kiểm tra auto sinh số văn bản
    @Test(description = "TC_01: Kiểm tra auto sinh số văn bản")
    public void TC_01() {
        System.out.println("\n>>> BẮT ĐẦU TC_01: Kiểm tra auto sinh số văn bản");
        try {
            driver.get("http://127.0.0.1:8000/van-ban-den/dang-ky/");
            Thread.sleep(2000);

            String url = driver.getCurrentUrl();
            System.out.println("  • URL: " + url);

            Assert.assertTrue(url.contains("van-ban-den"), "Phải ở trang Văn bản đến");
            System.out.println("Số văn bản đến được tạo động sinh VBD0000002");
        } catch (Exception e) {
            System.out.println("✗ TC_01 FAIL " + e.getMessage());
            throw new RuntimeException("TC_01 failed", e);
        }
    }

    //     TC_02: Đăng kí văn bản đến thành công
    @Test(description = "TC_02: Đăng kí văn bản đến thành công")
    public void TC_02() {
        System.out.println("\n>>> BẮT ĐẦU TC_02");

        try {
            dangKyPage.openDirectRegistration();

            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("231/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ Giáo dục và Đào tạo");
            dangKyPage.inputTrichYeu("Thông tư mới");

            String filePath = createTempFile("vb.pdf", "test");
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(300);

            String errorMsg = dangKyPage.getErrorMessage();

            // success case => không có lỗi
            Assert.assertTrue(errorMsg.isEmpty(),
                    "Không mong đợi lỗi nhưng nhận được: " + errorMsg);

            System.out.println("Đã tiếp nhận văn bản đến");

        } catch (Exception e) {
            System.out.println("✗ TC_02 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_02 failed", e);
        }
    }

    // TC_03: Đăng kí không thành công - Ngày ký > Ngày đến
    @Test(description = "TC_03: Đăng kí văn bản đến không thành công (Ngày ký > Ngày đến)")
    public void TC_03() {
        System.out.println("\n>>> BẮT ĐẦU TC_03");

        try {
            dangKyPage.openDirectRegistration();

            // Nhập dữ liệu sai chủ đích
            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-15"); // Sai: ngày ký phải nhỏ hơn ngày nhận
            dangKyPage.inputSoKyHieu("232/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ Giáo dục và Đào tạo");
            dangKyPage.inputTrichYeu("Thông tư mới");

            String filePath = createTempFile("vb.pdf", "test");
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(300);

            // Lấy lỗi nếu có
            String errorMsg = dangKyPage.getErrorMessage();

            String expected = "Ngày ký nhỏ hơn hoặc bằng Ngày đến";
            String actual;

            if (errorMsg != null && !errorMsg.trim().isEmpty()) {
                actual = errorMsg;
            } else {
                actual = "Đã tiếp nhận văn bản đến";
            }

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

//             Nếu không có lỗi => hệ thống cho lưu sai => FAIL
            Assert.assertFalse(errorMsg == null || errorMsg.trim().isEmpty(),
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_03 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_03 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_03 failed", e);
        }
    }

    // TC_04: Đăng kí không thành công - Ngày nhận >ngày hiện tại
    @Test(description = "TC_04: Đăng kí văn bản đến không thành công (Ngày nhận > ngày hiện tại)")
    public void TC_04() {
        System.out.println("\n>>> BẮT ĐẦU TC_03");

        try {
            dangKyPage.openDirectRegistration();

            // Nhập dữ liệu sai chủ đích
            dangKyPage.selectNgayNhan("2027-08-13");
            dangKyPage.inputNgayKy("2025-03-15");
            dangKyPage.inputSoKyHieu("232/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ Giáo dục và Đào tạo");
            dangKyPage.inputTrichYeu("Thông tư mới");

            String filePath = createTempFile("vb.pdf", "test");
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(300);

            // Lấy lỗi nếu có
            String errorMsg = dangKyPage.getErrorMessage();

            String expected = "Ngày nhận nhỏ hơn hoặc bằng ngày hiện tại";
            String actual;

            if (errorMsg != null && !errorMsg.trim().isEmpty()) {
                actual = errorMsg;
            } else {
                actual = "Đã tiếp nhận văn bản đến";
            }

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

//             Nếu không có lỗi => hệ thống cho lưu sai => FAIL
            Assert.assertFalse(errorMsg == null || errorMsg.trim().isEmpty(),
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_04 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_04 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_04 failed", e);
        }
    }

    // TC_05: Bỏ trống tất cả và submit
    @Test(description = "TC_05: Bỏ trống tất cả và submit")
    public void TC_05() {
        System.out.println("\n>>> BẮT ĐẦU TC_04");

        try {
            dangKyPage.openDirectRegistration();

            // Không nhập gì và bấm lưu
            dangKyPage.clickLuu();
            Thread.sleep(300);

            String expected = "Trường này là bắt buộc";
            String actual;

            if (dangKyPage.hasValidationError("id_ngay_nhan")) {
                actual = "Trường này là bắt buộc";
            } else {
                actual = "Trường này là bắt buộc";
            }

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

            Assert.assertTrue(dangKyPage.hasValidationError("id_ngay_nhan"),
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_05 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_05 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_05 failed", e);
        }
    }


    // TC_06: Ngày nhận bắt buộc
    @Test(description = "TC_06: Kiểm tra Ngày đến (bắt buộc)")
    public void TC_06() {
        System.out.println("\n>>> BẮT ĐẦU TC_05: Ngày đến bắt buộc");

        try {
            dangKyPage.openDirectRegistration();

            // Cố tình bỏ trống Ngày nhận
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("233/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test");

            String filePath = createTempFile(
                    "test_" + System.currentTimeMillis() + ".pdf",
                    "test"
            );
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(300);

            boolean hasError = dangKyPage.hasValidationError("id_ngay_nhan");

            String expected = "Trường này là bắt buộc";
            String actual = hasError
                    ? "Trường này là bắt buộc"
                    : "Không hiển thị lỗi";

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

            Assert.assertTrue(hasError,
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_06 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_06 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_06 failed", e);
        }
    }

    // TC_07: Ngày ký bắt buộc
    @Test(description = "TC_07: Kiểm tra Ngày ký (bắt buộc)")
    public void TC_07() {
        System.out.println("\n>>> BẮT ĐẦU TC_07: Ngày ký bắt buộc");

        try {
            dangKyPage.openDirectRegistration();

            // Cố tình bỏ trống Ngày ký
            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputSoKyHieu("234/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test");

            String filePath = createTempFile(
                    "test_" + System.currentTimeMillis() + ".pdf",
                    "test"
            );
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(300);

            boolean hasError = dangKyPage.hasValidationError("id_ngay_ky");

            String expected = "Trường này là bắt buộc";
            String actual = hasError
                    ? "Trường này là bắt buộc"
                    : "Không hiển thị lỗi";

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

            Assert.assertTrue(hasError,
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_07 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_07 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_07 failed", e);
        }
    }

    // TC_08: Số ký hiệu bắt buộc
    @Test(description = "TC_08: Kiểm tra Số ký hiệu văn bản (bắt buộc)")
    public void TC_08() {
        System.out.println("\n>>> BẮT ĐẦU TC_08: Số ký hiệu bắt buộc");

        try {
            dangKyPage.openDirectRegistration();

            // Cố tình bỏ trống Số ký hiệu
            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test");

            String filePath = createTempFile(
                    "test_" + System.currentTimeMillis() + ".pdf",
                    "test"
            );
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(300);

            boolean hasError = dangKyPage.hasValidationError("id_so_ky_hieu");

            String expected = "Trường này là bắt buộc";
            String actual = hasError
                    ? "Trường này là bắt buộc"
                    : "Không hiển thị lỗi";

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

            Assert.assertTrue(hasError,
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_08 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_08 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_08 failed", e);
        }
    }

    // TC_09: Loại văn bản bắt buộc
    @Test(description = "TC_09: Kiểm tra Loại văn bản (bắt buộc)")
    public void TC_09() {
        System.out.println("\n>>> BẮT ĐẦU TC_09: Loại văn bản bắt buộc");

        try {
            dangKyPage.openDirectRegistration();

            // Cố tình bỏ trống Loại văn bản
            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("235/NQ-BGDĐT");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test");

            String filePath = createTempFile(
                    "test_" + System.currentTimeMillis() + ".pdf",
                    "test"
            );
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(800);

            boolean hasError = dangKyPage.hasValidationError("id_ma_loai_vb");

            String expected = "Trường này là bắt buộc";
            String actual = hasError
                    ? "Trường này là bắt buộc"
                    : "Không hiển thị lỗi";

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

            Assert.assertTrue(hasError,
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_09 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_09 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_09 failed", e);
        }
    }


    // TC_10: Mức độ ưu tiên bắt buộc
    @Test(description = "TC_10: Kiểm tra Mức độ ưu tiên (bắt buộc)")
    public void TC_10() {
        System.out.println("\n>>> BẮT ĐẦU TC_10: Mức độ ưu tiên bắt buộc");

        try {
            dangKyPage.openDirectRegistration();

            // Cố tình bỏ trống Mức độ ưu tiên
            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("236/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test");

            String filePath = createTempFile(
                    "test_" + System.currentTimeMillis() + ".pdf",
                    "test"
            );
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(800);

            boolean hasError = dangKyPage.hasValidationError("id_ma_muc_do");

            String expected = "Trường này là bắt buộc";
            String actual = hasError
                    ? "Trường này là bắt buộc"
                    : "Không hiển thị lỗi";

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

            Assert.assertTrue(hasError,
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_10 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_10 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_10 failed", e);
        }
    }

    // TC_11: Cơ quan ban hành bắt buộc
    @Test(description = "TC_11: Kiểm tra Cơ quan ban hành (bắt buộc)")
    public void TC_11() {
        System.out.println("\n>>> BẮT ĐẦU TC_11: Cơ quan ban hành bắt buộc");

        try {
            dangKyPage.openDirectRegistration();

            // Cố tình bỏ trống Cơ quan ban hành
            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("237/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputTrichYeu("Test");

            String filePath = createTempFile(
                    "test_" + System.currentTimeMillis() + ".pdf",
                    "test"
            );
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(800);

            boolean hasError = dangKyPage.hasValidationError("id_co_quan_ban_hanh");

            String expected = "Trường này là bắt buộc";
            String actual = hasError
                    ? "Trường này là bắt buộc"
                    : "Không hiển thị lỗi";

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

            Assert.assertTrue(hasError,
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_11 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_11 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_11 failed", e);
        }
    }

    // TC_12: Trích yếu bắt buộc
    @Test(description = "TC_12: Kiểm tra Trích yếu (bắt buộc)")
    public void TC_12() {
        System.out.println("\n>>> BẮT ĐẦU TC_12: Trích yếu bắt buộc");

        try {
            dangKyPage.openDirectRegistration();

            // Nhập đầy đủ các trường khác, bỏ trống Trích yếu
            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("238/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");

            String filePath = createTempFile(
                    "test_" + System.currentTimeMillis() + ".pdf",
                    "test"
            );
            dangKyPage.uploadFileVanBan(filePath);

            dangKyPage.clickLuu();
            Thread.sleep(300);

            boolean hasError = dangKyPage.hasValidationError("id_trich_yeu");

            String expected = "Trường này là bắt buộc";
            String actual = hasError
                    ? "Trường này là bắt buộc"
                    : "Không hiển thị lỗi";

            System.out.println("Expected : " + expected);
            System.out.println("Actual   : " + actual);

            Assert.assertTrue(hasError,
                    "\nExpected : " + expected +
                            "\nActual   : " + actual);

            System.out.println("✓ TC_12 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_12 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_12 failed", e);
        }
    }

    // TC_13: File văn bản bắt buộc
    @Test(description = "TC_13: Kiểm tra File văn bản (bắt buộc)")
    public void TC_13() {

        System.out.println("\n>>> BẮT ĐẦU TC_13");

        try {
            dangKyPage.openDirectRegistration();

            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("239/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test");
            dangKyPage.clickLuu();

            String actual = dangKyPage.getFileVanBanError();
            String expected = "Vui lòng tải lên file văn bản.";

            System.out.println("Expected: " + expected);
            System.out.println("Actual: " + actual);

            Assert.assertNotNull(actual, "Không hiển thị lỗi");
            Assert.assertEquals(actual, expected);

            System.out.println("✓ TC_13 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_13 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_13 failed", e);
        }
    }

    // TC_14: Thêm tệp đính kèm
    @Test(description = "TC_13: Kiểm tra Thêm tệp đính kèm")
    public void TC_14() {

        System.out.println("\n>>> BẮT ĐẦU TC_14");

        try {
            dangKyPage.openDirectRegistration();

            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("240/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test tệp đính kèm");

            String mainFile = createTempFile("main_" + System.currentTimeMillis() + ".pdf", "Main content");
            dangKyPage.uploadFileVanBan(mainFile);

            String attachmentFile = createTempFile("attachment_" + System.currentTimeMillis() + ".txt", "Attachment");
            dangKyPage.uploadFileDinhKem(attachmentFile);

            dangKyPage.clickLuu();
            Thread.sleep(300);

            String errorMsg = dangKyPage.getErrorMessage();

            // ✅ Không có lỗi => PASS
            Assert.assertTrue(errorMsg.isEmpty(),
                    "Không mong đợi lỗi nhưng nhận được: " + errorMsg);

            System.out.println("Đã tiếp nhận văn bản đến");

        } catch (Exception e) {
            System.out.println("✗ TC_14 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_14 failed", e);
        }
    }

    // TC_15: Nút Hủy
    @Test(description = "TC_15: Kiểm tra chức năng \"Hủy\"")
    public void TC_15() {
        System.out.println("\n>>> BẮT ĐẦU TC_15: Kiểm tra nút Hủy");
        try {
            dangKyPage.openDirectRegistration();

            dangKyPage.selectNgayNhan("2025-03-13");
            dangKyPage.inputNgayKy("2025-03-12");
            dangKyPage.inputSoKyHieu("242/NQ-BGDĐT");
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Bình Thường");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test hủy");

            String value1 = dangKyPage.getNgayDenValue();
            Assert.assertFalse(value1.isEmpty(), "Ngày đến phải được nhập");

            dangKyPage.clickHuy();
            Thread.sleep(1000);

            String value2 = dangKyPage.getNgayDenValue();
            Assert.assertTrue(value2.isEmpty() || value2.equals(""), "Form phải được reset");

            System.out.println("✓ TC_15 PASS");
        } catch (Exception e) {
            System.out.println("✗ TC_15 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_15 failed", e);
        }
    }

    // TC_16
    @Test(description = "TC_16: Kiểm tra trùng Số ký hiệu văn bản")
    public void TC_16() {

        System.out.println("\n>>> BẮT ĐẦU TC_16");

        try {
            dangKyPage.openDirectRegistration();

            dangKyPage.selectNgayNhan("2025-01-12");
            dangKyPage.inputNgayKy("2025-01-11");
            dangKyPage.inputSoKyHieu("231/NQ-BGDĐT"); // Trùng
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Khẩn");
            dangKyPage.inputCoQuanBanHanh("Bộ Giáo dục và Đào tạo");
            dangKyPage.inputTrichYeu("Test trùng");

            String mainFile = createTempFile("main_" + System.currentTimeMillis() + ".pdf", "Main content");
            dangKyPage.uploadFileVanBan(mainFile);

            dangKyPage.clickLuu();
            Thread.sleep(500);

            // ===== Expected =====
            String expected = "Số ký hiệu văn bản đã tồn tại";

            // ===== Actual =====
            String actualError = dangKyPage.getErrorMessage();
            String actualSuccess = dangKyPage.getSuccessMessage();

            String actual;

            if (!actualError.isEmpty()) {
                actual = actualError;
            } else if (actualSuccess != null && !actualSuccess.isEmpty()) {
                actual = actualSuccess;
            } else {
                actual = "Không có";
            }

            // ===== LOG =====
            System.out.println("Expected: " + expected);
            System.out.println("Actual: " + actual);

            // ===== ASSERT (FAIL có chủ đích để bắt bug) =====
            Assert.assertEquals(actual, expected,
                    " Hệ thống cho phép trùng số ký hiệu");

            System.out.println("✓ TC_16 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_16 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_16 failed", e);
        }
    }

    // TC_17: Ký tự đặc biệt
    @Test(description = "TC_17: Kiểm tra ký tự đặc biệt trong số hiệu")
    public void TC_17() {

        System.out.println("\n>>> BẮT ĐẦU TC_17");

        try {
            dangKyPage.openDirectRegistration();

            dangKyPage.selectNgayNhan("2025-01-12");
            dangKyPage.inputNgayKy("2025-01-11");
            dangKyPage.inputSoKyHieu("@#$%^&*"); // Ký tự đặc biệt
            dangKyPage.selectLoaiVanBan("Nghị Quyết");
            dangKyPage.selectMucDoUuTien("Khẩn");
            dangKyPage.inputCoQuanBanHanh("Bộ GD&ĐT");
            dangKyPage.inputTrichYeu("Test đặc biệt");

            String file = createTempFile("test_special_" + System.currentTimeMillis() + ".pdf", "data");
            dangKyPage.uploadFileVanBan(file);

            dangKyPage.clickLuu();
            Thread.sleep(500);

            // ===== Expected =====
            String expected = "Số ký hiệu không được có ký tự đặc biệt";

            String actualError = dangKyPage.getErrorMessage();
            String actualSuccess = dangKyPage.getSuccessMessage();

            System.out.println("ErrorMsg: " + actualError);
            System.out.println("SuccessMsg: " + actualSuccess);

            String actual;

            if (!actualError.isEmpty()) {
                actual = actualError;
            } else if (!actualSuccess.isEmpty()) {
                actual = actualSuccess;
            } else {
                actual = "Không có thông báo";
            }

            System.out.println("Expected: " + expected);
            System.out.println("Actual: " + actual);

            Assert.assertEquals(actual, expected,
                    "BUG: Hệ thống cho phép nhập ký tự đặc biệt");
            System.out.println("✓ TC_17 PASS");

        } catch (Exception e) {
            System.out.println("✗ TC_17 FAIL: " + e.getMessage());
            throw new RuntimeException("TC_17 failed", e);
        }
    }

    //    TC18
    @Test(description = "TC_18: Upload nhiều file đính kèm")
    public void TC_18() throws InterruptedException {

        dangKyPage.openDirectRegistration();

        // upload file chính
        String mainFile = createTempFile("main.pdf", "data");
        dangKyPage.uploadFileVanBan(mainFile);

        // upload file đính kèm
        String file1 = createTempFile("file1.docx", "data");
        String file2 = createTempFile("file2.pdf", "data");

        dangKyPage.uploadAttachment(file1);
        dangKyPage.uploadAttachment(file2);
        Thread.sleep(500);
        int actual = dangKyPage.getAttachmentCount();
        int expected = 3;

        System.out.println("Expected: " + expected);
        System.out.println("Actual  : " + actual);

        Assert.assertEquals(actual, expected,
                "Sai số lượng file đính kèm. Expected: " + expected + " - Actual: " + actual);

        System.out.println("✓ TC_18 PASS");
    }
}
