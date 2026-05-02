package pageobjects.bn;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;
import java.util.*;

public class XemVanBanDi {
    private WebDriver driver;
    private WebDriverWait wait;

    public XemVanBanDi(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    public boolean kiemTraHienThiDayDuCot() {
        List<String> mongDoi = Arrays.asList("số đi", "ngày ban hành", "ngày ký", "số ký hiệu", "trích yếu văn bản", "nơi nhận", "trạng thái");
        List<WebElement> headers = driver.findElements(By.cssSelector(".table-custom thead th"));
        List<String> thucTe = new ArrayList<>();
        for (WebElement h : headers) {
            String txt = h.getText().trim().toLowerCase();
            if (!txt.isEmpty()) thucTe.add(txt);
        }
        return thucTe.containsAll(mongDoi);
    }

    public boolean kiemTraSapXepNgayBanHanhGiamDan() {
        List<WebElement> cells = driver.findElements(By.cssSelector("td[data-col='ngay-ban-hanh']"));
        List<String> danhSachNgay = new ArrayList<>();
        for (WebElement cell : cells) {
            danhSachNgay.add(cell.getText().trim());
        }
        
        List<String> copy = new ArrayList<>(danhSachNgay);
        Collections.sort(copy, (a, b) -> daoNguocNgay(b).compareTo(daoNguocNgay(a)));
        return danhSachNgay.equals(copy);
    }

    private String daoNguocNgay(String ngay) {
        if (ngay == null || !ngay.contains("/")) return "";
        String[] p = ngay.split("/");
        if (p.length < 3) return ngay;
        return p[2] + p[1] + p[0];
    }

    public void clickVanBanDauTien() {
        WebElement firstRow = wait.until(ExpectedConditions.elementToBeClickable(By.cssSelector("#data-table-body tr:not(.empty-state)")));
        firstRow.click();
    }

    public void clickVanBanTheoTrangThai(String trangThai) {
        String xpath = "//tr[descendant::span[contains(@class, 'status-badge') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '" + trangThai.toLowerCase() + "')]]";
        WebElement row = wait.until(ExpectedConditions.elementToBeClickable(By.xpath(xpath)));
        row.click();
    }
    
    public boolean kiemTraVanBanCoTrangThai(String trangThai) {
        try {
            String xpath = "//span[contains(@class, 'status-badge') and contains(text(), '" + trangThai + "')]";
            return wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath(xpath))).isDisplayed();
        } catch (Exception e) {
            return false;
        }
    }
    
    public String getTrichYeuDongDauTien() {
        WebElement cell = wait.until(ExpectedConditions.visibilityOfElementLocated(By.cssSelector("#data-table-body tr:first-child td[data-col='trich-yeu']")));
        return cell.getText().trim();
    }
}
