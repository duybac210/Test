package common;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import pageobjects.LoginPage;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class Utilities {
    private static WebDriver driver;
    private static boolean isLoggedIn = false;
    
    public static WebDriver getDriver() {
        if (driver == null) {
            ChromeOptions options = new ChromeOptions();
            options.addArguments("--start-maximized");
            options.addArguments("--disable-notifications");
            
            driver = new ChromeDriver(options);
            driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
        }
        return driver;
    }
    
    public static void autoLogin() {
        if (!isLoggedIn) {
            loginAs("GV000006", "giaovien123");
        }
    }
    
    public static void loginAs(String username, String password) {
        WebDriver webDriver = getDriver();
        webDriver.get("http://127.0.0.1:8000/dang-nhap/");
        LoginPage loginPage = new LoginPage(webDriver);
        loginPage.login(username, password);
        
        // Đợi đăng nhập thành công (URL không còn chứa /dang-nhap/)
        new WebDriverWait(webDriver, Duration.ofSeconds(10))
            .until(ExpectedConditions.not(ExpectedConditions.urlContains("/dang-nhap/")));
            
        isLoggedIn = true;
    }
    
    public static void logout() {
        if (driver != null && isLoggedIn) {
            driver.get("http://127.0.0.1:8000/dang-xuat/");
            isLoggedIn = false;
        }
    }
    
    public static void quitDriver() {
        if (driver != null) {
            driver.quit();
            driver = null;
            isLoggedIn = false;
        }
    }
}
