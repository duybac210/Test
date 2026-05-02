package pageobjects.oanh;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;

public class HomePage {
    private WebDriver driver;
    
    public HomePage(WebDriver driver) {
        this.driver = driver;
    }
    
    public void clickXemVanBanDi() {
        WebElement xemVanBanDilink = driver.findElement(By.cssSelector(".taskbar-top a[href='/van-ban-di/']"));
        xemVanBanDilink.click();
    }
}
