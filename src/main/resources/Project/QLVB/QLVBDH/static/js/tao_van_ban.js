(function () {
    const modal = document.getElementById("template-modal");
    const openModalButton = document.getElementById("open-template-modal");
    const closeModalButton = document.getElementById("close-template-modal");
    const templateRows = document.querySelectorAll(".modal-table tbody tr[data-template-id]");
    const selectedTemplateId = document.getElementById("selected-template-id");
    const loaiVanBanSelect = document.getElementById("id_ma_loai_vb");
    const hiddenFileInput = document.getElementById("id_ban_du_thao");
    const draftFileTrigger = document.getElementById("draft-file-trigger");
    const draftFileName = document.getElementById("draft-file-name");
    const resetFormButton = document.getElementById("reset-form-btn");
    const placeholder = document.getElementById("preview-placeholder");
    const imagePreview = document.getElementById("preview-image");
    const pdfPreview = document.getElementById("preview-pdf");
    const messagePreview = document.getElementById("preview-message");

    if (!modal || !openModalButton) {
        return;
    }

    let activeObjectUrl = null;

    function revokeObjectUrl() {
        if (activeObjectUrl) {
            URL.revokeObjectURL(activeObjectUrl);
            activeObjectUrl = null;
        }
    }

    function hidePreviewElements() {
        [placeholder, imagePreview, pdfPreview, messagePreview].forEach(function (element) {
            if (element) {
                element.classList.add("hidden");
            }
        });
        if (imagePreview) {
            imagePreview.removeAttribute("src");
        }
        if (pdfPreview) {
            pdfPreview.removeAttribute("src");
        }
        if (messagePreview) {
            messagePreview.textContent = "";
        }
        revokeObjectUrl();
    }

    function showPlaceholder(message) {
        hidePreviewElements();
        placeholder.textContent = message || "Chua co file de xem truoc.";
        placeholder.classList.remove("hidden");
    }

    function showMessage(message) {
        hidePreviewElements();
        messagePreview.textContent = message;
        messagePreview.classList.remove("hidden");
    }

    function previewUrl(url, fileName) {
        const lowerName = (fileName || "").toLowerCase();
        if (!url) {
            showPlaceholder();
            return;
        }

        if (lowerName.endsWith(".pdf")) {
            hidePreviewElements();
            pdfPreview.src = url;
            pdfPreview.classList.remove("hidden");
            return;
        }

        if (/\.(png|jpg|jpeg|gif|webp|bmp)$/i.test(lowerName)) {
            hidePreviewElements();
            imagePreview.src = url;
            imagePreview.classList.remove("hidden");
            return;
        }

        showMessage("Tep mau nay khong the xem truc tiep tren trinh duyet. Ban co the tai xuong de soan thao.");
    }

    function previewFile(file) {
        const lowerName = file.name.toLowerCase();
        if (file.type.startsWith("image/")) {
            hidePreviewElements();
            activeObjectUrl = URL.createObjectURL(file);
            imagePreview.src = activeObjectUrl;
            imagePreview.classList.remove("hidden");
            return;
        }

        if (file.type === "application/pdf" || lowerName.endsWith(".pdf")) {
            hidePreviewElements();
            activeObjectUrl = URL.createObjectURL(file);
            pdfPreview.src = activeObjectUrl;
            pdfPreview.classList.remove("hidden");
            return;
        }

        showMessage("Tep du thao da duoc chon nhung trinh duyet khong ho tro xem truoc dinh dang nay.");
    }

    function openModal() {
        modal.classList.remove("hidden");
    }

    function closeModal() {
        modal.classList.add("hidden");
    }

    openModalButton.addEventListener("click", openModal);
    closeModalButton.addEventListener("click", closeModal);

    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    templateRows.forEach(function (row) {
        row.addEventListener("click", function (event) {
            if (event.target.closest(".template-file-link")) {
                return;
            }

            selectedTemplateId.value = row.dataset.templateId || "";
            loaiVanBanSelect.value = row.dataset.loaiVbId || "";
            draftFileName.value = row.dataset.fileName || "Nhan de tai file du thao";
            previewUrl(row.dataset.fileUrl, row.dataset.fileName);
            closeModal();
        });
    });

    draftFileTrigger.addEventListener("click", function () {
        hiddenFileInput.click();
    });

    hiddenFileInput.addEventListener("change", function () {
        const file = hiddenFileInput.files && hiddenFileInput.files[0];
        if (!file) {
            return;
        }
        draftFileName.value = file.name;
        previewFile(file);
    });

    resetFormButton.addEventListener("click", function () {
        window.setTimeout(function () {
            selectedTemplateId.value = "";
            draftFileName.value = "Nhan de tai file du thao";
            showPlaceholder();
        }, 0);
    });

    showPlaceholder();
})();
