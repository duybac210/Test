package pageobjects.oanh;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

public class TimVBDi {
    private WebDriver driver;
    private WebDriverWait wait;

    // Locators (Bạn hãy kiểm tra lại ID/XPath thực tế trên web của bạn)
    private By txtTimKiem = By.id("search-input");
    private By btnXem = By.id("search-button");
    private By lblThongBaoTrong = By.xpath("//td[contains(text(),'Không tìm thấy văn bản hợp lệ')]");

    public TimVBDi(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    public void timKiemVanBan(String tuKhoa) {
        WebElement input = wait.until(ExpectedConditions.visibilityOfElementLocated(txtTimKiem));
        input.clear();
        input.sendKeys(tuKhoa);
        driver.findElement(btnXem).click();
    }

    public String getThongBaoTrongText() {
        try {
            return wait.until(ExpectedConditions.visibilityOfElementLocated(lblThongBaoTrong)).getText();
        } catch (Exception e) {
            return "";
        }
    }


    public boolean kiemTraKetQuaHienThiSoKyHieu(String soKyHieu) {
        try {
            // Chờ cho đến khi xuất hiện ô chứa số ký hiệu mong muốn (điều này cũng tự động giúp xử lý thời gian chờ AJAX)
            String xpath = "//td[contains(text(),'" + soKyHieu + "')]";
            WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(5));
            return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(xpath))).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }

    public void timKiemTheoNgayBanHanh(String ngayBanHanh) {
        WebElement input = driver.findElement(txtTimKiem);
        input.clear();
        input.sendKeys(ngayBanHanh);
        driver.findElement(btnXem).click();

    }

    public boolean kiemTraKetQuaHienThiNgayBanHanh(String ngayBanHanh) {
        try {
            
            java.util.List<WebElement> cells = driver.findElements(By.cssSelector(".table-custom tbody tr td:nth-child(2)"));
            if (cells.isEmpty()) return false;
            
            // Duyệt qua TẤT CẢ các dòng để đảm bảo KHÔNG có dòng nào sai
            for (WebElement cell : cells) {
                if (!cell.getText().contains(ngayBanHanh)) {
                    System.out.println("Lỗi: Dòng kết quả có ngày ban hành sai: " + cell.getText());
                    return false;
                }
            }
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
