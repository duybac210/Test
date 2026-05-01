package pageobjects;

import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.List;

/**
 * Page Object cho chức năng ĐĂNG KÝ VĂN BẢN ĐẾN
 * 
 * Quản lý tất cả các tương tác với form đăng ký văn bản đến
 */
public class ManHinhDangKyVanBanDen {
    private WebDriver driver;
    private WebDriverWait wait;

    // Locators cho các field INPUT của form Văn bản Đến
    private By ngayNhanselect = By.id("id_ngay_nhan");
    private By ngayKyInput = By.id("id_ngay_ky");
    private By soKyHieuInput = By.id("id_so_ky_hieu");
    private By loaiVanBanSelect = By.id("id_ma_loai_vb");
    private By mucDoUuTienSelect = By.id("id_ma_muc_do");
    private By coQuanBanHanhInput = By.id("id_co_quan_ban_hanh");
    private By trichYeuInput = By.id("id_trich_yeu");
    private By fileVanBanInput = By.id("id_file_van_ban");
    private By fileDinhKemInput = By.id("id_tep_dinh_kem");

    // Locators cho các button
    private By btnLuu = By.xpath("//button[contains(text(), 'Lưu')]");
    private By btnHuy = By.xpath("//button[contains(text(), 'Hủy') or @type='reset']");

    // Readonly fields for verification
    private By displaySoVBDen = By.id("auto_so_vb_den");
    private By displayTrangThai = By.id("auto_trang_thai");

    // Thông báo
    private By successMessage = By.cssSelector(".alert-success, .message-success, .alert.alert-primary, .toast-success");
    private By errorMessage = By.cssSelector(".alert-danger, .alert-error, .error-message, .invalid-feedback, .help-block");

