(function () {
    const hiddenFileInput = document.getElementById("id_file_mau");
    const fileTrigger = document.getElementById("template-file-trigger");
    const fileNameInput = document.getElementById("template-file-name");
    const resetButton = document.getElementById("reset-template-form");
    const placeholder = document.getElementById("preview-placeholder");
    const imagePreview = document.getElementById("preview-image");
    const pdfPreview = document.getElementById("preview-pdf");
    const messagePreview = document.getElementById("preview-message");

    if (!hiddenFileInput || !fileTrigger) {
        return;
    }

    let activeObjectUrl = null;

    function revokeObjectUrl() {
        if (activeObjectUrl) {
            URL.revokeObjectURL(activeObjectUrl);
            activeObjectUrl = null;
        }
    }

    function hidePreview() {
        [placeholder, imagePreview, pdfPreview, messagePreview].forEach(function (element) {
            if (element) {
                element.classList.add("hidden");
            }
        });
        revokeObjectUrl();
        if (imagePreview) {
            imagePreview.removeAttribute("src");
        }
        if (pdfPreview) {
            pdfPreview.removeAttribute("src");
        }
        if (messagePreview) {
            messagePreview.textContent = "";
        }
    }

    function showPlaceholder(message) {
        hidePreview();
        placeholder.textContent = message || "Chưa có file mẫu để xem trước.";
        placeholder.classList.remove("hidden");
    }

    function showMessage(message) {
        hidePreview();
        messagePreview.textContent = message;
        messagePreview.classList.remove("hidden");
    }

    function previewFile(file) {
        const lowerName = file.name.toLowerCase();
        if (file.type.startsWith("image/")) {
            hidePreview();
            activeObjectUrl = URL.createObjectURL(file);
            imagePreview.src = activeObjectUrl;
            imagePreview.classList.remove("hidden");
            return;
        }

        if (file.type === "application/pdf" || lowerName.endsWith(".pdf")) {
            hidePreview();
            activeObjectUrl = URL.createObjectURL(file);
            pdfPreview.src = activeObjectUrl;
            pdfPreview.classList.remove("hidden");
            return;
        }

        showMessage("File mẫu đã được chọn nhưng trình duyệt không hỗ trợ xem trước định dạng này.");
    }

    fileTrigger.addEventListener("click", function () {
        hiddenFileInput.click();
    });

    hiddenFileInput.addEventListener("change", function () {
        const file = hiddenFileInput.files && hiddenFileInput.files[0];
        if (!file) {
            return;
        }
        fileNameInput.value = file.name;
        previewFile(file);
    });

    resetButton.addEventListener("click", function () {
        window.setTimeout(function () {
            fileNameInput.value = "Nhấn để tải file mẫu";
            showPlaceholder();
        }, 0);
    });

    showPlaceholder();
})();
