package common;

import org.openqa.selenium.By;
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
        if (driver != null) {
            try {
                // Kiểm tra xem trình duyệt còn sống không bằng cách lấy URL hoặc WindowHandle
                driver.getCurrentUrl();
            } catch (Exception e) {
                System.out.println("Trình duyệt đã bị đóng bất thường, đang khởi tạo lại...");
                driver = null;
                isLoggedIn = false;
            }
        }

        if (driver == null) {
            ChromeOptions options = new ChromeOptions();
            options.addArguments("--start-maximized");
            options.addArguments("--disable-notifications");
            // Thêm các options giúp driver ổn định hơn
            options.addArguments("--disable-dev-shm-usage");
            options.addArguments("--no-sandbox");
            
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
        System.out.println("Đang đăng nhập với user: " + username);
        
        webDriver.get("http://127.0.0.1:8000/dang-nhap/");
        
        // Đợi form login hiển thị để tránh lỗi trang chưa load kịp
        new WebDriverWait(webDriver, Duration.ofSeconds(10))
            .until(ExpectedConditions.presenceOfElementLocated(By.id("username")));
            
        LoginPage loginPage = new LoginPage(webDriver);
        loginPage.login(username, password);
        
        // Đợi đăng nhập thành công (URL không còn chứa /dang-nhap/)
        try {
            new WebDriverWait(webDriver, Duration.ofSeconds(10))
                .until(ExpectedConditions.not(ExpectedConditions.urlContains("/dang-nhap/")));
            isLoggedIn = true;
            System.out.println("Đăng nhập thành công.");
        } catch (Exception e) {
            System.out.println("Lỗi: Đăng nhập không thành công hoặc timeout. URL hiện tại: " + webDriver.getCurrentUrl());
            isLoggedIn = false;
            throw e;
        }
    }
    
    public static void logout() {
        if (driver != null && isLoggedIn) {
            try {
                driver.get("http://127.0.0.1:8000/dang-xuat/");
            } catch (Exception e) {
                System.out.println("Không thể thực hiện logout: " + e.getMessage());
            } finally {
                isLoggedIn = false;
            }
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
