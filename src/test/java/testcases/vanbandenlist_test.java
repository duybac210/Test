package testcases;

import common.viet.Constant;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;
import pageobjects.viet.DashboardPage;
import pageobjects.viet.LoginPage;
import pageobjects.viet.VanBanDen_List;

import java.text.Normalizer;
import java.util.List;
import java.util.Locale;
import java.util.Map;

public class vanbandenlist_test {
    @BeforeMethod
    public void beforeMethod(){
        System.out.println("Pre-condition");
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--force-device-scale-factor=0.75");
        Constant.WEBDRIVER=new ChromeDriver(options);
        Constant.WEBDRIVER.manage().window().maximize();
    }
    @AfterMethod
    public void afterMethod(){
        System.out.println("Post-condition");
        Constant.WEBDRIVER.quit();
    }
    @Test
    public void TC01(){
        Constant.WEBDRIVER.get(Constant.VAN_BAN_DEN_URL);

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        String actualTitle = vanBanDenList.getLoginTitle().getText();

        Assert.assertEquals(actualTitle, "Đăng nhập vào hệ thống");
    }

    @Test
    public void TC02(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.VIEW_ONLY_USERNAME, Constant.PASSWORD);
        Constant.WEBDRIVER.get(Constant.VAN_BAN_DEN_URL);

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        String actualMessage = vanBanDenList.getErrorMessageTextIfPresent();
        if (!actualMessage.isBlank()) {
            Assert.assertEquals(actualMessage, "Ban khong co quyen truy cap chuc nang nay.");
        } else {
            Assert.assertFalse(
                    Constant.WEBDRIVER.getCurrentUrl().startsWith(Constant.VAN_BAN_DEN_URL),
                    "User view-only van truy cap duoc trang van ban den."
            );
        }
    }

    @Test
    public void TC03(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        List<String> priorityIds = vanBanDenList.getPriorityIds();

        Assert.assertTrue(
                isSortedByPriority(priorityIds),
                "Danh sách văn bản đến chưa được sắp xếp theo mức độ ưu tiên. Actual: "
                        + priorityIds
                        + ". Expected order: MD00000001 -> MD00000002 -> MD00000003 -> MD00000004."
        );
    }

    private boolean isSortedByPriority(List<String> priorityIds) {
        Map<String, Integer> priorityOrder = Map.of(
                "MD00000001", 1,
                "MD00000002", 2,
                "MD00000003", 3,
                "MD00000004", 4
        );

        for (int i = 1; i < priorityIds.size(); i++) {
            int previousPriority = priorityOrder.getOrDefault(priorityIds.get(i - 1), Integer.MAX_VALUE);
            int currentPriority = priorityOrder.getOrDefault(priorityIds.get(i), Integer.MAX_VALUE);
            if (previousPriority > currentPriority) {
                return false;
            }
        }
        return true;
    }

    @Test
    public void TC04(){
        String expectedDocumentNumber = "VBD0000004";

        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.search(expectedDocumentNumber);
        List<String> actualDocumentNumbers = vanBanDenList.getVisibleDocumentNumbers();

        Assert.assertFalse(actualDocumentNumbers.isEmpty(), "Khong tim thay van ban co so den " + expectedDocumentNumber);
        Assert.assertTrue(
                actualDocumentNumbers.stream().allMatch(expectedDocumentNumber::equals),
                "Ket qua tim kiem khong dung. Actual: " + actualDocumentNumbers
        );
    }

    @Test
    public void TC05(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        String actualTitle = vanBanDenList.getDocumentDetailTitle().getText();

        Assert.assertEquals(actualTitle, "CHI TIẾT VĂN BẢN ĐẾN");
    }

    @Test
    public void TC06(){
        String expectedDocumentSymbol = "QD-NTD2025";

        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.search(expectedDocumentSymbol);
        List<String> actualDocumentSymbols = vanBanDenList.getVisibleDocumentSymbols();

        Assert.assertFalse(actualDocumentSymbols.isEmpty(), "Khong tim thay van ban co so ky hieu " + expectedDocumentSymbol);
        Assert.assertTrue(
                actualDocumentSymbols.stream().allMatch(expectedDocumentSymbol::equals),
                "Ket qua tim kiem khong dung. Actual: " + actualDocumentSymbols
        );
    }

    @Test
    public void TC07(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.BOARD_USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        String actualTitle = vanBanDenList.getDocumentDetailTitle().getText();

        Assert.assertEquals(actualTitle, "CHI TIẾT VĂN BẢN ĐẾN");
        Assert.assertFalse(vanBanDenList.isEditOrPublishVisible(), "Van ban den dang hien nut chinh sua hoac ban hanh.");
    }

    @Test
    public void TC08(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        String actualTitle = vanBanDenList.getDocumentDetailTitle().getText();

        Assert.assertEquals(actualTitle, "CHI TIẾT VĂN BẢN ĐẾN");
        Assert.assertTrue(vanBanDenList.isEditButtonVisible(), "Khong hien nut Chinh sua.");
        Assert.assertTrue(vanBanDenList.isPublishButtonVisible(), "Khong hien nut Ban hanh noi bo.");
    }

    @Test
    public void TC09(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        Assert.assertEquals(vanBanDenList.getDocumentDetailTitle().getText(), "CHI TIẾT VĂN BẢN ĐẾN");

        vanBanDenList.clickEditButton();

        Assert.assertTrue(vanBanDenList.areDocumentFieldsEditable(), "Mot so truong van ban den chua chuyen sang editable.");
        Assert.assertTrue(vanBanDenList.areSaveAndCancelButtonsVisible(), "Nut Luu hoac Huy chua hien thi.");
    }

    @Test
    public void TC10(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        Assert.assertEquals(vanBanDenList.getDocumentDetailTitle().getText(), "CHI TIẾT VĂN BẢN ĐẾN");

        String originalDocumentSymbol = vanBanDenList.getDocumentSymbolValue();

        vanBanDenList.clickEditButton();
        vanBanDenList.setDocumentSymbol("testchinhsua");
        vanBanDenList.clickCancelButton();

        String actualDocumentSymbol = vanBanDenList.getDocumentSymbolValue();
        Assert.assertEquals(actualDocumentSymbol, originalDocumentSymbol);
        Assert.assertTrue(vanBanDenList.areDocumentFieldsNotEditable(), "Cac truong van ban den van con editable sau khi nhan Huy.");
    }

    @Test
    public void TC11(){
        String expectedDocumentSymbol = "Dachinhsua";

        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        Assert.assertEquals(vanBanDenList.getDocumentDetailTitle().getText(), "CHI TIẾT VĂN BẢN ĐẾN");

        vanBanDenList.clickEditButton();
        vanBanDenList.setDocumentSymbol(expectedDocumentSymbol);
        vanBanDenList.clickSaveButton();

        Assert.assertFalse(vanBanDenList.getNotificationMessage().getText().isBlank(), "He thong chua hien thong bao sau khi luu.");
        Assert.assertEquals(vanBanDenList.getDocumentSymbolValue(), expectedDocumentSymbol);
        Assert.assertEquals(vanBanDenList.getFirstVisibleDocumentSymbol(), expectedDocumentSymbol);
    }

    @Test
    public void TC12(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        Assert.assertEquals(vanBanDenList.getDocumentDetailTitle().getText(), "CHI TIẾT VĂN BẢN ĐẾN");

        vanBanDenList.clickEditButton();
        vanBanDenList.setSignedDate("2026-04-22");
        vanBanDenList.setReceivedDate("2026-04-17");
        vanBanDenList.clickSaveButton();

        String saveResultMessage = vanBanDenList.getSaveResultMessage();
        Assert.assertFalse(
                saveResultMessage.startsWith("SUCCESS:"),
                "He thong da luu thanh cong voi ngay khong hop le. Actual: " + saveResultMessage
        );

        String actualErrorMessage = saveResultMessage.replace("ERROR:", "");
        Assert.assertTrue(
                actualErrorMessage.toLowerCase().contains("ngay nhan")
                        || actualErrorMessage.toLowerCase().contains("ngày nhận"),
                "Thong bao loi khong dung. Actual: " + actualErrorMessage
        );
    }

    @Test
    public void TC13(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        Assert.assertEquals(vanBanDenList.getDocumentDetailTitle().getText(), "CHI TIẾT VĂN BẢN ĐẾN");

        vanBanDenList.clickEditButton();
        vanBanDenList.setSignedDate("2026-04-22");
        vanBanDenList.setReceivedDate("2026-05-01");
        vanBanDenList.clickSaveButton();

        String saveResultMessage = vanBanDenList.getSaveResultMessage();
        Assert.assertFalse(
                saveResultMessage.startsWith("SUCCESS:"),
                "He thong da luu thanh cong voi ngay nhan lon hon ngay hien tai. Actual: " + saveResultMessage
        );

        String actualErrorMessage = saveResultMessage.replace("ERROR:", "");
        Assert.assertTrue(
                actualErrorMessage.toLowerCase().contains("ngay nhan")
                        || actualErrorMessage.toLowerCase().contains("ngày nhận"),
                "Thong bao loi khong dung. Actual: " + actualErrorMessage
        );
    }

    @Test
    public void TC14(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        Assert.assertEquals(vanBanDenList.getDocumentDetailTitle().getText(), "CHI TIẾT VĂN BẢN ĐẾN");

        vanBanDenList.clickEditButton();
        vanBanDenList.setReceivedDate("2026-04-30");
        vanBanDenList.setSignedDate("2026-05-01");
        vanBanDenList.clickSaveButton();

        String saveResultMessage = vanBanDenList.getSaveResultMessage();
        Assert.assertFalse(
                saveResultMessage.startsWith("SUCCESS:"),
                "He thong da luu thanh cong voi ngay ky lon hon ngay hien tai. Actual: " + saveResultMessage
        );

        String actualErrorMessage = saveResultMessage.replace("ERROR:", "");
        Assert.assertTrue(
                actualErrorMessage.toLowerCase().contains("ngay ky")
                        || actualErrorMessage.toLowerCase().contains("ngày ký"),
                "Thong bao loi khong dung. Actual: " + actualErrorMessage
        );
    }

    @Test
    public void TC15(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        vanBanDenList.clickFirstVisibleDocumentRow();
        Assert.assertEquals(vanBanDenList.getDocumentDetailTitle().getText(), "CHI TIẾT VĂN BẢN ĐẾN");

        vanBanDenList.clickEditButton();
        vanBanDenList.setDocumentSymbol("");
        vanBanDenList.clickSaveButton();

        String saveResultMessage = vanBanDenList.getSaveResultMessage();
        Assert.assertFalse(
                saveResultMessage.startsWith("SUCCESS:"),
                "He thong da luu thanh cong khi so ky hieu bi bo trong. Actual: " + saveResultMessage
        );

        String actualErrorMessage = saveResultMessage.replace("ERROR:", "");
        Assert.assertTrue(
                actualErrorMessage.toLowerCase().contains("bắt buộc")
                        || actualErrorMessage.toLowerCase().contains("bat buoc")
                        || actualErrorMessage.toLowerCase().contains("required")
                        || actualErrorMessage.toLowerCase().contains("số ký hiệu")
                        || actualErrorMessage.toLowerCase().contains("so ky hieu"),
                "Thong bao loi khong dung. Actual: " + actualErrorMessage
        );
    }

    @Test
    public void TC16(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        String duplicatedDocumentSymbol = vanBanDenList.getSecondVisibleDocumentSymbol();
        Assert.assertFalse(duplicatedDocumentSymbol.isBlank(), "Khong lay duoc so ky hieu cua van ban thu hai.");

        vanBanDenList.clickFirstVisibleDocumentRow();
        Assert.assertEquals(vanBanDenList.getDocumentDetailTitle().getText(), "CHI TIẾT VĂN BẢN ĐẾN");

        vanBanDenList.clickEditButton();
        vanBanDenList.setDocumentSymbol(duplicatedDocumentSymbol);
        vanBanDenList.clickSaveButton();

        String saveResultMessage = vanBanDenList.getSaveResultMessage();
        Assert.assertFalse(
                saveResultMessage.startsWith("SUCCESS:"),
                "He thong da luu thanh cong khi so ky hieu bi trung. Actual: " + saveResultMessage
        );

        String actualErrorMessage = saveResultMessage.replace("ERROR:", "");
        Assert.assertTrue(
                actualErrorMessage.toLowerCase().contains("trùng")
                        || actualErrorMessage.toLowerCase().contains("trung")
                        || actualErrorMessage.toLowerCase().contains("số ký hiệu")
                        || actualErrorMessage.toLowerCase().contains("so ky hieu"),
                "Thong bao loi khong dung. Actual: " + actualErrorMessage
        );
    }

    @Test
    public void TC17(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        String expectedDocumentNumber = vanBanDenList.getFirstUnpublishedDocumentNumber();
        Assert.assertFalse(expectedDocumentNumber.isBlank(), "Khong tim thay van ban chua ban hanh noi bo.");

        vanBanDenList.clickFirstUnpublishedDocumentRow();
        Assert.assertEquals(normalizeText(vanBanDenList.getDocumentDetailTitle().getText()), "chi tiet van ban den");
        Assert.assertTrue(vanBanDenList.isPublishButtonVisible(), "Khong hien nut Ban hanh noi bo.");

        vanBanDenList.clickPublishButton();

        String actualMessage = vanBanDenList.getNotificationMessage().getText();
        String expectedMessage = "Da ban hanh noi bo van ban den " + expectedDocumentNumber + ".";
        Assert.assertEquals(normalizeText(actualMessage), normalizeText(expectedMessage));
        Assert.assertTrue(
                vanBanDenList.isPublishButtonShowingUnpublish(),
                "Nut Ban hanh noi bo chua chuyen sang Ngung ban hanh. Actual: "
                        + vanBanDenList.waitForUnpublishButtonText()
        );
    }

    @Test
    public void TC18(){
        Constant.WEBDRIVER.get(Constant.WEB_URL);

        LoginPage loginPage = new LoginPage();
        loginPage.login(Constant.USERNAME, Constant.PASSWORD);

        DashboardPage dashboardPage = new DashboardPage();
        dashboardPage.clickVanBanDenTaskbarButton();

        VanBanDen_List vanBanDenList = new VanBanDen_List();
        String expectedDocumentNumber = vanBanDenList.getFirstPublishedDocumentNumber();
        Assert.assertFalse(expectedDocumentNumber.isBlank(), "Khong tim thay van ban da ban hanh noi bo.");

        vanBanDenList.clickFirstPublishedDocumentRow();
        Assert.assertEquals(normalizeText(vanBanDenList.getDocumentDetailTitle().getText()), "chi tiet van ban den");
        Assert.assertTrue(
                vanBanDenList.isPublishButtonShowingUnpublish(),
                "Khong hien nut Ngung ban hanh."
        );

        vanBanDenList.clickUnpublishButton();

        String actualMessage = vanBanDenList.getNotificationMessage().getText();
        String expectedMessage = "Da ngung ban hanh van ban den " + expectedDocumentNumber + ".";
        Assert.assertEquals(normalizeText(actualMessage), normalizeText(expectedMessage));
        Assert.assertTrue(
                vanBanDenList.isUnpublishButtonShowingPublish(),
                "Nut Ngung ban hanh chua chuyen sang Ban hanh noi bo. Actual: "
                        + vanBanDenList.waitForPublishButtonText()
        );
    }

    private String normalizeText(String text) {
        return Normalizer.normalize(text, Normalizer.Form.NFD)
                .replaceAll("\\p{M}", "")
                .replace('\u0111', 'd')
                .replace('\u0110', 'D')
                .toLowerCase(Locale.ROOT)
                .trim();
    }
}