    public ManHinhDangKyVanBanDen(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    /**
     * Mở trang đăng ký văn bản đến trực tiếp
     */
    public void openDirectRegistration() {
        System.out.println("    [DEBUG] Đang mở trang đăng ký văn bản đến: http://127.0.0.1:8000/van-ban-den/dang-ky/");
        driver.get("http://127.0.0.1:8000/van-ban-den/dang-ky/");
        checkPageNotFound();
        try {
            // Đợi form tải xong
            wait.until(ExpectedConditions.visibilityOfElementLocated(ngayNhanselect));
            System.out.println("    [DEBUG] Trang đăng ký văn bản đến đã tải xong.");
        } catch (Exception e) {
            System.out.println("    [DEBUG] LỖI: Không tìm thấy form đăng ký!");
            System.out.println("    [DEBUG] URL hiện tại: " + driver.getCurrentUrl());
            System.out.println("    [DEBUG] Tiêu đề trang: " + driver.getTitle());
            throw e;
        }
    }

    /**
     * Kiểm tra xem trang có bị 404 không
     */
    public void checkPageNotFound() {
        String title = driver.getTitle();
        String bodyText = driver.findElement(By.tagName("body")).getText();
        if (title.contains("404") || bodyText.contains("Page not found") || bodyText.contains("404 Not Found")) {
            throw new RuntimeException("CRITICAL ERROR: Page Not Found (404) at " + driver.getCurrentUrl());
        }
    }

    // ==========================================
    // INPUT METHODS - Nhập dữ liệu vào form
    // ==========================================

    /**
     * Nhập Ngày nhận
     */
    public void selectNgayNhan(String date) {
        try {
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(ngayNhanselect));
            element.clear();
            // Dùng JS để set value vì date input có thể phức tạp
            ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1];",
                    element, date);
            ((org.openqa.selenium.JavascriptExecutor) driver)
                    .executeScript("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element);
            System.out.println("    [DEBUG] Đã nhập Ngày nhận: " + date);
        } catch (Exception e) {
            System.out.println("    [DEBUG] Lỗi khi nhập Ngày nhận: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Nhập Ngày ký
     */
    public void inputNgayKy(String date) {
        try {
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(ngayKyInput));
            element.clear();
            ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1];",
                    element, date);
            ((org.openqa.selenium.JavascriptExecutor) driver)
                    .executeScript("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element);
            System.out.println("    [DEBUG] Đã nhập Ngày ký: " + date);
        } catch (Exception e) {
            System.out.println("    [DEBUG] Lỗi khi nhập Ngày ký: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Nhập Số ký hiệu văn bản
     */
    public void inputSoKyHieu(String soKyHieu) {
        try {
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(soKyHieuInput));
            element.clear();
            element.sendKeys(soKyHieu);
            System.out.println("    [DEBUG] Đã nhập Số ký hiệu: " + soKyHieu);
        } catch (Exception e) {
            System.out.println("    [DEBUG] Lỗi khi nhập Số ký hiệu: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Chọn Loại văn bản
     */
//    public void selectLoaiVanBan(String value) {
//        try {
//            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(loaiVanBanSelect));
//            Select select = new Select(element);
//
//            // Đợi cho đến khi có ít nhất một option
//            wait.until(d -> select.getOptions().size() > 0);
//
//            select.selectByValue(value);
//            System.out.println("    [DEBUG] Đã chọn Loại văn bản: " + value);
//        } catch (Exception e) {
//            System.out.println("    [DEBUG] Lỗi khi chọn Loại văn bản: " + e.getMessage());
//            throw e;
//        }
//    }
    public void selectLoaiVanBan(String loai) {
        WebElement dropdown = driver.findElement(By.id("id_ma_loai_vb"));
        Select select = new Select(dropdown);
        select.selectByVisibleText(loai);
    }

    /**
     * Chọn Mức độ ưu tiên
     */
    public void selectMucDoUuTien(String mucDo) {
        WebElement dropdown = driver.findElement(By.id("id_ma_muc_do"));
        Select select = new Select(dropdown);
        select.selectByVisibleText(mucDo);
    }

    /**
     * Nhập Cơ quan ban hành
     */
    public void inputCoQuanBanHanh(String coQuan) {
        try {
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(coQuanBanHanhInput));
            element.clear();
            element.sendKeys(coQuan);
            System.out.println("    [DEBUG] Đã nhập Cơ quan ban hành: " + coQuan);
        } catch (Exception e) {
            System.out.println("    [DEBUG] Lỗi khi nhập Cơ quan ban hành: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Nhập Trích yếu
     */
    public void inputTrichYeu(String trichYeu) {
        try {
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(trichYeuInput));
            element.clear();
            // Sử dụng JS để nhập (tránh vấn đề với các ký tự đặc biệt)
            ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1];",
                    element, trichYeu);
            // Trigger events
            ((org.openqa.selenium.JavascriptExecutor) driver)
                    .executeScript("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element);
            ((org.openqa.selenium.JavascriptExecutor) driver)
                    .executeScript("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element);
            System.out.println("    [DEBUG] Đã nhập Trích yếu: " + trichYeu);
        } catch (Exception e) {
            System.out.println("    [DEBUG] Lỗi khi nhập Trích yếu: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Tải file văn bản
     */
    public void uploadFileVanBan(String filePath) {
        try {
            WebElement element = driver.findElement(fileVanBanInput);
            element.sendKeys(filePath);
            System.out.println("    [DEBUG] Đã tải file văn bản: " + filePath);
        } catch (Exception e) {
            System.out.println("    [DEBUG] Lỗi khi tải file văn bản: " + e.getMessage());
            throw e;
        }
    }

    /**
     * Tải file đính kèm
     */
    public void uploadFileDinhKem(String filePath) {
        try {
            WebElement element = driver.findElement(fileDinhKemInput);
            element.sendKeys(filePath);
            System.out.println("    [DEBUG] Đã tải file đính kèm: " + filePath);
        } catch (Exception e) {
            System.out.println("    [DEBUG] Lỗi khi tải file đính kèm: " + e.getMessage());
            throw e;
        }
    }

    // ==========================================
    // CLICK METHODS - Click các button
    // ==========================================

    /**
     * Click nút Lưu
     */
    public void clickLuu() {
        System.out.println("    [DEBUG] Đang click nút Lưu...");
        try {
            WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(btnLuu));

            // Scroll tới nút
            ((org.openqa.selenium.JavascriptExecutor) driver)
                    .executeScript("arguments[0].scrollIntoView({block: 'center'});", element);
            Thread.sleep(500);

            System.out.println("    [DEBUG] Nút Lưu hiển thị: " + element.isDisplayed() + ", Kích hoạt: " + element.isEnabled());

            try {
                wait.until(ExpectedConditions.elementToBeClickable(btnLuu)).click();
                System.out.println("    [DEBUG] Click Lưu thành công (Selenium)");
            } catch (Exception e) {
                System.out.println("    [DEBUG] Thử click bằng JavaScript...");
                ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].click();", element);
                System.out.println("    [DEBUG] Click Lưu thành công (JavaScript)");
            }
        } catch (Exception e) {
            System.out.println("    [DEBUG] LỖI khi click Lưu: " + e.getMessage());
            throw new RuntimeException("Không thể click nút Lưu: " + e.getMessage());
        }
    }

    /**
     * Click nút Hủy
     */
    public void clickHuy() {
        System.out.println("    [DEBUG] Đang click nút Hủy...");
        try {
            WebElement element = wait.until(ExpectedConditions.elementToBeClickable(btnHuy));
            element.click();
            System.out.println("    [DEBUG] Click Hủy thành công");
        } catch (Exception e) {
            System.out.println("    [DEBUG] LỖI khi click Hủy: " + e.getMessage());
            throw new RuntimeException("Không thể click nút Hủy: " + e.getMessage());
        }
    }

    // ==========================================
    // VERIFICATION METHODS - Kiểm tra
    // ==========================================

    /**
     * Lấy thông báo thành công
     */
    public String getSuccessMessage() {
        try {
            WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(5));

            WebElement msg = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    By.cssSelector(".page-message.success")
            ));

            return msg.getText().trim();

        } catch (Exception e) {
            return "";
        }
    }

    /**
     * Lấy thông báo lỗi
     */
    public String getErrorMessage() {
        try {
            List<WebElement> elements = driver.findElements(errorMessage);
            StringBuilder allErrors = new StringBuilder();

            for (WebElement elem : elements) {
                String text = elem.getText().trim();
                if (!text.isEmpty()) {
                    allErrors.append(text).append("; ");
                }
            }

            String result = allErrors.toString();
            System.out.println("    [DEBUG] Thông báo lỗi: " + result);
            return result;
        } catch (Exception e) {
            System.out.println("    [DEBUG] Không tìm thấy thông báo lỗi");
            return "";
        }
    }

    /**
     * Kiểm tra có lỗi validation không
     */
    public boolean hasValidationError(String fieldId) {
        try {
            WebElement field = driver.findElement(By.id(fieldId));

            String message = field.getAttribute("validationMessage");

            System.out.println("Validation message: " + message);

            return message != null && !message.trim().isEmpty();

        } catch (Exception e) {
            return false;
        }
    }


    /**
     * Lấy giá trị của trường Ngày đến
     */
    public String getNgayDenValue() {
        try {
            WebElement element = driver.findElement(ngayNhanselect);
            return element.getAttribute("value");
        } catch (Exception e) {
            return "";
        }
    }

    /**
     * Lấy giá trị của trường Số ký hiệu
     */
    public String getSoKyHieuValue() {
        try {
            WebElement element = driver.findElement(soKyHieuInput);
            return element.getAttribute("value");
        } catch (Exception e) {
            return "";
        }
    }

    /**
     * Lấy số VB đến được tạo (từ field readonly)
     */
    public String getSoVBDen() {
        try {
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(displaySoVBDen));
            return element.getAttribute("value").trim();
        } catch (Exception e) {
            System.out.println("    [DEBUG] Không tìm thấy Số VB đến");
            return "";
        }
    }

    /**
     * Lấy trạng thái văn bản
     */
    public String getTrangThai() {
        try {
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(displayTrangThai));
            return element.getAttribute("value").trim();
        } catch (Exception e) {
            System.out.println("    [DEBUG] Không tìm thấy Trạng thái");
            return "";
        }
    }

    /**
     * Chờ đến khi form reset (Hủy thành công)
     */
    public void waitForFormReset() throws InterruptedException {
        System.out.println("    [DEBUG] Đang chờ form reset...");
        Thread.sleep(1000);
        String value = driver.findElement(trichYeuInput).getAttribute("value");
        if (!value.isEmpty()) {
            throw new RuntimeException("Form chưa được reset, Trích yếu vẫn còn: " + value);
        }
        System.out.println("    [DEBUG] Form đã được reset");
    }

    /**
     * Kiểm tra xem field có readonly không
     */
    public boolean isFieldReadOnly(String fieldId) {
        try {
            WebElement element = driver.findElement(By.id(fieldId));
            String readonly = element.getAttribute("readonly");
            String disabled = element.getAttribute("disabled");
            return (readonly != null) || (disabled != null);
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Chờ cho đến khi đơn đăng ký thành công
     */
    public void waitForRegistrationSuccess() {
        System.out.println("    [DEBUG] Chờ đăng ký thành công...");
        wait.until(ExpectedConditions.visibilityOfElementLocated(successMessage));
        System.out.println("    [DEBUG] Đăng ký thành công!");
    }

    public By getNgayNhanselect() {
        return ngayNhanselect;
    }

    public void setNgayNhanselect(By ngayNhanselect) {
        this.ngayNhanselect = ngayNhanselect;
    }
    public String getFileVanBanError() {
        try {
            WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(5));

            WebElement error = wait.until(
                    ExpectedConditions.visibilityOfElementLocated(
                            By.cssSelector("ul.errorlist.nonfield li")
                    )
            );

            return error.getText().trim();

        } catch (TimeoutException e) {
            return null;
        }
    }

    public int getAttachmentCount() {
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        List<WebElement> files = wait.until(
                ExpectedConditions.numberOfElementsToBeMoreThan(
                        By.cssSelector("#attachment-list .attachment-item"), 0
                )
        );

        return files.size();
    }
    public void uploadAttachment(String filePath) {
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        WebElement fileInput = wait.until(ExpectedConditions.presenceOfElementLocated(
                By.id("id_tep_dinh_kem")
        ));

        // Bỏ hidden (sr-only)
        JavascriptExecutor js = (JavascriptExecutor) driver;
        js.executeScript("arguments[0].style.display='block';", fileInput);

        // Upload trực tiếp → KHÔNG mở File Explorer
        fileInput.sendKeys(filePath);

        System.out.println("[DEBUG] Upload attachment: " + filePath);
    }
}




