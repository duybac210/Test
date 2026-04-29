package pageobjects;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.interactions.Actions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.List;

public class ManHinhDangKyVanBanDi {
    private WebDriver driver;
    private WebDriverWait wait;

    // Locators
    private By ngayKyInput = By.id("id_ngay_ky");
    private By loaiVanBanSelect = By.id("id_ma_loai_vb");
    private By mucDoSelect = By.id("id_ma_muc_do");
    private By nguoiTaoSelect = By.id("id_nguoi_tao");
    private By nguoiKySelect = By.id("id_nguoi_ky");
    private By noiNhanInput = By.id("id_noi_nhan");
    private By soKyHieuInput = By.id("id_so_ky_hieu");
    private By btnCapSo = By.id("btn-cap-so");
    private By trichYeuInput = By.id("id_trich_yeu");
    private By banChinhThucInput = By.id("id_ban_chinh_thuc");
    private By tepDinhKemInput = By.id("id_tep_dinh_kem");
    private By btnLuu = By.xpath("//button[contains(text(), 'Lưu')]");
    private By btnHuy = By.cssSelector("button[type='reset']");

    // Readonly fields for verification
    private By displaySoVBDi = By.id("display_so_vb_di");
    private By displayTrangThai = By.id("display_trang_thai");
    private By displayLoaiVB = By.id("display_loai_vb");
    private By displayNgayBanHanh = By.id("display_ngay_ban_hanh");
    private By successMessage = By.cssSelector(".alert-success, .success-message, .alert.alert-primary");
    private By btnXemVBDi = By.id("xemvbd");

