package pageobjects.viet;

import common.viet.Constant;
import org.openqa.selenium.By;
import org.openqa.selenium.JavascriptExecutor;
import org.openqa.selenium.NoSuchElementException;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.text.Normalizer;
import java.time.Duration;
import java.util.List;
import java.util.Locale;
import java.util.stream.Collectors;

public class VanBanDen_List {
    private final By loginTitle = By.xpath("//h4[normalize-space()='Đăng nhập vào hệ thống']");
    private final By errorMessage = By.cssSelector("div.page-message.error");
    private final By documentRows = By.cssSelector("#data-table-body tr");
    private final By firstDocumentCell = By.cssSelector("#data-table-body tr[data-update-url] td");
    private final By firstUnpublishedDocumentCell = By.cssSelector("#data-table-body tr[data-da-ban-hanh-noi-bo='0'] td");
    private final By firstPublishedDocumentCell = By.cssSelector("#data-table-body tr[data-da-ban-hanh-noi-bo='1'] td");
    private final By searchInput = By.id("search-input");
    private final By searchButton = By.id("search-button");
    private final By documentDetailTitle = By.cssSelector("#document-modal.show .modal-header span");
    private final By editButton = By.id("btn-edit");
    private final By publishButton = By.id("btn-publish");
    private final By unpublishButton = By.id("btn-unpublish");
    private final By saveButton = By.id("btn-save");
    private final By cancelButton = By.id("btn-cancel");
    private final By receivedDateField = By.id("m-ngay-nhan");
    private final By signedDateField = By.id("m-ngay-ky");
    private final By documentSymbolField = By.id("m-so-ky-hieu");
    private final By documentTypeField = By.id("m-loai-vb");
    private final By priorityField = By.id("m-muc-do");
    private final By issuingAgencyField = By.id("m-co-quan");
    private final By summaryField = By.id("m-trich-yeu");
    private final By notificationMessage = By.cssSelector("#notification-overlay:not(.hidden) #notification-message");
    private final By modalFormErrors = By.id("modal-form-errors");

