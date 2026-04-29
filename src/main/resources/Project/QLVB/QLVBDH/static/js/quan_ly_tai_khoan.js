document.addEventListener("DOMContentLoaded", () => {
    const page = document.querySelector(".account-page");
    if (!page) {
        return;
    }

    const mode = page.dataset.mode;
    const searchInput = document.getElementById("search-input");
    const rows = Array.from(document.querySelectorAll(".teacher-row"));

    function normalizeText(value) {
        return (value || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();
    }

    function buildUrl(template, teacherId) {
        return template.replace("__teacher_id__", teacherId);
    }

    function filterRows() {
        const keyword = normalizeText(searchInput ? searchInput.value : "");
        rows.forEach((row) => {
            const haystack = normalizeText([
                row.dataset.maGv,
                row.dataset.hoTen,
                row.dataset.chucVu,
                row.dataset.toChuyenMon,
                row.dataset.groupNames,
            ].join(" "));
            row.classList.toggle("hidden", keyword && !haystack.includes(keyword));
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterRows);
    }

    if (mode === "user-list") {
        setupUserListPage(page, rows, buildUrl);
    }

    if (mode === "permission-list") {
        setupPermissionPage(page, rows, buildUrl);
    }
});

function setupUserListPage(page, rows, buildUrl) {
    const tableBody = document.getElementById("teacher-table-body");
    const createModal = document.getElementById("create-teacher-modal");
    const detailModal = document.getElementById("teacher-detail-modal");
    const resetModal = document.getElementById("reset-password-modal");
    const createFeedback = document.getElementById("create-teacher-feedback");
    const detailFeedback = document.getElementById("teacher-modal-feedback");
    const resetFeedback = document.getElementById("reset-modal-feedback");
    const openCreateButton = document.getElementById("btn-open-create-teacher");
    const saveCreateButton = document.getElementById("btn-save-create-teacher");
    const editButton = document.getElementById("btn-edit-teacher");
    const saveButton = document.getElementById("btn-save-teacher");
    const openResetButton = document.getElementById("btn-open-reset-password");
    const confirmResetButton = document.getElementById("btn-confirm-reset-password");

    const fields = {
        createMaGv: document.getElementById("create-ma-gv"),
        createHoTen: document.getElementById("create-ho-ten"),
        createChucVu: document.getElementById("create-chuc-vu"),
        createMaTo: document.getElementById("create-ma-to"),
        createTrangThai: document.getElementById("create-trang-thai"),
        maGv: document.getElementById("detail-ma-gv"),
        hoTen: document.getElementById("detail-ho-ten"),
        chucVu: document.getElementById("detail-chuc-vu"),
        toText: document.getElementById("detail-to-text"),
        toSelect: document.getElementById("detail-to-select"),
        lastLogin: document.getElementById("detail-last-login"),
        trangThaiText: document.getElementById("detail-trang-thai-text"),
        trangThaiSelect: document.getElementById("detail-trang-thai-select"),
        resetPassword: document.getElementById("reset-password"),
        resetConfirmPassword: document.getElementById("reset-confirm-password"),
    };

    let currentRow = null;

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

    function toggleEditMode(isEditing) {
        fields.hoTen.readOnly = !isEditing;
        fields.chucVu.readOnly = !isEditing;
        fields.toText.classList.toggle("hidden", isEditing);
        fields.toSelect.classList.toggle("hidden", !isEditing);
        fields.trangThaiText.classList.toggle("hidden", isEditing);
        fields.trangThaiSelect.classList.toggle("hidden", !isEditing);
        [fields.hoTen, fields.chucVu].forEach((field) => field.classList.toggle("bg-gray", !isEditing));
        editButton.classList.toggle("hidden", isEditing);
        saveButton.classList.toggle("hidden", !isEditing);
    }

    function fillModalFromRow(row) {
        fields.maGv.value = row.dataset.maGv || "";
        fields.hoTen.value = row.dataset.hoTen || "";
        fields.chucVu.value = row.dataset.chucVu || "";
        fields.toText.value = row.dataset.toChuyenMon || "";
        fields.toSelect.value = row.dataset.maTo || "";
        fields.lastLogin.value = row.dataset.lastLogin || "Chua dang nhap";
        fields.trangThaiText.value = row.dataset.trangThai || "";
        fields.trangThaiSelect.value = row.dataset.trangThai || "";
        toggleEditMode(false);
        hideFeedback(detailFeedback);
    }

    function resetCreateForm() {
        fields.createMaGv.value = "";
        fields.createHoTen.value = "";
        fields.createChucVu.value = "";
        fields.createMaTo.value = "";
        fields.createTrangThai.value = "Hoat dong";
        hideFeedback(createFeedback);
    }

    function applyTeacherDataToRow(row, teacher) {
        row.dataset.hoTen = teacher.ho_ten;
        row.dataset.chucVu = teacher.chuc_vu;
        row.dataset.maTo = teacher.ma_to;
        row.dataset.toChuyenMon = teacher.to_chuyen_mon;
        row.dataset.lastLogin = teacher.lan_cuoi_dang_nhap;
        row.dataset.trangThai = teacher.trang_thai_tk;
        const cells = row.querySelectorAll("td");
        cells[0].textContent = teacher.ho_ten;
        cells[1].textContent = teacher.chuc_vu || "";
        cells[2].textContent = teacher.to_chuyen_mon || "";
    }

    function attachRowEvents(row) {
        row.addEventListener("click", () => {
            currentRow = row;
            fillModalFromRow(row);
            detailModal.classList.remove("hidden");
        });
    }

    async function createTeacher() {
        const formData = new FormData();
        formData.append("ma_gv", fields.createMaGv.value);
        formData.append("ho_ten", fields.createHoTen.value);
        formData.append("chuc_vu", fields.createChucVu.value);
        formData.append("ma_to", fields.createMaTo.value);
        formData.append("trang_thai_tk", fields.createTrangThai.value);

        try {
            const response = await fetch(page.dataset.createUrl, {
                method: "POST",
                headers: { "X-CSRFToken": page.dataset.csrfToken },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                const errors = data.errors ? Object.values(data.errors).flat().join(" ") : data.message;
                showFeedback(createFeedback, errors || "Khong the them giao vien.", "error");
                return;
            }

            const emptyRow = tableBody.querySelector(".empty-row");
            if (emptyRow) {
                emptyRow.remove();
            }
            tableBody.insertAdjacentHTML("afterbegin", data.row_html);
            const newRow = tableBody.querySelector(".teacher-row");
            attachRowEvents(newRow);
            createModal.classList.add("hidden");
            resetCreateForm();
        } catch (error) {
            showFeedback(createFeedback, "Khong the them giao vien.", "error");
        }
    }

    async function saveTeacher() {
        if (!currentRow) {
            return;
        }

        const formData = new FormData();
        formData.append("ho_ten", fields.hoTen.value);
        formData.append("chuc_vu", fields.chucVu.value);
        formData.append("ma_to", fields.toSelect.value);
        formData.append("trang_thai_tk", fields.trangThaiSelect.value);

        try {
            const response = await fetch(buildUrl(page.dataset.updateUrlTemplate, fields.maGv.value), {
                method: "POST",
                headers: { "X-CSRFToken": page.dataset.csrfToken },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                const errors = data.errors ? Object.values(data.errors).flat().join(" ") : data.message;
                showFeedback(detailFeedback, errors || "Khong the cap nhat tai khoan.", "error");
                return;
            }

            applyTeacherDataToRow(currentRow, data.teacher);
            fillModalFromRow(currentRow);
            showFeedback(detailFeedback, data.message, "success");
        } catch (error) {
            showFeedback(detailFeedback, "Khong the cap nhat tai khoan.", "error");
        }
    }

    async function resetPassword() {
        if (!currentRow) {
            return;
        }

        if (!window.confirm("Bạn có chắc muốn reset mật khẩu không?")) {
            return;
        }

        const formData = new FormData();
        formData.append("password", fields.resetPassword.value);
        formData.append("confirm_password", fields.resetConfirmPassword.value);

        try {
            const response = await fetch(buildUrl(page.dataset.resetUrlTemplate, fields.maGv.value), {
                method: "POST",
                headers: { "X-CSRFToken": page.dataset.csrfToken },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                showFeedback(resetFeedback, data.message || "Khong the reset mat khau.", "error");
                return;
            }

            hideFeedback(resetFeedback);
            fields.resetPassword.value = "";
            fields.resetConfirmPassword.value = "";
            resetModal.classList.add("hidden");
            showFeedback(detailFeedback, data.message, "success");
        } catch (error) {
            showFeedback(resetFeedback, "Khong the reset mat khau.", "error");
        }
    }

    rows.forEach(attachRowEvents);

    document.querySelectorAll("[data-close-modal]").forEach((button) => {
        button.addEventListener("click", () => {
            const modal = document.getElementById(button.dataset.closeModal);
            if (modal) {
                modal.classList.add("hidden");
            }
        });
    });

    [createModal, detailModal, resetModal].forEach((modal) => {
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
    saveCreateButton.addEventListener("click", createTeacher);
    editButton.addEventListener("click", () => {
        hideFeedback(detailFeedback);
        toggleEditMode(true);
    });
    saveButton.addEventListener("click", saveTeacher);
    openResetButton.addEventListener("click", () => {
        hideFeedback(resetFeedback);
        fields.resetPassword.value = "";
        fields.resetConfirmPassword.value = "";
        resetModal.classList.remove("hidden");
    });
    confirmResetButton.addEventListener("click", resetPassword);
}

function setupPermissionPage(page, rows, buildUrl) {
    const modal = document.getElementById("permission-modal");
    const feedback = document.getElementById("permission-modal-feedback");
    const saveButton = document.getElementById("btn-save-permissions");
    const teacherCode = document.getElementById("permission-teacher-code");
    const teacherName = document.getElementById("permission-teacher-name");
    const checkboxes = Array.from(document.querySelectorAll(".permission-checkbox"));
    let currentRow = null;

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

    function openModal(row) {
        currentRow = row;
        teacherCode.textContent = row.dataset.maGv || "";
        teacherName.textContent = row.dataset.hoTen || "";
        const activeIds = (row.dataset.groupIds || "").split(",").filter(Boolean);
        checkboxes.forEach((checkbox) => {
            checkbox.checked = activeIds.includes(checkbox.value);
        });
        hideFeedback();
        modal.classList.remove("hidden");
    }

    async function savePermissions() {
        if (!currentRow) {
            return;
        }

        const formData = new FormData();
        checkboxes
            .filter((checkbox) => checkbox.checked)
            .forEach((checkbox) => formData.append("nhom_quyen", checkbox.value));

        try {
            const response = await fetch(buildUrl(page.dataset.permissionUrlTemplate, currentRow.dataset.maGv), {
                method: "POST",
                headers: { "X-CSRFToken": page.dataset.csrfToken },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                const errors = data.errors ? Object.values(data.errors).flat().join(" ") : data.message;
                showFeedback(errors || "Khong the cap nhat phan quyen.", "error");
                return;
            }

            currentRow.dataset.groupNames = data.teacher.nhom_quyen_display;
            currentRow.dataset.groupIds = checkboxes
                .filter((checkbox) => checkbox.checked)
                .map((checkbox) => checkbox.value)
                .join(",");
            const displayCell = currentRow.querySelector(".teacher-group-display");
            if (displayCell) {
                displayCell.textContent = data.teacher.nhom_quyen_display;
            }
            showFeedback(data.message, "success");
        } catch (error) {
            showFeedback("Khong the cap nhat phan quyen.", "error");
        }
    }

    rows.forEach((row) => {
        const button = row.querySelector("[data-open-permission]");
        if (button) {
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                openModal(row);
            });
        }
    });

    document.querySelectorAll("[data-close-modal]").forEach((button) => {
        button.addEventListener("click", () => {
            const targetModal = document.getElementById(button.dataset.closeModal);
            if (targetModal) {
                targetModal.classList.add("hidden");
            }
        });
    });

    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            modal.classList.add("hidden");
        }
    });

    saveButton.addEventListener("click", savePermissions);
}