    public ManHinhDangKyVanBanDi(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    public void openDirectRegistration() {
        System.out.println("    [DEBUG] Đang mở trang đăng ký trực tiếp: http://127.0.0.1:8000/van-ban-di/dang-ky/");
        driver.get("http://127.0.0.1:8000/van-ban-di/dang-ky/");
        checkPageNotFound();
        try {
            // Đợi cho đến khi form thực sự hiển thị
            wait.until(ExpectedConditions.visibilityOfElementLocated(ngayKyInput));
            System.out.println("    [DEBUG] Trang đăng ký đã tải xong.");
        } catch (Exception e) {
            System.out.println("    [DEBUG] LỖI: Không tìm thấy form đăng ký!");
            System.out.println("    [DEBUG] URL hiện tại: " + driver.getCurrentUrl());
            System.out.println("    [DEBUG] Tiêu đề trang: " + driver.getTitle());
            throw e;
        }
    }

    public void checkPageNotFound() {
        String title = driver.getTitle();
        String bodyText = driver.findElement(By.tagName("body")).getText();
        if (title.contains("404") || bodyText.contains("Page not found") || bodyText.contains("404 Not Found")) {
            throw new RuntimeException("CRITICAL ERROR: Page Not Found (404) at " + driver.getCurrentUrl());
        }
    }

    public void inputNgayKy(String date) {
        int attempts = 0;
        while (attempts < 2) {
            try {
                WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(ngayKyInput));
                element.clear();
                ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1];",
                        element, date);
                ((org.openqa.selenium.JavascriptExecutor) driver)
                        .executeScript("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element);
                break;
            } catch (org.openqa.selenium.StaleElementReferenceException e) {
                System.out.println("    [DEBUG] Gặp lỗi StaleElement ở inputNgayKy, đang thử lại...");
                attempts++;
            }
        }
    }

    public void selectLoaiVanBan(String value) {
        // Đợi cho select element hiển thị
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(loaiVanBanSelect));
        Select select = new Select(element);

        // Đợi cho đến khi có ít nhất một option (ngoại trừ placeholder nếu có)
        wait.until(d -> select.getOptions().size() > 1);

        try {
            select.selectByValue(value);
        } catch (Exception e) {
            // Nếu không tìm thấy value cụ thể, thử chọn option đầu tiên sau placeholder
            if (!select.getOptions().isEmpty()) {
                System.out.println("Cảnh báo: Không tìm thấy loại văn bản '" + value + "', chọn option mặc định.");
                select.selectByIndex(1);
            } else {
                throw e;
            }
        }
    }

    public void selectEmptyLoaiVanBan() {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(loaiVanBanSelect));
        Select select = new Select(element);
        select.selectByIndex(0);
    }

    public void selectMucDo(String value) {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(mucDoSelect));
        Select select = new Select(element);
        try {
            select.selectByValue(value);
        } catch (Exception e) {
            if (select.getOptions().size() > 1)
                select.selectByIndex(1);
            else
                throw e;
        }
    }

    public void selectNguoiTao(String value) {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(nguoiTaoSelect));
        Select select = new Select(element);
        try {
            select.selectByValue(value);
        } catch (Exception e) {
            if (select.getOptions().size() > 1)
                select.selectByIndex(1);
            else
                throw e;
        }
    }

    public void selectEmptyNguoiTao() {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(nguoiTaoSelect));
        Select select = new Select(element);
        select.selectByIndex(0);
    }

    public void selectInvalidNguoiTao(String value) {
        WebElement element = driver.findElement(nguoiTaoSelect);
        ((org.openqa.selenium.JavascriptExecutor) driver).executeScript(
                "var opt = document.createElement('option'); opt.value = arguments[1]; opt.text = 'Invalid User'; arguments[0].appendChild(opt); arguments[0].value = arguments[1];",
                element, value);
    }

    public void selectNguoiKy(String value) {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(nguoiKySelect));
        Select select = new Select(element);
        try {
            select.selectByValue(value);
        } catch (Exception e) {
            if (select.getOptions().size() > 1)
                select.selectByIndex(1);
            else
                throw e;
        }
    }

    public void selectEmptyNguoiKy() {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(nguoiKySelect));
        Select select = new Select(element);
        select.selectByIndex(0);
    }

    public void inputNoiNhan(String text) {
        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(noiNhanInput));
        element.clear();
        ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1];", element,
                text);
        ((org.openqa.selenium.JavascriptExecutor) driver)
                .executeScript("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element);
    }

    public void inputSoKyHieu(String text) {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(soKyHieuInput));
        element.clear();
        element.sendKeys(text);
    }

    public void clickCapSo() {
        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(btnCapSo));
        element.click();
    }

    public void inputTrichYeu(String text) {
        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(trichYeuInput));
        element.clear();
        // Sử dụng Javascript để nhập liệu nhằm tránh lỗi BMP (Emoji) của ChromeDriver
        ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].value = arguments[1];", element,
                text);
        // Trigger sự kiện để hệ thống nhận diện thay đổi
        ((org.openqa.selenium.JavascriptExecutor) driver)
                .executeScript("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", element);
        ((org.openqa.selenium.JavascriptExecutor) driver)
                .executeScript("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", element);
    }

    public void uploadBanChinhThuc(String filePath) {
        WebElement element = driver.findElement(banChinhThucInput);
        element.sendKeys(filePath);
    }

    public void uploadTepDinhKem(String filePath) {
        WebElement element = driver.findElement(tepDinhKemInput);
        element.sendKeys(filePath);
    }

    public void clickLuu() {
        System.out.println("    [DEBUG] Đang thực hiện clickLuu...");
        try {
            WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(btnLuu));
            // Cuộn vào tầm nhìn
            ((org.openqa.selenium.JavascriptExecutor) driver)
                    .executeScript("arguments[0].scrollIntoView({block: 'center'});", element);
            Thread.sleep(500); // Đợi một chút để UI ổn định sau khi scroll

            System.out.println(
                    "    [DEBUG] Nút Lưu hiển thị: " + element.isDisplayed() + ", Kích hoạt: " + element.isEnabled());

            try {
                wait.until(ExpectedConditions.elementToBeClickable(btnLuu)).click();
                System.out.println("    [DEBUG] Click thành công bằng Selenium.");
            } catch (Exception e) {
                System.out.println("    [DEBUG] Click bằng Selenium thất bại, thử bằng Javascript: " + e.getMessage());
                ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("arguments[0].click();", element);
                System.out.println("    [DEBUG] Click thành công bằng Javascript.");
            }
        } catch (Exception e) {
            System.out.println("    [DEBUG] LỖI trong clickLuu: " + e.getMessage());
            throw new RuntimeException("Không thể nhấn nút Lưu: " + e.getMessage());
        }
    }

    public void doubleClickLuu() {
        System.out.println("    [DEBUG] Đang thực hiện doubleClickLuu...");
        try {
            WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(btnLuu));
            ((org.openqa.selenium.JavascriptExecutor) driver)
                    .executeScript("arguments[0].scrollIntoView({block: 'center'});", element);
            Thread.sleep(500);

            Actions actions = new Actions(driver);
            actions.doubleClick(element).perform();
            System.out.println("    [DEBUG] Double click thành công.");
        } catch (Exception e) {
            System.out.println("    [DEBUG] LỖI trong doubleClickLuu: " + e.getMessage());
            // Thử bằng JS nếu Actions fail (mặc dù JS double click hơi khác)
            WebElement element = driver.findElement(btnLuu);
            ((org.openqa.selenium.JavascriptExecutor) driver).executeScript(
                    "arguments[0].dispatchEvent(new MouseEvent('dblclick', { bubbles: true }));", element);
        }
    }

    public void waitForRegistrationSuccess() {
        // Đợi cho đến khi URL thay đổi từ /dang-ky/ sang /VBO.../dang-ky/
        wait.until(ExpectedConditions.urlMatches(".*van-ban-di/VBO\\d+/dang-ky/.*"));
    }

    public void waitForStatusChange(String oldStatus) {
        System.out.println("    [DEBUG] Đang đợi trạng thái thay đổi từ: " + oldStatus);
        wait.until(d -> {
            try {
                System.out.println("    [DEBUG] URL hiện tại: " + d.getCurrentUrl());
                // Tìm lại element mỗi lần để tránh stale hoặc lấy giá trị mới sau load trang
                WebElement statusEl = d.findElement(displayTrangThai);
                String current = statusEl.getAttribute("value");
                if (current != null)
                    current = current.trim();
                System.out.println("    [DEBUG] Trạng thái hiện tại: " + current);
                return current != null && !current.equalsIgnoreCase(oldStatus);
            } catch (Exception e) {
                System.out.println("    [DEBUG] Chờ đợi status change... (Element chưa sẵn sàng hoặc trang đang tải)");
                return false;
            }
        });
    }

    public void clickHuy() {
        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(btnHuy));
        element.click();
    }

    public String getSoKyHieu() {
        return driver.findElement(soKyHieuInput).getAttribute("value");
    }

    public String getTrangThai() {
        return driver.findElement(displayTrangThai).getAttribute("value");
    }

    public String getNgayBanHanh() {
        WebElement el = wait.until(ExpectedConditions.presenceOfElementLocated(displayNgayBanHanh));
        String val = el.getAttribute("value");
        if (val == null || val.isEmpty())
            val = el.getText();
        return val;
    }

    public String getValidationErrors() {
        StringBuilder sb = new StringBuilder();

        try {
            // Ép Selenium chờ tối đa 2 giây cho đến khi ít nhất 1 thông báo lỗi xuất hiện trong DOM
            new WebDriverWait(driver, Duration.ofSeconds(2))
                    .until(ExpectedConditions.presenceOfElementLocated(
                            By.cssSelector(".errorlist, .invalid-feedback, .form-errors, .alert-danger, .text-danger, .help-block")
                    ));
        } catch (Exception e) {
            // Nếu sau 2s không có lỗi DOM, kệ nó, chúng ta sẽ bắt tiếp bằng HTML5 Popup bên dưới
        }

        // 1. Tìm các thông báo lỗi trong DOM (Django/Bootstrap)
        List<WebElement> errors = driver.findElements(By.cssSelector(".errorlist, .invalid-feedback, .form-errors, .alert-danger, .text-danger, .help-block"));
        for (WebElement error : errors) {
            String text = error.getText().trim();
            if (!text.isEmpty()) sb.append(text).append("; ");
        }

        // 2. Nếu không thấy, thử lấy validation message của HTML5 (Browser popup)
        if (sb.length() == 0) {
            String h5Error = (String) ((org.openqa.selenium.JavascriptExecutor) driver).executeScript(
                    "var invalid = document.querySelector(':invalid'); return invalid ? invalid.validationMessage : '';"
            );
            if (h5Error != null && !h5Error.isEmpty()) sb.append(h5Error).append("; ");
        }

        return sb.toString();
    }

    public boolean isFieldReadOnly(By locator) {
        WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(locator));
        String readonly = element.getAttribute("readonly");
        String disabled = element.getAttribute("disabled");
        String tag = element.getTagName();

        System.out.println("    [DEBUG] Kiểm tra Read-only cho " + locator + ": tag=" + tag + ", readonly=" + readonly
                + ", disabled=" + disabled);

        // Trong Selenium, getAttribute trả về "true" cho các thuộc tính boolean nếu
        // chúng tồn tại
        boolean isRO = (readonly != null && (readonly.equalsIgnoreCase("true") || readonly.equals("")))
                || (disabled != null && (disabled.equalsIgnoreCase("true") || disabled.equals("")));

        // Thêm kiểm tra class nếu hệ thống dùng CSS để giả lập readonly
        if (!isRO) {
            String classes = element.getAttribute("class");
            if (classes != null && (classes.contains("readonly") || classes.contains("disabled"))) {
                isRO = true;
            }
        }

        return isRO;
    }

    public String getSoVBDi() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(displaySoVBDi)).getAttribute("value");
    }

    public String getSuccessMessage() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(successMessage)).getText().trim();
        } catch (Exception e) {
            // Fallback: tìm bất kỳ element nào chứa text "dang ky"
            try {
                return driver.findElement(By.xpath("//*[contains(text(), 'dang ky') or contains(text(), 'đăng ký')]"))
                        .getText().trim();
            } catch (Exception e2) {
                return "Không tìm thấy thông báo thành công trên trang.";
            }
        }
    }

    public void clickXemVBDi() {
        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(btnXemVBDi));
        element.click();
    }

    public boolean isLoaiVBReadOnly() {
        return driver.findElements(displayLoaiVB).size() > 0;
    }

    public boolean isSoVBDiReadOnly() {
        WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(displaySoVBDi));
        String readonly = element.getAttribute("readonly");
        String disabled = element.getAttribute("disabled");
        return (readonly != null) || (disabled != null);
    }

    /** Lấy Số văn bản đi lớn nhất hiện tại từ danh sách. */
    public String getLatestSoVBDiFromList() {
        driver.get("http://127.0.0.1:8000/van-ban-di/");
        try {
            // Đợi bảng load
            wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("table tbody tr")));
            // Lấy ID ở dòng đầu tiên (giả định sắp xếp mới nhất lên đầu)
            WebElement firstRowId = driver.findElement(By.xpath("//table/tbody/tr[1]/td[1]"));
            return firstRowId.getText().trim();
        } catch (Exception e) {
            System.out.println("    [DEBUG] Không tìm thấy bản ghi nào trong danh sách.");
            return "VBO00000000";
        }
    }
}
