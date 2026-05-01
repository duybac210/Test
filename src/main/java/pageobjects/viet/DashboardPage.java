package pageobjects.viet;

import common.viet.Constant;
import org.openqa.selenium.By;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

public class DashboardPage {
    private final By vanBanDenTaskbarButton = By.cssSelector(".taskbar-top a[href='/van-ban-den/']");

    public void clickVanBanDenTaskbarButton() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.elementToBeClickable(vanBanDenTaskbarButton)).click();
    }
}
