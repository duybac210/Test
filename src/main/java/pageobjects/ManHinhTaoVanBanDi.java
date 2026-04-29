package pageobjects;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

public class ManHinhTaoVanBanDi {
    private WebDriver driver;
    private WebDriverWait wait;

    // Các locator bền vững sử dụng ID thực tế từ forms.py
    private By loaiVanBanSelect = By.id("loai-van-ban");
    private By mucDoSelect = By.id("muc-do-uu-tien");
    private By noiNhanInput = By.id("noi-nhan");
    private By trichYeuInput = By.id("trich-yeu");
    private By fileDuThaoInput = By.id("id_ban_du_thao"); 
    private By trinhDuyetBtn = By.id("submit-preview-btn");
    private By huyBtn = By.id("reset-form-btn");
    
    // Locator cho thông báo lỗi validation nếu để trống (tùy thuộc vào HTML thực tế, đây là class mặc định của Django Form)
    private By validationError = By.cssSelector(".errorlist, .page-feedback"); 

    public ManHinhTaoVanBanDi(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    // Mở trang tạo văn bản đi
    public void openPage() {
        driver.get("http://127.0.0.1:8000/tao-van-ban/");
    }

    // Explicit Wait + Select cho dropdown
    public void selectLoaiVanBan(String value) {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(loaiVanBanSelect));
        new Select(element).selectByValue(value);
    }
    
    public void selectMucDo(String value) {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(mucDoSelect));
        new Select(element).selectByValue(value);
    }

    // Explicit Wait + Nhập text
    public void inputNoiNhan(String noiNhan) {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(noiNhanInput));
        element.clear();
        element.sendKeys(noiNhan);
    }

    public void inputTrichYeu(String trichYeu) {
        WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(trichYeuInput));
        element.clear();
        element.sendKeys(trichYeu);
    }

    // Upload file
    public void uploadFileDuThao(String absoluteFilePath) {
        // Đối với thẻ <input type="file"> bị ẩn, ta không dùng click() mà truyền thẳng path
        WebElement element = driver.findElement(fileDuThaoInput);
        element.sendKeys(absoluteFilePath);
    }

    // Explicit Wait + Click
    public void submitForm() {
        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(trinhDuyetBtn));
        element.click();
    }

    public void clickHuy() {
        WebElement element = wait.until(ExpectedConditions.elementToBeClickable(huyBtn));
        element.click();
    }

    public String getNoiNhanValue() {
        return driver.findElement(noiNhanInput).getAttribute("value");
    }

    public String getTrichYeuValue() {
        return driver.findElement(trichYeuInput).getAttribute("value");
    }
    
    // Lấy nội dung lỗi validation
    public String getValidationErrorMessage() {
        try {
            WebElement element = wait.until(ExpectedConditions.visibilityOfElementLocated(validationError));
            return element.getText();
        } catch (Exception e) {
            return "";
        }
    }
}
