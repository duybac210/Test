package common.bn;

import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import pageobjects.bn.LoginPage;
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
            
            // Tự động tìm chromedriver (Selenium 4.6+)
            driver = new ChromeDriver(options);
            driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(10));
            Constant.WEBDRIVER = driver;
        }
        return driver;
    }
    
    public static void autoLogin() {
        if (!isLoggedIn) {
            loginAs(Constant.USERNAME, Constant.PASSWORD);
        }
    }
    
    public static void loginAs(String username, String password) {
        WebDriver webDriver = getDriver();
        webDriver.get(Constant.RAILWAY_URL);
        LoginPage loginPage = new LoginPage(webDriver);
        loginPage.login(username, password);
        
        // Đợi đăng nhập thành công
        new WebDriverWait(webDriver, Duration.ofSeconds(15))
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

    // Hàm click an toàn sử dụng Javascript nếu click thông thường bị lỗi
    public static void safeClick(WebElement element) {
        try {
            element.click();
        } catch (Exception e) {
            ((JavascriptExecutor) driver).executeScript("arguments[0].click();", element);
        }
    }
}
