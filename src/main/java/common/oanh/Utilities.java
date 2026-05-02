package common.oanh;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import pageobjects.oanh.LoginPage;
import java.time.Duration;

public class Utilities {
    private static WebDriver driver;
    private static boolean isLoggedIn = false;
    
    public static WebDriver getDriver() {
        if (driver == null) {
            ChromeOptions options = new ChromeOptions();
            options.addArguments("--start-maximized");
            driver = new ChromeDriver(options);
            driver.manage().timeouts().implicitlyWait(Duration.ofSeconds(2));
        }
        return driver;
    }
    
    public static void autoLogin() {
        if (!isLoggedIn) {
            WebDriver driver = getDriver();
            driver.get("http://127.0.0.1:8000/");
            
            LoginPage loginPage = new LoginPage(driver);
            loginPage.login("GV000006", "giaovien123");

            isLoggedIn = true;
        }
    }

    public static void logout() {
        if (driver != null && isLoggedIn) {
            try {

                // 1. Nhấn nút Đăng xuất ở menu trái
                org.openqa.selenium.WebElement menuLogout = driver.findElement(org.openqa.selenium.By.xpath("//a[contains(., 'Đăng xuất')] | //div[contains(., 'Đăng xuất') and @class='menu-item'] | //*[contains(text(), 'Đăng xuất') and not(ancestor::button)]"));
                menuLogout.click();

                // 2. Chờ popup Xác nhận đăng xuất hiện lên
                org.openqa.selenium.support.ui.WebDriverWait wait = new org.openqa.selenium.support.ui.WebDriverWait(driver, Duration.ofSeconds(1));
                org.openqa.selenium.WebElement btnConfirm = wait.until(org.openqa.selenium.support.ui.ExpectedConditions.elementToBeClickable(
                    org.openqa.selenium.By.xpath("//button[contains(text(), 'Đăng xuất')]")
                ));

                // 3. Nhấn Xác nhận
                btnConfirm.click();
                
                // Chờ load về trang chủ
                Thread.sleep(100);
            } catch (Exception e) {
                // Fallback: Tung chiêu cuối xóa trắng toàn bộ dữ liệu đăng nhập nếu không click được nút
                driver.manage().deleteAllCookies();
                ((org.openqa.selenium.JavascriptExecutor) driver).executeScript("window.localStorage.clear(); window.sessionStorage.clear();");
                driver.navigate().refresh();
            }
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
