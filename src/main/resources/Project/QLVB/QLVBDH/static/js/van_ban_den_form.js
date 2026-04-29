(function () {
    const primaryInput = document.getElementById("id_file_van_ban");
    const attachmentInput = document.getElementById("id_tep_dinh_kem");
    const fileNameInput = document.getElementById("selected-file-name");
    const primaryTriggerAreas = document.querySelectorAll("[data-primary-file-trigger], #trigger-file-button");
    const attachmentTrigger = document.getElementById("trigger-attachment-button");
    const attachmentListWrapper = document.getElementById("attachment-list-wrapper");
    const attachmentList = document.getElementById("attachment-list");
    const placeholder = document.getElementById("preview-placeholder");
    const imagePreview = document.getElementById("preview-image");
    const pdfPreview = document.getElementById("preview-pdf");
    const wordPreview = document.getElementById("preview-word");
    const messagePreview = document.getElementById("preview-message");

    if (!primaryInput) {
        return;
    }

    let activeObjectUrl = null;
    let attachmentUrls = [];
    const attachmentStore = new DataTransfer();

    function revokeObjectUrl() {
        if (activeObjectUrl) {
            URL.revokeObjectURL(activeObjectUrl);
            activeObjectUrl = null;
        }
    }

    function revokeAttachmentUrls() {
        attachmentUrls.forEach(function (url) {
            URL.revokeObjectURL(url);
        });
        attachmentUrls = [];
    }

    function syncAttachmentStore(files) {
        attachmentStore.items.clear();
        files.forEach(function (file) {
            attachmentStore.items.add(file);
        });
        attachmentInput.files = attachmentStore.files;
    }

    function hideAllPreviews() {
        [placeholder, imagePreview, pdfPreview, wordPreview, messagePreview].forEach((element) => {
            element.classList.add("hidden");
        });
        revokeObjectUrl();
        imagePreview.removeAttribute("src");
        pdfPreview.removeAttribute("src");
        wordPreview.innerHTML = "";
        messagePreview.textContent = "";
    }

    function showPlaceholder(message) {
        hideAllPreviews();
        placeholder.textContent = message || "Chua co tep nao duoc chon.";
        placeholder.classList.remove("hidden");
    }

    function showMessage(message) {
        hideAllPreviews();
        messagePreview.textContent = message;
        messagePreview.classList.remove("hidden");
    }

    function previewImage(file) {
        hideAllPreviews();
        activeObjectUrl = URL.createObjectURL(file);
        imagePreview.src = activeObjectUrl;
        imagePreview.classList.remove("hidden");
    }

    function previewPdf(file) {
        hideAllPreviews();
        activeObjectUrl = URL.createObjectURL(file);
        pdfPreview.src = activeObjectUrl;
        pdfPreview.classList.remove("hidden");
    }

    function previewDocx(file) {
        hideAllPreviews();
        const reader = new FileReader();
        reader.onload = function (event) {
            mammoth.convertToHtml({ arrayBuffer: event.target.result })
                .then(function (result) {
                    wordPreview.innerHTML = result.value || "<p>Khong doc duoc noi dung tep Word.</p>";
                    wordPreview.classList.remove("hidden");
                })
                .catch(function () {
                    showMessage("Khong the xem truoc tep Word nay.");
                });
        };
        reader.readAsArrayBuffer(file);
    }

    function handleFileChange() {
        const files = primaryInput.files ? Array.from(primaryInput.files) : [];
        const file = files[0];
        if (!file) {
            fileNameInput.value = "Nhan bieu tuong de tai 1 tep PDF, Word hoac anh scan";
            showPlaceholder();
            return;
        }

        const lowerName = file.name.toLowerCase();
        fileNameInput.value = file.name;

        if (file.type.startsWith("image/")) {
            previewImage(file);
            return;
        }

        if (file.type === "application/pdf" || lowerName.endsWith(".pdf")) {
            previewPdf(file);
            return;
        }

        if (
            file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document" ||
            lowerName.endsWith(".docx")
        ) {
            previewDocx(file);
            return;
        }

        if (file.type === "application/msword" || lowerName.endsWith(".doc")) {
            showMessage("Tep .doc khong the xem truc tiep tren trinh duyet.");
            return;
        }

        showMessage("Dinh dang tep nay chua duoc ho tro xem truoc.");
    }

    function renderAttachmentList() {
        if (!attachmentList || !attachmentInput) {
            return;
        }

        revokeAttachmentUrls();
        attachmentList.innerHTML = "";
        const files = Array.from(attachmentInput.files || []);
        attachmentListWrapper.classList.toggle("hidden", files.length === 0);

        files.forEach(function (file, index) {
            const item = document.createElement("div");
            const link = document.createElement("a");
            const deleteButton = document.createElement("button");
            const objectUrl = URL.createObjectURL(file);

            attachmentUrls.push(objectUrl);
            item.className = "attachment-item";
            link.className = "attachment-link";
            link.href = objectUrl;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = file.name;

            deleteButton.type = "button";
            deleteButton.className = "attachment-delete";
            deleteButton.textContent = "Xoa";
            deleteButton.addEventListener("click", function () {
                const remainingFiles = Array.from(attachmentInput.files || []).filter(function (_, currentIndex) {
                    return currentIndex !== index;
                });
                syncAttachmentStore(remainingFiles);
                renderAttachmentList();
            });

            item.appendChild(link);
            item.appendChild(deleteButton);
            attachmentList.appendChild(item);
        });
    }

    function appendAttachments() {
        if (!attachmentInput || !attachmentInput.files) {
            return;
        }

        Array.from(attachmentInput.files).forEach(function (file) {
            attachmentStore.items.add(file);
        });
        attachmentInput.files = attachmentStore.files;
        renderAttachmentList();
    }

    primaryTriggerAreas.forEach((element) => {
        element.addEventListener("click", function () {
            primaryInput.click();
        });
    });

    primaryInput.addEventListener("change", handleFileChange);
    attachmentTrigger?.addEventListener("click", function () {
        attachmentInput?.click();
    });
    attachmentInput?.addEventListener("change", appendAttachments);
    document.querySelector(".btn-cancel")?.addEventListener("click", function () {
        window.setTimeout(function () {
            showPlaceholder();
            fileNameInput.value = "Nhan bieu tuong de tai 1 tep PDF, Word hoac anh scan";
            attachmentInput.value = "";
            attachmentStore.items.clear();
            revokeAttachmentUrls();
            if (attachmentList) {
                attachmentList.innerHTML = "";
            }
            attachmentListWrapper?.classList.add("hidden");
        }, 0);
    });

    showPlaceholder();
    renderAttachmentList();
})();
