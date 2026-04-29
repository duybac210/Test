(function () {
    const page = document.querySelector(".approval-page");
    const tableBody = document.getElementById("approval-table-body");
    const modal = document.getElementById("approval-modal");
    const form = document.getElementById("approval-form");
    const closeModalButton = document.getElementById("close-modal-btn");
    const approveButton = document.getElementById("btn-approve");
    const requestRevisionButton = document.getElementById("btn-request-revision");
    const delegateButton = document.getElementById("btn-delegate");
    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");
    const errorBox = document.getElementById("modal-form-errors");
    const notificationOverlay = document.getElementById("notification-overlay");
    const notificationMessage = document.getElementById("notification-message");
    const revisionModal = document.getElementById("revision-modal");
    const closeRevisionModalButton = document.getElementById("close-revision-modal");
    const submitRevisionButton = document.getElementById("submit-revision-button");
    const revisionText = document.getElementById("revision-text");
    const revisionErrors = document.getElementById("revision-errors");
    const delegateModal = document.getElementById("delegate-modal");
    const closeDelegateModalButton = document.getElementById("close-delegate-modal");
    const submitDelegateButton = document.getElementById("submit-delegate-button");
    const delegateSelect = document.getElementById("delegate-id");
    const delegateErrors = document.getElementById("delegate-errors");

    if (!page || !tableBody || !modal || !form) {
        return;
    }

    let activeRow = null;

    function buildUrl(template, documentId) {
        return template.replace("__document_id__", documentId);
    }

    function showNotification(message) {
        notificationMessage.textContent = message;
        notificationOverlay.classList.remove("hidden");
        window.setTimeout(function () {
            notificationOverlay.classList.add("hidden");
        }, 1600);
    }

    function syncDraftLink(name, url) {
        const link = document.getElementById("m-ban-du-thao-link");
        const nameField = document.getElementById("m-ban-du-thao-name");
        nameField.value = name || "";
        if (url) {
            link.href = url;
            link.classList.remove("disabled");
        } else {
            link.href = "#";
            link.classList.add("disabled");
        }
    }

    function populateModal(row) {
        document.getElementById("m-so-vb").value = row.dataset.soVb;
        document.getElementById("m-so-vb-display").value = row.dataset.soVb || "";
        document.getElementById("m-ngay-ban-hanh").value = row.dataset.ngayBanHanhDisplay || "";
        document.getElementById("m-loai-vb").value = row.dataset.loaiVb || "";
        document.getElementById("m-so-ky-hieu").value = row.dataset.soKyHieu || "";
        document.getElementById("m-trich-yeu").value = row.dataset.trichYeu || "";
        document.getElementById("m-co-quan-ban-hanh").value = row.dataset.coQuanBanHanh || "";
        document.getElementById("m-noi-nhan").value = row.dataset.noiNhan || "";
        document.getElementById("m-nguoi-soan").value = row.dataset.nguoiSoan || "";
        document.getElementById("m-nguoi-ky").value = row.dataset.nguoiKy || "";
        document.getElementById("m-revision-request").value = row.dataset.latestRevisionRequest || "";
        document.getElementById("m-revision-author").value = row.dataset.latestRevisionAuthor || "";
        syncDraftLink(row.dataset.banDuThaoName || "", row.dataset.banDuThaoUrl || "");
        approveButton.textContent = row.dataset.canForward === "1" ? "Trinh duyet" : "Duyet";
        delegateButton.classList.toggle("hidden", row.dataset.canDelegate !== "1");
        errorBox.textContent = "";
    }

    function filterRows() {
        const keyword = (searchInput.value || "").trim().toLowerCase();
        const rows = tableBody.querySelectorAll("tr[data-so-vb]");
        rows.forEach((row) => {
            const haystack = [
                row.dataset.soVb,
                row.dataset.loaiVb,
                row.dataset.soKyHieu,
                row.dataset.trichYeu,
                row.dataset.coQuanBanHanh,
                row.dataset.tinhTrang,
            ]
                .join(" ")
                .toLowerCase();
            row.classList.toggle("hidden", keyword !== "" && !haystack.includes(keyword));
        });
    }

    function updateRowFromResponse(documentData) {
        if (!activeRow) {
            return;
        }

        activeRow.dataset.tinhTrang = documentData.tinh_trang_phan_cong;
        activeRow.dataset.assignedIds = (documentData.assigned_ids || []).join(",");
        activeRow.dataset.chiDao = documentData.chi_dao || "";
        const statusCell = activeRow.querySelector('[data-col="tinh-trang"]');
        statusCell.textContent = documentData.tinh_trang_phan_cong;
        statusCell.classList.toggle("status-done", documentData.tinh_trang_phan_cong === "Da phan cong");
        statusCell.classList.toggle("status-pending", documentData.tinh_trang_phan_cong !== "Da phan cong");
    }

    function closeModal() {
        modal.classList.remove("show");
        revisionModal.classList.remove("show");
        delegateModal.classList.remove("show");
        activeRow = null;
    }

    tableBody.addEventListener("click", function (event) {
        const row = event.target.closest("tr[data-so-vb]");
        if (!row) {
            return;
        }
        activeRow = row;
        populateModal(row);
        modal.classList.add("show");
    });

    closeModalButton.addEventListener("click", closeModal);
    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    searchInput.addEventListener("input", filterRows);
    searchButton.addEventListener("click", filterRows);

    function submitApprovalAction(action, extraData) {
        if (!activeRow) {
            return;
        }

        const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
        const documentId = document.getElementById("m-so-vb").value;
        const formData = new FormData();
        formData.append("action", action);
        Object.entries(extraData || {}).forEach(function ([key, value]) {
            formData.append(key, value);
        });

        fetch(buildUrl(page.dataset.approveUrlTemplate, documentId), {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
            body: formData,
        })
            .then(async function (response) {
                const payload = await response.json();
                if (!response.ok) {
                    throw payload;
                }
                return payload;
            })
            .then(function (payload) {
                showNotification(payload.message || "Da cap nhat van ban.");
                activeRow.remove();
                closeModal();
            })
            .catch(function (payload) {
                errorBox.textContent = (payload && payload.message) || "Khong the duyet van ban.";
            });
    }

    approveButton.addEventListener("click", function () {
        submitApprovalAction(activeRow && activeRow.dataset.canForward === "1" ? "forward" : "approve");
    });

    requestRevisionButton.addEventListener("click", function () {
        revisionText.value = "";
        revisionErrors.textContent = "";
        revisionModal.classList.add("show");
    });

    submitRevisionButton.addEventListener("click", function () {
        if (!revisionText.value.trim()) {
            revisionErrors.textContent = "Vui long nhap noi dung yeu cau chinh sua.";
            return;
        }
        submitApprovalAction("request_revision", { yc_chinh_sua: revisionText.value.trim() });
    });

    delegateButton.addEventListener("click", function () {
        delegateSelect.value = "";
        delegateErrors.textContent = "";
        delegateModal.classList.add("show");
    });

    submitDelegateButton.addEventListener("click", function () {
        if (!delegateSelect.value) {
            delegateErrors.textContent = "Vui long chon nguoi duoc uy quyen.";
            return;
        }
        submitApprovalAction("delegate", { delegate_id: delegateSelect.value });
    });

    if (closeRevisionModalButton) {
        closeRevisionModalButton.addEventListener("click", function () {
            revisionModal.classList.remove("show");
        });
    }
    if (closeDelegateModalButton) {
        closeDelegateModalButton.addEventListener("click", function () {
            delegateModal.classList.remove("show");
        });
    }
    if (revisionModal) {
        revisionModal.addEventListener("click", function (event) {
            if (event.target === revisionModal) {
                revisionModal.classList.remove("show");
            }
        });
    }
    if (delegateModal) {
        delegateModal.addEventListener("click", function (event) {
            if (event.target === delegateModal) {
                delegateModal.classList.remove("show");
            }
        });
    }
})();
