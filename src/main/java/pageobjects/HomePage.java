package pageobjects;

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

    public void clickTaoVanBanLink() {
        WebElement link = wait.until(ExpectedConditions.elementToBeClickable(
            By.cssSelector("a[href='/tao-van-ban/']")));
        link.click();
    }

    public void clickDuyetVanBanLink() {
        // Thử click link menu trước; nếu không có (user không có quyền) thì navigate thẳng
        try {
            WebElement link = wait.until(ExpectedConditions.elementToBeClickable(
                By.cssSelector("a[href='/quan-ly-cong-viec/duyet-van-ban/']")));
            link.click();
        } catch (Exception e) {
            driver.get("http://127.0.0.1:8000/quan-ly-cong-viec/duyet-van-ban/");
        }
    }

    public void navigateToDuyetVanBan() {
        driver.get("http://127.0.0.1:8000/quan-ly-cong-viec/duyet-van-ban/");
    }

    public void navigateToTaoVanBan() {
        driver.get("http://127.0.0.1:8000/tao-van-ban/");
    }
}
