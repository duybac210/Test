document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector(".account-page[data-mode='recipient-list']");
    if (!page) {
        return;
    }

    const tableBody = document.getElementById("recipient-table-body");
    const searchInput = document.getElementById("search-input");
    const createModal = document.getElementById("create-recipient-modal");
    const detailModal = document.getElementById("recipient-detail-modal");
    const createFeedback = document.getElementById("create-recipient-feedback");
    const detailFeedback = document.getElementById("recipient-modal-feedback");
    const openCreateButton = document.getElementById("btn-open-create-recipient");
    const saveCreateButton = document.getElementById("btn-save-create-recipient");
    const editButton = document.getElementById("btn-edit-recipient");
    const saveButton = document.getElementById("btn-save-recipient");

    const fields = {
        createTen: document.getElementById("create-ten-noi-nhan"),
        createDiaChi: document.getElementById("create-dia-chi"),
        createSoDienThoai: document.getElementById("create-so-dien-thoai"),
        createGmail: document.getElementById("create-gmail"),
        createThongTinKhac: document.getElementById("create-thong-tin-khac"),
        maNoiNhan: document.getElementById("detail-ma-noi-nhan"),
        tenNoiNhan: document.getElementById("detail-ten-noi-nhan"),
        diaChi: document.getElementById("detail-dia-chi"),
        soDienThoai: document.getElementById("detail-so-dien-thoai"),
        gmail: document.getElementById("detail-gmail"),
        thongTinKhac: document.getElementById("detail-thong-tin-khac"),
    };

    let rows = Array.from(document.querySelectorAll(".recipient-row"));
    let currentRow = null;

    function normalizeText(value) {
        return (value || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();
    }

    function buildUrl(template, recipientId) {
        return template.replace("__recipient_id__", recipientId);
    }

    function showFeedback(node, message, level) {
        node.textContent = message;
        node.classList.remove("hidden", "success", "error");
        node.classList.add(level);
    }

    function hideFeedback(node) {
        node.textContent = "";
        node.classList.add("hidden");
        node.classList.remove("success", "error");
    }

    function filterRows() {
        const keyword = normalizeText(searchInput ? searchInput.value : "");
        rows.forEach((row) => {
            const haystack = normalizeText([
                row.dataset.maNoiNhan,
                row.dataset.tenNoiNhan,
                row.dataset.diaChi,
                row.dataset.soDienThoai,
                row.dataset.gmail,
                row.dataset.thongTinKhac,
            ].join(" "));
            row.classList.toggle("hidden", keyword && !haystack.includes(keyword));
        });
    }

    function resetCreateForm() {
        fields.createTen.value = "";
        fields.createDiaChi.value = "";
        fields.createSoDienThoai.value = "";
        fields.createGmail.value = "";
        fields.createThongTinKhac.value = "";
        hideFeedback(createFeedback);
    }

    function toggleEditMode(isEditing) {
        [fields.tenNoiNhan, fields.diaChi, fields.soDienThoai, fields.gmail, fields.thongTinKhac].forEach((field) => {
            field.readOnly = !isEditing;
            field.classList.toggle("bg-gray", !isEditing);
        });
        editButton.classList.toggle("hidden", isEditing);
        saveButton.classList.toggle("hidden", !isEditing);
    }

    function fillModalFromRow(row) {
        fields.maNoiNhan.value = row.dataset.maNoiNhan || "";
        fields.tenNoiNhan.value = row.dataset.tenNoiNhan || "";
        fields.diaChi.value = row.dataset.diaChi || "";
        fields.soDienThoai.value = row.dataset.soDienThoai || "";
        fields.gmail.value = row.dataset.gmail || "";
        fields.thongTinKhac.value = row.dataset.thongTinKhac || "";
        toggleEditMode(false);
        hideFeedback(detailFeedback);
    }

    function applyRecipientDataToRow(row, recipient) {
        row.dataset.tenNoiNhan = recipient.ten_noi_nhan;
        row.dataset.diaChi = recipient.dia_chi;
        row.dataset.soDienThoai = recipient.so_dien_thoai;
        row.dataset.gmail = recipient.gmail;
        row.dataset.thongTinKhac = recipient.thong_tin_khac;
        const cells = row.querySelectorAll("td");
        cells[0].textContent = recipient.ten_noi_nhan;
        cells[1].textContent = recipient.dia_chi || "";
        cells[2].textContent = recipient.so_dien_thoai || "";
    }

    function attachRowEvents(row) {
        row.addEventListener("click", () => {
            currentRow = row;
            fillModalFromRow(row);
            detailModal.classList.remove("hidden");
        });
    }

    async function createRecipient() {
        const formData = new FormData();
        formData.append("ten_noi_nhan", fields.createTen.value);
        formData.append("dia_chi", fields.createDiaChi.value);
        formData.append("so_dien_thoai", fields.createSoDienThoai.value);
        formData.append("gmail", fields.createGmail.value);
        formData.append("thong_tin_khac", fields.createThongTinKhac.value);

        try {
            const response = await fetch(page.dataset.createUrl, {
                method: "POST",
                headers: { "X-CSRFToken": page.dataset.csrfToken },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                showFeedback(createFeedback, data.message || "Khong the them noi nhan.", "error");
                return;
            }
            const emptyRow = tableBody.querySelector(".empty-row");
            if (emptyRow) {
                emptyRow.remove();
            }
            tableBody.insertAdjacentHTML("afterbegin", data.row_html);
            rows = Array.from(document.querySelectorAll(".recipient-row"));
            attachRowEvents(rows[0]);
            createModal.classList.add("hidden");
            resetCreateForm();
        } catch (error) {
            showFeedback(createFeedback, "Khong the them noi nhan.", "error");
        }
    }

    async function saveRecipient() {
        if (!currentRow) {
            return;
        }
        const formData = new FormData();
        formData.append("ten_noi_nhan", fields.tenNoiNhan.value);
        formData.append("dia_chi", fields.diaChi.value);
        formData.append("so_dien_thoai", fields.soDienThoai.value);
        formData.append("gmail", fields.gmail.value);
        formData.append("thong_tin_khac", fields.thongTinKhac.value);

        try {
            const response = await fetch(buildUrl(page.dataset.updateUrlTemplate, fields.maNoiNhan.value), {
                method: "POST",
                headers: { "X-CSRFToken": page.dataset.csrfToken },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                showFeedback(detailFeedback, data.message || "Khong the cap nhat noi nhan.", "error");
                return;
            }
            applyRecipientDataToRow(currentRow, data.recipient);
            fillModalFromRow(currentRow);
            showFeedback(detailFeedback, data.message, "success");
        } catch (error) {
            showFeedback(detailFeedback, "Khong the cap nhat noi nhan.", "error");
        }
    }

    rows.forEach(attachRowEvents);
    if (searchInput) {
        searchInput.addEventListener("input", filterRows);
    }

    document.querySelectorAll("[data-close-modal]").forEach((button) => {
        button.addEventListener("click", () => {
            const modal = document.getElementById(button.dataset.closeModal);
            if (modal) {
                modal.classList.add("hidden");
            }
        });
    });

    [createModal, detailModal].forEach((modal) => {
        if (!modal) {
            return;
        }
        modal.addEventListener("click", (event) => {
            if (event.target === modal) {
                modal.classList.add("hidden");
            }
        });
    });

    openCreateButton.addEventListener("click", () => {
        resetCreateForm();
        createModal.classList.remove("hidden");
    });

    saveCreateButton.addEventListener("click", createRecipient);
    editButton.addEventListener("click", () => {
        hideFeedback(detailFeedback);
        toggleEditMode(true);
    });
    saveButton.addEventListener("click", saveRecipient);
});
