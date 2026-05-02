package pageobjects.bn;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;
import java.util.List;

public class TimVBDi {
    private WebDriver driver;
    private WebDriverWait wait;

    private By txtTimKiem = By.id("search-input");
    private By btnXem = By.id("search-button");
    private By lblThongBaoTrong = By.xpath("//td[contains(text(),'Không tìm thấy văn bản hợp lệ')]");

    public TimVBDi(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    public void timKiemVanBan(String tuKhoa) {
        WebElement input = wait.until(ExpectedConditions.visibilityOfElementLocated(txtTimKiem));
        input.clear();
        input.sendKeys(tuKhoa);
        
        // TIÊU CHUẨN DEV: Lưu lại tham chiếu của DÒNG ĐẦU TIÊN thay vì cả bảng
        List<WebElement> currentRows = driver.findElements(By.cssSelector(".table-custom tbody tr"));
        
        if (!currentRows.isEmpty()) {
            WebElement firstRow = currentRows.get(0);
            driver.findElement(btnXem).click();
            // Đợi chính xác dòng này bị hệ thống gỡ bỏ/thay thế bằng kết quả mới
            wait.until(ExpectedConditions.stalenessOf(firstRow));
        } else {
            driver.findElement(btnXem).click();
            // Nếu bảng đang trống, chỉ cần chờ có dòng mới xuất hiện
            wait.until(ExpectedConditions.presenceOfElementLocated(By.cssSelector(".table-custom tbody tr")));
        }
    }

    public String getThongBaoTrongText() {
        return wait.until(ExpectedConditions.visibilityOfElementLocated(lblThongBaoTrong)).getText();
    }

    public boolean kiemTraKetQuaHienThiSoKyHieu(String soKyHieu) {
        String xpath = "//td[contains(text(),'" + soKyHieu + "')]";
        return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(xpath))).isDisplayed();
    }
    
    public boolean kiemTraKetQuaHienThiLoaiVB(String loaiVB) {
        String xpath = "//td[contains(text(),'" + loaiVB + "')]";
        return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(xpath))).isDisplayed();
    }

    public boolean kiemTraNoiNhanHienThi(String noiNhan) {
        List<WebElement> noiNhanCells = wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(By.cssSelector(".table-custom tbody tr td[data-col='noi-nhan']")));
        if (noiNhanCells.isEmpty()) return false;
        
        for (WebElement cell : noiNhanCells) {
            if (!cell.getText().toLowerCase().contains(noiNhan.toLowerCase())) {
                return false; 
            }
        }
        return true; 
    }
}
