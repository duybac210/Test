(function () {
    const tableBody = document.getElementById("external-table-body");
    const modal = document.getElementById("external-modal");
    const closeButton = document.getElementById("close-external-modal");
    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");
    const editForm = document.getElementById("external-edit-form");
    const errorBox = document.getElementById("external-form-errors");
    const editButton = document.getElementById("btn-external-edit");
    const cancelButton = document.getElementById("btn-external-cancel");
    const editActions = document.getElementById("external-edit-actions");
    const markSentButton = document.getElementById("btn-mark-sent");
    const updateUrlInput = document.getElementById("external-update-url");
    const markSentUrlInput = document.getElementById("external-mark-sent-url");
    const fileLink = document.getElementById("e-file-link");

    if (!tableBody || !modal || !editForm) {
        return;
    }

    let activeRow = null;

    function filterRows() {
        const keyword = ((searchInput && searchInput.value) || "").trim().toLowerCase();
        tableBody.querySelectorAll("tr[data-record-id]").forEach((row) => {
            const haystack = [
                row.dataset.soVanBan,
                row.dataset.loaiVb,
                row.dataset.soKyHieu,
                row.dataset.trichYeu,
                row.dataset.noiNhan,
                row.dataset.trangThai,
            ]
                .join(" ")
                .toLowerCase();
            row.classList.toggle("hidden", Boolean(keyword) && !haystack.includes(keyword));
        });
    }

    function closeModal() {
        modal.classList.remove("show");
        activeRow = null;
        setEditMode(false);
        errorBox.textContent = "";
    }

    function setFileLink(url) {
        if (url) {
            fileLink.href = url;
            fileLink.classList.remove("disabled");
            return;
        }
        fileLink.href = "#";
        fileLink.classList.add("disabled");
    }

    function populateModal(row) {
        const actions = document.getElementById("external-modal-actions");
        document.getElementById("e-so-van-ban").value = row.dataset.soVanBan || "";
        document.getElementById("e-ngay-ban-hanh").value = row.dataset.ngayBanHanh || "";
        document.getElementById("e-loai-vb").value = row.dataset.loaiVb || "";
        document.getElementById("e-so-ky-hieu").value = row.dataset.soKyHieu || "";
        document.getElementById("e-trich-yeu").value = row.dataset.trichYeu || "";
        document.getElementById("e-nguoi-thuc-hien").value = row.dataset.nguoiThucHien || "";
        document.getElementById("e-thoi-gian-gui").value = row.dataset.thoiGianGui || "";
        document.getElementById("e-noi-nhan-display").value = row.dataset.noiNhan || "";
        document.getElementById("e-noi-nhan").value = row.dataset.maNoiNhan || "";
        document.getElementById("e-ghi-chu").value = row.dataset.ghiChu || "";
        document.getElementById("e-file-name").value = row.dataset.fileName || "";
        updateUrlInput.value = row.dataset.updateUrl || "";
        markSentUrlInput.value = row.dataset.markSentUrl || "";
        setFileLink(row.dataset.fileUrl || "");
        actions.classList.remove("hidden");
        setEditMode(false);
    }

    function setEditMode(enabled) {
        const noteField = document.getElementById("e-ghi-chu");
        const recipientDisplay = document.getElementById("e-noi-nhan-display");
        const recipientSelect = document.getElementById("e-noi-nhan");

        noteField.readOnly = !enabled;
        recipientDisplay.classList.toggle("hidden", enabled);
        recipientSelect.classList.toggle("hidden", !enabled);
        noteField.classList.toggle("editable", enabled);
        recipientSelect.classList.toggle("editable", enabled);
        editButton.classList.toggle("hidden", enabled);
        editActions.classList.toggle("hidden", !enabled);

        const isSent = activeRow && activeRow.dataset.trangThai === "Da gui";
        markSentButton.classList.toggle("hidden", enabled || isSent);
        if (!enabled) {
            if (isSent) {
                document.getElementById("external-modal-actions").classList.add("hidden");
            } else {
                document.getElementById("external-modal-actions").classList.remove("hidden");
                editButton.classList.remove("hidden");
            }
        }
        errorBox.textContent = "";
    }

    function applyUpdatedRow(record) {
        if (!activeRow) {
            return;
        }
        activeRow.dataset.noiNhan = record.noi_nhan_tong_hop || "";
        activeRow.dataset.maNoiNhan = record.ma_noi_nhan || "";
        activeRow.dataset.ghiChu = record.ghi_chu || "";
        activeRow.dataset.trangThai = record.trang_thai || "";
        activeRow.dataset.thoiGianGui = record.thoi_gian_gui || "";
        activeRow.querySelector("td:nth-child(7)").textContent = record.noi_nhan_tong_hop || "";
        activeRow.querySelector("td:nth-child(8) .status-badge").textContent = record.trang_thai || "";
    }

    tableBody.addEventListener("click", (event) => {
        const row = event.target.closest("tr[data-record-id]");
        if (!row) {
            return;
        }
        activeRow = row;
        populateModal(row);
        modal.classList.add("show");
    });

    editButton.addEventListener("click", () => {
        setEditMode(true);
    });

    cancelButton.addEventListener("click", () => {
        if (activeRow) {
            populateModal(activeRow);
        }
        setEditMode(false);
    });

    editForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const csrfToken = editForm.querySelector("[name=csrfmiddlewaretoken]").value;
        const formData = new FormData();
        formData.append("ma_noi_nhan", document.getElementById("e-noi-nhan").value);
        formData.append("ghi_chu", document.getElementById("e-ghi-chu").value.trim());

        fetch(updateUrlInput.value, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
            body: formData,
        })
            .then(async (response) => {
                const payload = await response.json();
                if (!response.ok) {
                    throw payload;
                }
                return payload;
            })
            .then((payload) => {
                applyUpdatedRow(payload.record);
                populateModal(activeRow);
            })
            .catch((payload) => {
                errorBox.textContent = (payload && payload.message) || "Khong the cap nhat ban ghi.";
            });
    });

    markSentButton.addEventListener("click", () => {
        const csrfToken = editForm.querySelector("[name=csrfmiddlewaretoken]").value;
        fetch(markSentUrlInput.value, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then(async (response) => {
                const payload = await response.json();
                if (!response.ok) {
                    throw payload;
                }
                return payload;
            })
            .then((payload) => {
                applyUpdatedRow(payload.record);
                populateModal(activeRow);
            })
            .catch((payload) => {
                errorBox.textContent = (payload && payload.message) || "Khong the danh dau da gui.";
            });
    });

    closeButton.addEventListener("click", closeModal);
    modal.addEventListener("click", (event) => {
        if (event.target === modal) {
            closeModal();
        }
    });

    if (searchInput) {
        searchInput.addEventListener("input", filterRows);
    }
    if (searchButton) {
        searchButton.addEventListener("click", filterRows);
    }
})();