    public WebElement getLoginTitle() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(ExpectedConditions.visibilityOfElementLocated(loginTitle));
    }

    public WebElement getErrorMessage() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(ExpectedConditions.visibilityOfElementLocated(errorMessage));
    }

    public String getErrorMessageTextIfPresent() {
        try {
            WebElement message = Constant.WEBDRIVER.findElement(errorMessage);
            return message.isDisplayed() ? message.getText().trim() : "";
        } catch (NoSuchElementException exception) {
            return "";
        }
    }

    public List<String> getPriorityIds() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.visibilityOfElementLocated(documentRows));
        return Constant.WEBDRIVER.findElements(documentRows)
                .stream()
                .map(row -> row.getDomAttribute("data-muc-do-id"))
                .collect(Collectors.toList());
    }

    public void search(String keyword) {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement input = wait.until(ExpectedConditions.visibilityOfElementLocated(searchInput));
        input.clear();
        input.sendKeys(keyword);
        Constant.WEBDRIVER.findElement(searchButton).click();
    }

    public List<String> getVisibleDocumentNumbers() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(documentRows));
        return Constant.WEBDRIVER.findElements(documentRows)
                .stream()
                .filter(WebElement::isDisplayed)
                .map(row -> row.getDomAttribute("data-so-den"))
                .collect(Collectors.toList());
    }

    public List<String> getVisibleDocumentSymbols() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(documentRows));
        return Constant.WEBDRIVER.findElements(documentRows)
                .stream()
                .filter(WebElement::isDisplayed)
                .map(row -> row.getDomAttribute("data-so-ky-hieu"))
                .collect(Collectors.toList());
    }

    public void clickFirstVisibleDocumentRow() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement cell = wait.until(ExpectedConditions.elementToBeClickable(firstDocumentCell));
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript(
                "arguments[0].scrollIntoView({block: 'center'});" +
                        "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));",
                cell
        );
    }

    public void clickFirstUnpublishedDocumentRow() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement cell = wait.until(ExpectedConditions.elementToBeClickable(firstUnpublishedDocumentCell));
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript(
                "arguments[0].scrollIntoView({block: 'center'});" +
                        "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));",
                cell
        );
    }

    public void clickFirstPublishedDocumentRow() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement cell = wait.until(ExpectedConditions.elementToBeClickable(firstPublishedDocumentCell));
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript(
                "arguments[0].scrollIntoView({block: 'center'});" +
                        "arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));",
                cell
        );
    }

    public WebElement getDocumentDetailTitle() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(ExpectedConditions.visibilityOfElementLocated(documentDetailTitle));
    }

    public boolean isEditOrPublishVisible() {
        return isDisplayed(editButton) || isDisplayed(publishButton);
    }

    public boolean isEditButtonVisible() {
        return isDisplayed(editButton);
    }

    public boolean isPublishButtonVisible() {
        return isDisplayed(publishButton);
    }

    public void clickPublishButton() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement button = wait.until(ExpectedConditions.elementToBeClickable(publishButton));
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript("arguments[0].click();", button);
    }

    public void clickUnpublishButton() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement button = wait.until(ExpectedConditions.elementToBeClickable(unpublishButton));
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript("arguments[0].click();", button);
    }

    public String waitForPublishButtonText() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(driver -> {
            WebElement button = driver.findElement(publishButton);
            if (!button.isDisplayed()) {
                return null;
            }

            String text = button.getText().trim();
            return text.isEmpty() ? null : text;
        });
    }

    public String waitForUnpublishButtonText() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(driver -> {
            WebElement button = driver.findElement(unpublishButton);
            if (!button.isDisplayed()) {
                return null;
            }

            String text = button.getText().trim();
            return text.isEmpty() ? null : text;
        });
    }

    public boolean isPublishButtonShowingUnpublish() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(driver -> normalizeText(driver.findElement(unpublishButton).getText())
                .contains("ngung ban hanh"));
    }

    public boolean isUnpublishButtonShowingPublish() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(driver -> normalizeText(driver.findElement(publishButton).getText())
                .contains("ban hanh noi bo"));
    }

    public void clickEditButton() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement button = wait.until(ExpectedConditions.elementToBeClickable(editButton));
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript("arguments[0].click();", button);
    }

    public boolean areDocumentFieldsEditable() {
        return isEditable(receivedDateField)
                && isEditable(signedDateField)
                && isEditable(documentSymbolField)
                && isEditable(documentTypeField)
                && isEditable(priorityField)
                && isEditable(issuingAgencyField)
                && isEditable(summaryField);
    }

    public boolean areDocumentFieldsNotEditable() {
        return !isEditable(receivedDateField)
                && !isEditable(signedDateField)
                && !isEditable(documentSymbolField)
                && !isEditable(documentTypeField)
                && !isEditable(priorityField)
                && !isEditable(issuingAgencyField)
                && !isEditable(summaryField);
    }

    public boolean areSaveAndCancelButtonsVisible() {
        return isDisplayed(saveButton) && isDisplayed(cancelButton);
    }

    public String getDocumentSymbolValue() {
        return Constant.WEBDRIVER.findElement(documentSymbolField).getDomProperty("value");
    }

    public void setDocumentSymbol(String documentSymbol) {
        WebElement element = Constant.WEBDRIVER.findElement(documentSymbolField);
        element.clear();
        element.sendKeys(documentSymbol);
    }

    public void setReceivedDate(String dateValue) {
        setDateValue(receivedDateField, dateValue);
    }

    public void setSignedDate(String dateValue) {
        setDateValue(signedDateField, dateValue);
    }

    public void clickCancelButton() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement button = wait.until(ExpectedConditions.elementToBeClickable(cancelButton));
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript("arguments[0].click();", button);
    }

    public void clickSaveButton() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        WebElement button = wait.until(ExpectedConditions.elementToBeClickable(saveButton));
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript("arguments[0].click();", button);
    }

    public WebElement getNotificationMessage() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(ExpectedConditions.visibilityOfElementLocated(notificationMessage));
    }

    public String getFirstVisibleDocumentSymbol() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(documentRows));
        return Constant.WEBDRIVER.findElements(documentRows)
                .stream()
                .filter(WebElement::isDisplayed)
                .findFirst()
                .map(row -> row.getDomAttribute("data-so-ky-hieu"))
                .orElse("");
    }

    public String getFirstVisibleDocumentNumber() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(documentRows));
        return Constant.WEBDRIVER.findElements(documentRows)
                .stream()
                .filter(WebElement::isDisplayed)
                .findFirst()
                .map(row -> row.getDomAttribute("data-so-den"))
                .orElse("");
    }

    public String getFirstUnpublishedDocumentNumber() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(documentRows));
        return Constant.WEBDRIVER.findElements(documentRows)
                .stream()
                .filter(WebElement::isDisplayed)
                .filter(row -> "0".equals(row.getDomAttribute("data-da-ban-hanh-noi-bo")))
                .findFirst()
                .map(row -> row.getDomAttribute("data-so-den"))
                .orElse("");
    }

    public String getFirstPublishedDocumentNumber() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(documentRows));
        return Constant.WEBDRIVER.findElements(documentRows)
                .stream()
                .filter(WebElement::isDisplayed)
                .filter(row -> "1".equals(row.getDomAttribute("data-da-ban-hanh-noi-bo")))
                .findFirst()
                .map(row -> row.getDomAttribute("data-so-den"))
                .orElse("");
    }

    public String getSecondVisibleDocumentSymbol() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        wait.until(ExpectedConditions.presenceOfAllElementsLocatedBy(documentRows));
        List<String> documentSymbols = Constant.WEBDRIVER.findElements(documentRows)
                .stream()
                .filter(WebElement::isDisplayed)
                .map(row -> row.getDomAttribute("data-so-ky-hieu"))
                .collect(Collectors.toList());
        return documentSymbols.size() > 1 ? documentSymbols.get(1) : "";
    }

    public String getModalFormErrorMessage() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(driver -> {
            String text = driver.findElement(modalFormErrors).getText().trim();
            return text.isEmpty() ? null : text;
        });
    }

    public String getSaveResultMessage() {
        WebDriverWait wait = new WebDriverWait(Constant.WEBDRIVER, Duration.ofSeconds(10));
        return wait.until(driver -> {
            String errorText = driver.findElement(modalFormErrors).getText().trim();
            if (!errorText.isEmpty()) {
                return "ERROR:" + errorText;
            }

            try {
                WebElement notification = driver.findElement(notificationMessage);
                if (notification.isDisplayed()) {
                    return "SUCCESS:" + notification.getText().trim();
                }
            } catch (NoSuchElementException exception) {
                return null;
            }
            return null;
        });
    }

    public boolean isSuccessNotificationVisible() {
        return isDisplayed(notificationMessage);
    }

    private boolean isDisplayed(By locator) {
        try {
            return Constant.WEBDRIVER.findElement(locator).isDisplayed();
        } catch (NoSuchElementException exception) {
            return false;
        }
    }

    private boolean isEditable(By locator) {
        WebElement element = Constant.WEBDRIVER.findElement(locator);
        return element.isEnabled()
                && element.getDomAttribute("readonly") == null
                && element.getDomAttribute("disabled") == null;
    }

    private void setDateValue(By locator, String dateValue) {
        WebElement element = Constant.WEBDRIVER.findElement(locator);
        ((JavascriptExecutor) Constant.WEBDRIVER).executeScript(
                "arguments[0].value = arguments[1];" +
                        "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));" +
                        "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                element,
                dateValue
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
