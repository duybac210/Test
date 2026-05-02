package pageobjects.oanh;

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

    // Lấy các thẻ th nằm trong bảng có class là table-custom
    private By danhSachCotHeader = By.cssSelector(".table-custom thead th");

    public XemVanBanDi(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
    }

    public List<String> getDanhSachTenCotThucTe() {
        // Đợi ít nhất 1 tiêu đề xuất hiện
        wait.until(ExpectedConditions.presenceOfElementLocated(danhSachCotHeader));

        List<WebElement> headers = driver.findElements(danhSachCotHeader);
        List<String> tenCotList = new ArrayList<>();


        for (WebElement header : headers) {
            String text = header.getText().trim().toLowerCase();
            if (!text.isEmpty()) {
                tenCotList.add(text);
            }
        }
        return tenCotList;
    }

    public boolean kiemTraHienThiDayDuCot() {

        List<String> danhSachMongDoi = Arrays.asList(
                "số đi",
                "ngày ban hành",
                "ngày ký",
                "số ký hiệu",
                "trích yếu văn bản",
                "nơi nhận",
                "trạng thái"
        );

        List<String> danhSachThucTe = getDanhSachTenCotThucTe();
        System.out.println("DEBUG - Thực tế (đã lowercase): " + danhSachThucTe);
        System.out.println("DEBUG - Mong đợi (đã lowercase): " + danhSachMongDoi);
        // Kiểm tra xem danh sách thực tế có chứa toàn bộ các cột mong đợi không
        return danhSachThucTe.containsAll(danhSachMongDoi);
    }

    public boolean kiemTraSapXepNgayBanHanhGiamDan() {
        // 1. Lấy dữ liệu từ cột Ngày ban hành
        List<WebElement> cells = driver.findElements(By.cssSelector(".table-custom tbody tr td:nth-child(2)"));
        List<String> danhSachNgayThucTe = new ArrayList<>();

        for (WebElement cell : cells) {
            String text = cell.getText().trim();
            // Nếu ô trống thì coi là NULL
            danhSachNgayThucTe.add(text.isEmpty() ? null : text);
        }

        // 2. Tạo danh sách mong đợi và sắp xếp
        List<String> danhSachNgayCopy = new ArrayList<>(danhSachNgayThucTe);

        // Sử dụng Comparator tùy chỉnh: Nulls Last và Giảm dần
        Collections.sort(danhSachNgayCopy, Comparator.nullsLast(new Comparator<String>() {
            @Override
            public int compare(String o1, String o2) {
                // Chuyển đổi dd/mm/yyyy thành yyyymmdd để so sánh chuỗi chính xác theo thời gian
                String date1 = daoNguocNgay(o1);
                String date2 = daoNguocNgay(o2);
                return date2.compareTo(date1); // So sánh ngược để lấy giảm dần
            }
        }));

        return danhSachNgayThucTe.equals(danhSachNgayCopy);
    }

    /**
     * Hàm phụ trợ để đổi dd/MM/yyyy thành yyyyMMdd giúp so sánh String chính xác
     */
    private String daoNguocNgay(String ngay) {
        if (ngay == null || !ngay.contains("/")) return "";
        String[] parts = ngay.split("/");
        if (parts.length < 3) return ngay;
        return parts[2] + parts[1] + parts[0]; // Trả về dạng 20260426
    }

    public void clickVanBanDauTien() {
        // Click thẳng vào dòng đầu tiên của bảng (vì mở dưới dạng modal popup chứ không phải thẻ <a>)
        WebElement vanBanDauTien = driver.findElement(By.cssSelector(".table-custom tbody tr:first-child"));
        vanBanDauTien.click();
    }

    public void clickVanBanDaDangKy() {
        clickVanBanTheoTrangThai("đã đăng ký");
    }

    public void clickVanBanTheoTrangThai(String trangThai) {
        // Tìm tất cả các dòng
        java.util.List<org.openqa.selenium.WebElement> rows = driver.findElements(org.openqa.selenium.By.cssSelector(".table-custom tbody tr"));
        for (org.openqa.selenium.WebElement row : rows) {
            try {
                // Kiểm tra xem dòng này có chứa text trạng thái không (không quan tâm cột nào)
                if (row.getText().toLowerCase().contains(trangThai.toLowerCase())) {
                    row.click();
                    return;
                }
            } catch (Exception e) {}
        }
        // Nếu không có dòng nào thì click bừa dòng đầu
        if (!rows.isEmpty()) rows.get(0).click();
    }
}