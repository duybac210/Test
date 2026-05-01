package pageobjects.viet;

import common.viet.Constant;
import org.openqa.selenium.By;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;

public class LoginPage {
    private final By usernameTextbox = By.id("username");
    private final By passwordTextbox = By.id("password");
    private final By loginButton = By.cssSelector(".login-btn");

    public void login(String username, String password) {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.visibilityOfElementLocated(usernameTextbox)).sendKeys(username);
        Constant.WEBDRIVER.findElement(passwordTextbox).sendKeys(password);
        Constant.WEBDRIVER.findElement(loginButton).click();
    }
}
