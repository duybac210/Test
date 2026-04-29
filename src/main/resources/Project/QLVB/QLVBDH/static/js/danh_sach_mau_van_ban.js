document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector(".template-list-page");
    if (!page) {
        return;
    }

    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");
    const rows = Array.from(document.querySelectorAll(".template-row"));
    const modal = document.getElementById("detail-modal");
    const closeModalButton = document.getElementById("close-detail-modal");
    const editButton = document.getElementById("btn-sua");
    const saveButton = document.getElementById("btn-luu");
    const deleteButton = document.getElementById("btn-xoa");
    const feedback = document.getElementById("modal-feedback");
    const fileInput = document.getElementById("detail-file-input");
    const fileTrigger = document.getElementById("detail-file-trigger");
    const fileDownload = document.getElementById("detail-file-download");

    const fields = {
        ma: document.getElementById("detail-ma"),
        ngay: document.getElementById("detail-ngay"),
        ten: document.getElementById("detail-ten"),
        loaiText: document.getElementById("detail-loai-text"),
        loaiSelect: document.getElementById("detail-loai-select"),
        trangThaiText: document.getElementById("detail-trangthai-text"),
        trangThaiSelect: document.getElementById("detail-trangthai-select"),
        mucDich: document.getElementById("detail-mucdich"),
        fileName: document.getElementById("detail-file"),
    };

    let currentRow = null;
    let selectedFile = null;

    function buildUrl(template, id) {
        return template.replace("__template_id__", id);
    }

    function showFeedback(message, level) {
        feedback.textContent = message;
        feedback.classList.remove("hidden", "success", "error");
        feedback.classList.add(level);
    }

    function hideFeedback() {
        feedback.textContent = "";
        feedback.classList.add("hidden");
        feedback.classList.remove("success", "error");
    }

    function setReadOnlyState(isReadOnly) {
        fields.ngay.readOnly = isReadOnly;
        fields.ten.readOnly = isReadOnly;
        fields.mucDich.readOnly = isReadOnly;

        [fields.ngay, fields.ten, fields.mucDich, fields.fileName].forEach((field) => {
            field.classList.toggle("bg-gray", isReadOnly);
        });

        fields.loaiText.classList.toggle("hidden", !isReadOnly);
        fields.trangThaiText.classList.toggle("hidden", !isReadOnly);
        fields.loaiSelect.classList.toggle("hidden", isReadOnly);
        fields.trangThaiSelect.classList.toggle("hidden", isReadOnly);
        fileTrigger.classList.toggle("hidden", isReadOnly);
        editButton.classList.toggle("hidden", !isReadOnly);
        saveButton.classList.toggle("hidden", isReadOnly);
    }

    function updateDownloadLink(fileName, fileUrl) {
        fields.fileName.value = fileName || "";
        if (fileUrl) {
            fileDownload.href = fileUrl;
            fileDownload.classList.remove("hidden");
        } else {
            fileDownload.removeAttribute("href");
            fileDownload.classList.add("hidden");
        }
    }

    function fillModalFromRow(row) {
        fields.ma.value = row.dataset.ma || "";
        fields.ngay.value = row.dataset.ngay || "";
        fields.ten.value = row.dataset.ten || "";
        fields.loaiText.value = row.dataset.loai || "";
        fields.loaiSelect.value = row.dataset.loaiId || "";
        fields.trangThaiText.value = row.dataset.trangthai || "";
        fields.trangThaiSelect.value = row.dataset.trangthai || "";
        fields.mucDich.value = row.dataset.mucdich || "";
        updateDownloadLink(row.dataset.file || "", row.dataset.fileUrl || "");
        fileInput.value = "";
        selectedFile = null;
        hideFeedback();
        setReadOnlyState(true);
    }

    function openModal(row) {
        currentRow = row;
        fillModalFromRow(row);
        modal.classList.remove("hidden");
    }

    function closeModal() {
        modal.classList.add("hidden");
        currentRow = null;
        selectedFile = null;
        fileInput.value = "";
        hideFeedback();
    }

    function applyTemplateToRow(row, template) {
        row.dataset.ma = template.ma_mau_vb;
        row.dataset.ngay = template.ngay_tao;
        row.dataset.ten = template.ten_mau;
        row.dataset.loai = template.ten_loai_vb;
        row.dataset.loaiId = template.ma_loai_vb;
        row.dataset.trangthai = template.trang_thai;
        row.dataset.mucdich = template.muc_dich || "";
        row.dataset.file = template.file_name || "";
        row.dataset.fileUrl = template.file_url || "";

        const cells = row.querySelectorAll("td");
        cells[0].textContent = template.ma_mau_vb;
        cells[1].textContent = template.ngay_tao_display;
        cells[2].textContent = template.ten_mau;
        cells[3].textContent = template.ten_loai_vb;
        cells[4].textContent = template.trang_thai;
        cells[5].textContent = template.muc_dich || "";
    }

    async function saveTemplate() {
        if (!currentRow) {
            return;
        }

        const formData = new FormData();
        formData.append("ngay_tao", fields.ngay.value);
        formData.append("ten_mau", fields.ten.value);
        formData.append("ma_loai_vb", fields.loaiSelect.value);
        formData.append("trang_thai", fields.trangThaiSelect.value);
        formData.append("muc_dich", fields.mucDich.value);
        if (selectedFile) {
            formData.append("file_mau", selectedFile);
        }

        try {
            const response = await fetch(buildUrl(page.dataset.updateUrlTemplate, fields.ma.value), {
                method: "POST",
                headers: {
                    "X-CSRFToken": page.dataset.csrfToken,
                },
                body: formData,
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                const errors = data.errors ? Object.values(data.errors).flat().join(" ") : data.message;
                showFeedback(errors || "Khong the cap nhat mau van ban.", "error");
                return;
            }

            applyTemplateToRow(currentRow, data.template);
            fillModalFromRow(currentRow);
            showFeedback(data.message, "success");
        } catch (error) {
            showFeedback("Khong the cap nhat mau van ban.", "error");
        }
    }

    async function deleteTemplate() {
        if (!currentRow) {
            return;
        }

        if (!window.confirm(`Xoa mau van ban ${fields.ma.value}?`)) {
            return;
        }

        try {
            const response = await fetch(buildUrl(page.dataset.deleteUrlTemplate, fields.ma.value), {
                method: "POST",
                headers: {
                    "X-CSRFToken": page.dataset.csrfToken,
                },
            });
            const data = await response.json();

            if (!response.ok || !data.success) {
                showFeedback(data.message || "Khong the xoa mau van ban.", "error");
                return;
            }

            currentRow.remove();
            closeModal();
        } catch (error) {
            showFeedback("Khong the xoa mau van ban.", "error");
        }
    }

    function filterRows() {
        const keyword = (searchInput.value || "").trim().toLowerCase();
        rows.forEach((row) => {
            const haystack = [
                row.dataset.ma,
                row.dataset.ten,
                row.dataset.loai,
                row.dataset.trangthai,
                row.dataset.mucdich,
            ]
                .join(" ")
                .toLowerCase();
            row.classList.toggle("hidden", keyword !== "" && !haystack.includes(keyword));
        });
    }

    rows.forEach((row) => {
        row.addEventListener("click", () => openModal(row));
    });

    searchInput.addEventListener("input", filterRows);
    searchButton.addEventListener("click", filterRows);
    closeModalButton.addEventListener("click", closeModal);
    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });
    editButton.addEventListener("click", () => {
        hideFeedback();
        setReadOnlyState(false);
    });
    saveButton.addEventListener("click", saveTemplate);
    deleteButton.addEventListener("click", deleteTemplate);
    fileTrigger.addEventListener("click", () => fileInput.click());
    fileInput.addEventListener("change", () => {
        selectedFile = fileInput.files[0] || null;
        if (selectedFile) {
            updateDownloadLink(selectedFile.name, "");
        }
    });
});
