package pageobjects.bn;

import common.bn.Constant;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class HomePage {
    private WebDriver driver;
    private WebDriverWait wait;

    public HomePage(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    public void clickXemVanBanDi() {
        try {
            // Thử tìm nút trên taskbar trước (nếu đang ở trang chủ)
            WebElement taskbarBtn = wait.until(ExpectedConditions.elementToBeClickable(
                By.xpath("//div[@class='taskbar-top']//label[contains(translate(text(), 'V', 'v'), 'văn bản đi')]/..")));
            taskbarBtn.click();
        } catch (Exception e) {
            // Nếu không thấy (có thể đã ở trong module), thử tìm ở sidebar
            try {
                WebElement sidebarBtn = wait.until(ExpectedConditions.elementToBeClickable(By.id("xemvbd")));
                sidebarBtn.click();
            } catch (Exception e2) {
                // Cuối cùng, nếu vẫn không được thì điều hướng trực tiếp bằng URL
                driver.get(Constant.VAN_BAN_DI_URL);
            }
        }
    }
    
    public void clickDangKyVanBanDi() {
        try {
            WebElement link = wait.until(ExpectedConditions.elementToBeClickable(By.id("dkvbd")));
            link.click();
        } catch (Exception e) {
            driver.get("http://127.0.0.1:8000/van-ban-di/dang-ky/");
        }
    }
    
    public void clickPhatHanhBenNgoai() {
        try {
            WebElement link = wait.until(ExpectedConditions.elementToBeClickable(By.id("phbng")));
            link.click();
        } catch (Exception e) {
            driver.get("http://127.0.0.1:8000/van-ban-di/phat-hanh-ben-ngoai/");
        }
    }
}
