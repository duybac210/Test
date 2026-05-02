package pageobjects.bn;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.Select;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class ChiTietVBDi {
    private WebDriver driver;
    private WebDriverWait wait;

    public ChiTietVBDi(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    public boolean kiemTraTrangChiTietHienThi() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//div[@class='modal-header']//span[contains(text(), 'CHI TIẾT')]"))).isDisplayed();
    }

    public void clickChinhSua() {
        WebElement btn = wait.until(ExpectedConditions.elementToBeClickable(By.id("btn-edit")));
        btn.click();
        wait.until(d -> driver.findElement(By.id("m-trich-yeu")).getAttribute("readonly") == null);
    }

    public void suaThongTin(String loaiVanBan, String noiNhan) {
        // TIÊU CHUẨN DEV: Xử lý Dropdown bằng vòng lặp trim() và equalsIgnoreCase()
        WebElement selectEl = wait.until(ExpectedConditions.elementToBeClickable(By.id("m-loai-vb")));
        Select select = new Select(selectEl);
        
        boolean isSelected = false;
        for (WebElement opt : select.getOptions()) {
            if (opt.getText().trim().equalsIgnoreCase(loaiVanBan.trim())) {
                opt.click();
                isSelected = true;
                break;
            }
        }
        
        if (!isSelected) {
            throw new RuntimeException("Automation Error: Không tìm thấy loại văn bản nào khớp với: " + loaiVanBan);
        }
        
        WebElement inputNoiNhan = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("m-noi-nhan")));
        inputNoiNhan.clear();
        inputNoiNhan.sendKeys(noiNhan);
    }

    public void clickLuu() {
        wait.until(ExpectedConditions.elementToBeClickable(By.id("btn-save"))).click();
    }

    public void clickHuy() {
        wait.until(ExpectedConditions.elementToBeClickable(By.id("btn-cancel"))).click();
    }

    public boolean kiemTraThongBaoLuuThanhCong() {
        return kiemTraThongBaoHienThi("thành công");
    }

    public boolean kiemTraTruongBiKhoa(String tenTruong) {
        String id = "";
        if (tenTruong.toLowerCase().contains("số văn bản")) id = "m-so-di";
        else if (tenTruong.toLowerCase().contains("trạng thái")) id = "m-trang-thai";
        else if (tenTruong.toLowerCase().contains("trích yếu")) id = "m-trich-yeu";
        
        WebElement element = wait.until(ExpectedConditions.presenceOfElementLocated(By.id(id)));
        String disabled = element.getAttribute("disabled");
        String readonly = element.getAttribute("readonly");
        return (disabled != null && disabled.equals("true")) || (readonly != null && readonly.equals("true"));
    }

    public void xoaTrichYeu() {
        WebElement el = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("m-trich-yeu")));
        el.clear();
    }

    public void suaNgayBanHanh(String ngay) {
        WebElement el = wait.until(ExpectedConditions.presenceOfElementLocated(By.id("m-ngay-ban-hanh")));
        ((JavascriptExecutor)driver).executeScript("arguments[0].value = arguments[1];", el, ngay);
    }
    
    public void suaTrichYeu(String text) {
        WebElement el = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("m-trich-yeu")));
        el.clear();
        el.sendKeys(text);
    }

    public boolean kiemTraThongBaoHienThi(String text) {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//*[contains(text(), '" + text + "')]"))).isDisplayed();
    }
    
    public void clickNutX() {
        wait.until(ExpectedConditions.elementToBeClickable(By.id("close-modal-btn"))).click();
        wait.until(ExpectedConditions.invisibilityOfElementLocated(By.id("document-modal")));
    }
    
    public boolean clickDownloadFile() {
        WebElement link = wait.until(ExpectedConditions.presenceOfElementLocated(By.id("m-ban-du-thao-link")));
        ((JavascriptExecutor) driver).executeScript("arguments[0].click();", link);
        return true;
    }
    
    public void clickPhatHanh() {
        wait.until(ExpectedConditions.elementToBeClickable(By.id("btn-external-publish"))).click();
    }
    
    public void clickNutPhatHanhMauXanh() {
        clickPhatHanh();
    }
    
    public String getTrichYeu() {
        return wait.until(ExpectedConditions.presenceOfElementLocated(By.id("m-trich-yeu"))).getAttribute("value");
    }
    
    public String getTrangThai() {
        WebElement select = wait.until(ExpectedConditions.presenceOfElementLocated(By.id("m-trang-thai")));
        return new Select(select).getFirstSelectedOption().getText().trim();
    }
    
    public void chonNoiNhanTuDropdown(String noiNhan) {
        WebElement el = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("m-noi-nhan")));
        el.clear();
        el.sendKeys(noiNhan);
    }
}
