package pageobjects.oanh;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;
import java.time.Duration;

public class ChiTietVBDi {
    private WebDriver driver;
    private WebDriverWait wait;

    public ChiTietVBDi(WebDriver driver) {
        this.driver = driver;

    }

    public boolean kiemTraTrangChiTietHienThi() {
        try {
            // Chờ tối đa 10s cho đến khi hiển thị form có tiêu đề CHI TIẾT VĂN BẢN ĐI
            wait.until(org.openqa.selenium.support.ui.ExpectedConditions.visibilityOfElementLocated(
                org.openqa.selenium.By.xpath("//*[contains(text(), 'CHI TIẾT VĂN BẢN ĐI')]")
            ));
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    public void clickChinhSua() {
        // Tìm nút Chỉnh sửa / Sửa
        driver.findElement(org.openqa.selenium.By.xpath("//button[contains(text(), 'Chỉnh sửa') or contains(text(), 'Sửa')]")).click();
    }

    public void suaThongTin(String loaiVanBan, String noiNhan) {
        // 1. Sửa Loại văn bản

        try {
            // 1. Tìm thẻ select dựa trên text của label đứng trước nó
            // XPath này tìm label có chữ 'Loại văn bản', sau đó lấy thẻ select ngay kế tiếp
            String xpathSelect = "//label[contains(text(), 'Loại văn bản')]/following-sibling::select[1]";

            org.openqa.selenium.WebElement element = driver.findElement(org.openqa.selenium.By.xpath(xpathSelect));

            // 2. Sử dụng class Select để chọn
            org.openqa.selenium.support.ui.Select selectLoaiVB = new org.openqa.selenium.support.ui.Select(element);

            // 3. Chọn theo đúng text (ví dụ: "Công Văn")
            selectLoaiVB.selectByVisibleText(loaiVanBan);

            System.out.println("Đã chọn thành công: " + loaiVanBan);

        } catch (Exception e) {
            System.out.println("Không thể chọn loại văn bản theo text. Lỗi: " + e.getMessage());
        }

        // 2. Sửa Nơi nhận
        try {
            org.openqa.selenium.WebElement inputNoiNhan = driver.findElement(org.openqa.selenium.By.xpath("//label[contains(text(),'Nơi nhận') or contains(text(),'Nơi Nhận')]/following::input[1] | //label[contains(text(),'Nơi')]/following::input[1]"));
            inputNoiNhan.sendKeys(org.openqa.selenium.Keys.CONTROL + "a");
            inputNoiNhan.sendKeys(org.openqa.selenium.Keys.BACK_SPACE);
            inputNoiNhan.sendKeys(noiNhan);
        } catch (Exception e) {
            System.out.println("Không tìm thấy trường Nơi nhận để sửa!");
        }
    }

    public void clickLuu() {
        driver.findElement(org.openqa.selenium.By.xpath("//button[contains(text(), 'Lưu') or contains(text(), 'Cập nhật')]")).click();
    }

    public void clickHuy() {
        driver.findElement(org.openqa.selenium.By.xpath("//button[contains(text(), 'Hủy') or contains(text(), 'Hủy bỏ')]")).click();
    }

    public boolean kiemTraThongBaoLuuThanhCong() {
        try {
            wait.until(org.openqa.selenium.support.ui.ExpectedConditions.visibilityOfElementLocated(
                org.openqa.selenium.By.xpath("//*[contains(text(), 'thành công') or contains(text(), 'Thành công')]")
            ));
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    public boolean kiemTraThongTinSauKhiSua(String loaiVanBan, String noiNhan) {
        String pageText = driver.getPageSource().toLowerCase();
        return pageText.contains(loaiVanBan.toLowerCase()) && pageText.contains(noiNhan.toLowerCase());
    }

    public boolean kiemTraTruongBiKhoa(String tenTruong) {
        try {
            org.openqa.selenium.WebElement element = driver.findElement(org.openqa.selenium.By.xpath("//label[contains(text(),'" + tenTruong + "')]/following::*[self::input or self::select or self::textarea][1]"));
            String disabled = element.getAttribute("disabled");
            String readonly = element.getAttribute("readonly");
            return (disabled != null && disabled.equals("true")) || (readonly != null && readonly.equals("true"));
        } catch (Exception e) {
            return false;
        }
    }

    public void xoaNoiNhan() {
        try {
            org.openqa.selenium.WebElement inputNoiNhan = driver.findElement(org.openqa.selenium.By.xpath("//label[contains(text(),'Nơi nhận')]/following::input[1]"));
            inputNoiNhan.sendKeys(org.openqa.selenium.Keys.CONTROL + "a");
            inputNoiNhan.sendKeys(org.openqa.selenium.Keys.BACK_SPACE);
            inputNoiNhan.clear();
        } catch (Exception e) {}
    }

    public void suaNgay(String ngayBanHanh, String ngayKy) {
        try {
            org.openqa.selenium.WebElement txtNgayBH = driver.findElement(org.openqa.selenium.By.xpath("//label[contains(text(),'Ngày ban hành')]/following::input[1]"));
            txtNgayBH.sendKeys(org.openqa.selenium.Keys.CONTROL + "a");
            txtNgayBH.sendKeys(ngayBanHanh);

            org.openqa.selenium.WebElement txtNgayKy = driver.findElement(org.openqa.selenium.By.xpath("//label[contains(text(),'Ngày ký')]/following::input[1]"));
            txtNgayKy.sendKeys(org.openqa.selenium.Keys.CONTROL + "a");
            txtNgayKy.sendKeys(ngayKy);
        } catch (Exception e) {}
    }


    public boolean kiemTraNgayBiNull() {
        try {
            org.openqa.selenium.WebElement txtNgayBH = driver.findElement(org.openqa.selenium.By.xpath("//label[contains(text(),'Ngày ban hành')]/following::input[1]"));
            org.openqa.selenium.WebElement txtNgayKy = driver.findElement(org.openqa.selenium.By.xpath("//label[contains(text(),'Ngày ký')]/following::input[1]"));
            
            String valBH = txtNgayBH.getAttribute("value");
            String valKy = txtNgayKy.getAttribute("value");
            
            // Trả về true nếu một trong hai ô ngày bị biến thành null hoặc rỗng
            return (valBH == null || valBH.trim().isEmpty()) || (valKy == null || valKy.trim().isEmpty());
        } catch (Exception e) {
            return false; // Nếu không tìm thấy ô, tạm coi như không lỗi
        }
    }

    public boolean kiemTraNutChinhSuaTrangThai() {
        try {
            org.openqa.selenium.WebElement btn = driver.findElement(org.openqa.selenium.By.xpath("//button[contains(text(), 'Chỉnh sửa') or contains(text(), 'Sửa')]"));
            return btn.isDisplayed() && btn.isEnabled();
        } catch (Exception e) {
            return false; // Không hiển thị
        }
    }

    public boolean kiemTraNutChuyenPhanCongTrangThai() {
        try {
            org.openqa.selenium.WebElement btn = driver.findElement(org.openqa.selenium.By.xpath("//button[contains(text(), 'Chuyển phân công') or contains(text(), 'Phân công')]"));
            return btn.isDisplayed() && btn.isEnabled();
        } catch (Exception e) {
            return false; // Không hiển thị
        }
    }

    public boolean kiemTraThongBaoHienThi(String text) {
        try {
            // Đợi thông báo xuất hiện và kiểm tra xem text có tồn tại trong mã nguồn trang không
            wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//*[contains(text(), '" + text + "')]")));
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
