package pageobjects;

import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.time.Duration;
import java.util.List;

public class ManHinhDuyetVanBan {
    private WebDriver driver;
    private WebDriverWait wait;

    // Locators thực tế từ trình duyệt
    private By searchInput   = By.id("search-input");
    private By searchBtn     = By.id("search-button");
    private By tableRows     = By.cssSelector("tbody tr"); // Sử dụng selector đơn giản hơn
    private By btnApprove    = By.id("btn-approve");
    private By btnRevision   = By.id("btn-request-revision");
    private By revisionText  = By.id("revision-text");
    private By submitRevision= By.id("submit-revision-button");
    private By revisionModal = By.id("revision-modal");
    private By approvalModal = By.id("approval-modal");
    private By notificationOverlay = By.id("notification-overlay");

    public ManHinhDuyetVanBan(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(15));
    }

    /**
     * Tìm văn bản theo trích yếu.
     * Nhập keyword vào ô tìm kiếm rồi click nút Xem.
     */
    public void searchDocument(String keyword) {
        System.out.println("    [DEBUG] Tìm kiếm văn bản với từ khóa: " + keyword);
        WebElement input = wait.until(ExpectedConditions.visibilityOfElementLocated(searchInput));
        input.clear();
        input.sendKeys(keyword);
        driver.findElement(searchBtn).click();
        // Chờ một chút để danh sách cập nhật
        try { Thread.sleep(1000); } catch (InterruptedException ignored) {}
    }

    /**
     * Kiểm tra có ít nhất 1 row hiển thị (không bị hidden) trong bảng.
     */
    public boolean hasVisibleRow() {
        List<WebElement> rows = driver.findElements(tableRows);
        for (WebElement row : rows) {
            if (!row.getAttribute("class").contains("hidden")) {
                return true;
            }
        }
        return false;
    }

    /**
     * Click vào row có trích yếu khớp.
     */
    public void clickDocumentByTrichYeu(String trichYeu) {
        System.out.println("    [DEBUG] Đang tìm dòng có trích yếu: " + trichYeu);
        // Đợi ít nhất 1 dòng xuất hiện trong tbody (ngoại trừ dòng 'Không có dữ liệu' nếu có)
        wait.until(ExpectedConditions.presenceOfElementLocated(tableRows));
        
        List<WebElement> rows = driver.findElements(tableRows);
        System.out.println("    [DEBUG] Số lượng dòng tìm thấy trong bảng: " + rows.size());
        
        String lowerTrichYeu = trichYeu.toLowerCase();
        for (WebElement row : rows) {
            String rowText = row.getText();
            System.out.println("    [DEBUG] Dòng đang xét: " + rowText.replace("\n", " | "));
            // Kiểm tra xem dòng này có chứa trích yếu không
            if (rowText.toLowerCase().contains(lowerTrichYeu)) {
                System.out.println("    [DEBUG] Tìm thấy dòng phù hợp!");
                ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block: 'center'});", row);
                try {
                    row.click();
                } catch (Exception e) {
                    System.out.println("    [DEBUG] Click dòng thất bại, thử bằng Javascript.");
                    ((JavascriptExecutor) driver).executeScript("arguments[0].click();", row);
                }
                
                // Đợi modal hiển thị
                System.out.println("    [DEBUG] Đợi modal chi tiết hiển thị...");
                wait.until(d -> {
                    try {
                        WebElement m = d.findElement(approvalModal);
                        return m.isDisplayed() || (m.getAttribute("class") != null && m.getAttribute("class").contains("show"));
                    } catch (Exception e2) { return false; }
                });
                System.out.println("    [DEBUG] Modal đã hiển thị.");
                return;
            }
        }
        throw new RuntimeException("KHÔNG tìm thấy văn bản có trích yếu: " + trichYeu + " trong danh sách.");
    }

    public void clickDuyet() {
        System.out.println("    [DEBUG] Đang thực hiện clickDuyet...");
        try {
            // Đợi modal xuất hiện (có thể chỉ cần có trong DOM hoặc có class show)
            WebElement modal = wait.until(ExpectedConditions.presenceOfElementLocated(approvalModal));
            System.out.println("    [DEBUG] Modal đã xuất hiện trong DOM.");
            
            // Tìm nút Duyệt (chờ trong DOM)
            WebElement btn = wait.until(ExpectedConditions.presenceOfElementLocated(btnApprove));
            System.out.println("    [DEBUG] Nút Duyệt đã xuất hiện trong DOM. Hiển thị: " + btn.isDisplayed());
            
            // Cuộn vào tầm nhìn để chắc chắn
            ((JavascriptExecutor) driver).executeScript("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", btn);
            try { Thread.sleep(1000); } catch (InterruptedException ignored) {}

            try {
                // Thử click thông thường trước
                btn.click();
                System.out.println("    [DEBUG] Click Duyệt thành công bằng Selenium.");
            } catch (Exception e) {
                System.out.println("    [DEBUG] Click Selenium thất bại, dùng Javascript click: " + e.getMessage());
                ((JavascriptExecutor) driver).executeScript("arguments[0].click();", btn);
                System.out.println("    [DEBUG] Click Duyệt thành công bằng Javascript.");
            }
            
            System.out.println("    [DEBUG] Đợi notification overlay...");
            try {
                wait.until(ExpectedConditions.visibilityOfElementLocated(notificationOverlay));
                wait.until(ExpectedConditions.invisibilityOfElementLocated(notificationOverlay));
                System.out.println("    [DEBUG] Duyệt hoàn tất.");
            } catch (Exception e) {
                System.out.println("    [DEBUG] Không thấy notification hoặc timeout, tiếp tục...");
            }
        } catch (Exception e) {
            System.out.println("    [DEBUG] LỖI trong clickDuyet: " + e.getMessage());
            throw e;
        }
    }

    public void clickYeuCauChinhSua(String noiDung) {
        wait.until(ExpectedConditions.elementToBeClickable(btnRevision)).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(revisionModal));
        WebElement textArea = driver.findElement(revisionText);
        textArea.clear();
        textArea.sendKeys(noiDung);
        driver.findElement(submitRevision).click();
        wait.until(ExpectedConditions.visibilityOfElementLocated(notificationOverlay));
        wait.until(ExpectedConditions.invisibilityOfElementLocated(notificationOverlay));
    }

    /**
     * Kiểm tra modal chi tiết đang hiển thị.
     */
    public boolean isModalVisible() {
        try {
            WebElement modal = driver.findElement(approvalModal);
            return modal.getAttribute("class").contains("show");
        } catch (Exception e) {
            return false;
        }
    }
}
