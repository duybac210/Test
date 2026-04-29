(function () {
    const page = document.querySelector(".van-ban-page");
    const modal = document.getElementById("document-modal");
    const tableBody = document.getElementById("data-table-body");
    const editForm = document.getElementById("document-edit-form");
    const closeModalButton = document.getElementById("close-modal-btn");
    const editButton = document.getElementById("btn-edit");
    const cancelButton = document.getElementById("btn-cancel");
    const editActions = document.getElementById("edit-actions");
    const updateUrlInput = document.getElementById("update-url");
    const registerUrlInput = document.getElementById("register-url");
    const transferUrlInput = document.getElementById("transfer-url");
    const externalPublishUrlInput = document.getElementById("external-publish-url");
    const internalPublishUrlInput = document.getElementById("internal-publish-url");
    const registerButton = document.getElementById("btn-register");
    const transferButton = document.getElementById("btn-transfer");
    const externalPublishButton = document.getElementById("btn-external-publish");
    const internalPublishButton = document.getElementById("btn-internal-publish");
    const errorBox = document.getElementById("modal-form-errors");
    const notificationOverlay = document.getElementById("notification-overlay");
    const notificationMessage = document.getElementById("notification-message");
    const draftLink = document.getElementById("m-ban-du-thao-link");
    const finalLink = document.getElementById("m-ban-chinh-thuc-link");
    const draftUploadInput = document.getElementById("m-ban-du-thao-upload");
    const finalUploadInput = document.getElementById("m-ban-chinh-thuc-upload");
    const draftUploadTrigger = document.getElementById("m-ban-du-thao-trigger");
    const finalUploadTrigger = document.getElementById("m-ban-chinh-thuc-trigger");
    const officialAttachmentList = document.getElementById("m-official-attachment-list");
    const officialAttachmentUploadInput = document.getElementById("m-official-attachment-upload");
    const officialAttachmentUploadTrigger = document.getElementById("m-official-attachment-upload-trigger");
    const attachmentDeleteIdsInput = document.getElementById("m-attachment-delete-ids");
    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");
    const recipientModal = document.getElementById("recipient-modal");
    const closeRecipientModalButton = document.getElementById("close-recipient-modal");
    const recipientSearchInput = document.getElementById("recipient-search-input");
    const recipientItems = document.querySelectorAll(".recipient-item");
    const submitRecipientSelectionButton = document.getElementById("btn-submit-recipient-selection");
    const recipientErrorBox = document.getElementById("recipient-form-errors");
    const dispatchNote = document.getElementById("dispatch-note");

    if (!modal || !tableBody || !editForm) {
        return;
    }

    const canManageDocuments = !page || page.dataset.canManage === "1";

    let activeRow = null;
    let deletedAttachmentIds = new Set();
    let currentOfficialAttachments = [];

    const fieldMap = {
        "m-so-di": "soDi",
        "m-trang-thai": "trangThai",
        "m-ngay-ban-hanh": "ngayBanHanh",
        "m-ngay-ky": "ngayKy",
        "m-so-ky-hieu": "soKyHieu",
        "m-trich-yeu": "trichYeu",
        "m-noi-nhan": "noiNhan",
        "m-loai-vb": "loaiVbId",
        "m-muc-do": "mucDoId",
        "m-nguoi-tao": "nguoiTaoId",
        "m-nguoi-ky": "nguoiKyId",
        "m-ban-du-thao-name": "banDuThaoName",
        "m-ban-chinh-thuc-name": "banChinhThucName",
    };

    function normalizeStatus(status) {
        return (status || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .trim()
            .toLowerCase();
    }

    function isPostRegistrationStatus(status) {
        const normalizedStatus = normalizeStatus(status);
        return ["da dang ky", "cho luan chuyen", "cho phan cong"].includes(normalizedStatus);
    }

    function convertDisplayDateToInput(displayDate) {
        if (!displayDate || displayDate === "NULL") {
            return "";
        }
        const parts = displayDate.split("/");
        if (parts.length !== 3) {
            return displayDate;
        }
        return `${parts[2]}-${parts[1]}-${parts[0]}`;
    }

    function convertInputDateToDisplay(inputDate) {
        if (!inputDate) {
            return "";
        }
        const parts = inputDate.split("-");
        if (parts.length !== 3) {
            return inputDate;
        }
        return `${parts[2]}/${parts[1]}/${parts[0]}`;
    }

    function syncFileLink(linkElement, url) {
        if (url) {
            linkElement.href = url;
            linkElement.classList.remove("disabled");
        } else {
            linkElement.href = "#";
            linkElement.classList.add("disabled");
        }
    }

    function parseAttachments(jsonValue) {
        if (!jsonValue) {
            return [];
        }
        try {
            return JSON.parse(jsonValue);
        } catch (error) {
            return [];
        }
    }

    function renderAttachmentList(container, items, editable) {
        if (!container) {
            return;
        }
        container.innerHTML = "";
        if (!items.length) {
            container.innerHTML = '<div class="attachment-empty">Khong co tep dinh kem.</div>';
            return;
        }
        items.forEach(function (item) {
            const row = document.createElement("div");
            const link = document.createElement("a");
            const actions = document.createElement("div");
            row.className = "attachment-item";
            link.className = "attachment-link";
            link.href = item.url || "#";
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = item.name || "Tep dinh kem";
            if (!item.url) {
                link.classList.add("disabled");
            }
            actions.className = "attachment-actions";
            row.appendChild(link);
            if (editable && item.id) {
                const deleteButton = document.createElement("button");
                deleteButton.type = "button";
                deleteButton.className = "attachment-delete-btn";
                deleteButton.dataset.attachmentId = item.id;
                deleteButton.textContent = "Xóa";
                actions.appendChild(deleteButton);
            }
            if (actions.childNodes.length) {
                row.appendChild(actions);
            }
            container.appendChild(row);
        });
    }

    function mergeAttachmentLists(draftItems, officialItems) {
        const mergedItems = [];
        const seenItems = new Set();

        [...(draftItems || []), ...(officialItems || [])].forEach(function (item) {
            const key = `${item.name || ""}|${item.url || ""}`;
            if (seenItems.has(key)) {
                return;
            }
            seenItems.add(key);
            mergedItems.push(item);
        });

        return mergedItems;
    }

    function updateActionButtons(status) {
        const normalizedStatus = normalizeStatus(status);
        const isWaitingRegister = normalizedStatus === "cho dang ky";
        const isReadyForPostRegistration = isPostRegistrationStatus(status);
        const hasExternalPublished = activeRow && activeRow.dataset.daPhatHanhBenNgoai === "1";
        const hasInternalPublished = activeRow && activeRow.dataset.daBanHanhNoiBo === "1";
        const hasSentAssignment = activeRow && activeRow.dataset.daGuiPhanCong === "1";

        registerButton.classList.toggle("hidden", !canManageDocuments || !isWaitingRegister);
        transferButton.classList.toggle("hidden", !canManageDocuments || !isReadyForPostRegistration || hasSentAssignment);
        externalPublishButton.classList.toggle(
            "hidden",
            !canManageDocuments || !isReadyForPostRegistration || hasExternalPublished
        );
        internalPublishButton.classList.toggle("hidden", !canManageDocuments || !isReadyForPostRegistration);
        internalPublishButton.textContent = hasInternalPublished ? "Ngừng ban hành" : "Ban hành nội bộ";
    }

    function setEditMode(enabled) {
        const editableInputs = editForm.querySelectorAll("input[name], textarea[name], select[name]");
        editableInputs.forEach(function (field) {
            if (field.id === "m-so-di") {
                return;
            }

            if (["m-trang-thai", "m-so-ky-hieu", "m-nguoi-tao", "m-nguoi-ky"].includes(field.id)) {
                field.disabled = true;
                if (field.tagName !== "SELECT") {
                    field.setAttribute("readonly", "readonly");
                }
                field.classList.remove("editable");
                return;
            }

            if (field.matches("select")) {
                field.disabled = !enabled;
            } else {
                if (enabled) {
                    if (field.dataset.dateInput !== undefined) {
                        field.type = "date";
                        field.value = convertDisplayDateToInput(field.value);
                    }
                    field.removeAttribute("readonly");
                } else {
                    if (field.dataset.dateInput !== undefined) {
                        if (field.type === "date") {
                            field.value = convertInputDateToDisplay(field.value);
                        }
                        field.type = "text";
                    }
                    field.setAttribute("readonly", "readonly");
                }
            }

            field.classList.toggle("editable", enabled);
        });

        draftUploadTrigger.disabled = !enabled;
        finalUploadTrigger.disabled = !enabled;
        if (officialAttachmentUploadTrigger) {
            officialAttachmentUploadTrigger.disabled = !enabled;
        }
        const signerDisplayField = document.getElementById("m-nguoi-ky-display");
        if (signerDisplayField) {
            signerDisplayField.classList.remove("hidden");
        }
        if (editButton) {
            editButton.classList.toggle("hidden", enabled || !canManageDocuments);
        }
        editActions.classList.toggle("hidden", !enabled);
        const normalizedStatus = normalizeStatus(document.getElementById("m-trang-thai").value);
        const isWaitingRegister = normalizedStatus === "cho dang ky";
        const isReadyForPostRegistration = isPostRegistrationStatus(document.getElementById("m-trang-thai").value);
        registerButton.classList.toggle("hidden", enabled || !canManageDocuments || !isWaitingRegister);
        transferButton.classList.toggle(
            "hidden",
            enabled || !canManageDocuments || !isReadyForPostRegistration || (activeRow && activeRow.dataset.daGuiPhanCong === "1")
        );
        externalPublishButton.classList.toggle(
            "hidden",
            enabled || !canManageDocuments || !isReadyForPostRegistration || (activeRow && activeRow.dataset.daPhatHanhBenNgoai === "1")
        );
        internalPublishButton.classList.toggle("hidden", enabled || !canManageDocuments || !isReadyForPostRegistration);
        renderAttachmentList(officialAttachmentList, currentOfficialAttachments, enabled);
        errorBox.textContent = "";
    }

    function populateModalFromRow(row) {
        document.getElementById("m-ngay-ban-hanh").type = "text";
        document.getElementById("m-ngay-ky").type = "text";

        const data = {
            soDi: row.dataset.soDi,
            trangThai: row.dataset.trangThai,
            ngayBanHanh: row.dataset.ngayBanHanh || "",
            ngayKy: row.dataset.ngayKy || "",
            soKyHieu: row.dataset.soKyHieu === "NULL" ? "" : row.dataset.soKyHieu,
            trichYeu: row.dataset.trichYeu,
            noiNhan: row.dataset.noiNhan,
            loaiVbId: row.dataset.loaiVbId,
            mucDoId: row.dataset.mucDoId,
            nguoiTaoId: row.dataset.nguoiTaoId,
            nguoiKyId: row.dataset.nguoiKyId,
            nguoiKyDisplay: row.dataset.nguoiKyDisplay || "",
            banDuThaoName: row.dataset.banDuThaoName,
            banDuThaoUrl: row.dataset.banDuThaoUrl,
            banChinhThucName: row.dataset.banChinhThucName,
            banChinhThucUrl: row.dataset.banChinhThucUrl,
            banChinhThucAttachments: parseAttachments(row.dataset.banChinhThucAttachmentsJson),
        };
        currentOfficialAttachments = data.banChinhThucAttachments.slice();
        deletedAttachmentIds = new Set();
        if (attachmentDeleteIdsInput) {
            attachmentDeleteIdsInput.value = "";
        }

        Object.entries(fieldMap).forEach(function ([elementId, key]) {
            const field = document.getElementById(elementId);
            if (field) {
                field.value = data[key] || "";
            }
        });
        const signerDisplayField = document.getElementById("m-nguoi-ky-display");
        if (signerDisplayField) {
            signerDisplayField.value = data.nguoiKyDisplay || "";
        }

        updateUrlInput.value = row.dataset.updateUrl;
        registerUrlInput.value = row.dataset.registerUrl;
        transferUrlInput.value = row.dataset.transferUrl;
        externalPublishUrlInput.value = row.dataset.externalPublishUrl;
        internalPublishUrlInput.value = row.dataset.internalPublishUrl;
        registerButton.href = row.dataset.registerUrl;
        syncFileLink(draftLink, data.banDuThaoUrl);
        syncFileLink(finalLink, data.banChinhThucUrl);
        renderAttachmentList(officialAttachmentList, currentOfficialAttachments, false);
        updateActionButtons(data.trangThai);
        draftUploadInput.value = "";
        finalUploadInput.value = "";
        if (officialAttachmentUploadInput) {
            officialAttachmentUploadInput.value = "";
        }
        errorBox.textContent = "";
    }

    function closeModal() {
        modal.classList.remove("show");
        setEditMode(false);
        activeRow = null;
    }

    function showNotification(message) {
        notificationMessage.textContent = message;
        notificationOverlay.classList.remove("hidden");
        window.setTimeout(function () {
            notificationOverlay.classList.add("hidden");
        }, 1600);
    }

    function filterRows() {
        if (!searchInput) {
            return;
        }

        const keyword = (searchInput.value || "").trim().toLowerCase();
        const rows = tableBody.querySelectorAll("tr[data-update-url]");
        rows.forEach(function (row) {
            const haystack = [
                row.dataset.soDi,
                row.dataset.ngayBanHanh,
                row.dataset.ngayKy,
                row.dataset.soKyHieu,
                row.dataset.trichYeu,
                row.dataset.noiNhan,
                row.dataset.trangThai,
            ]
                .join(" ")
                .toLowerCase();
            row.classList.toggle("hidden", keyword !== "" && !haystack.includes(keyword));
        });
    }

    function applyUpdatedRow(documentData) {
        if (!activeRow) {
            return;
        }

        activeRow.dataset.trangThai = documentData.trang_thai_vb_di;
        if (documentData.ngay_ban_hanh !== undefined) {
            activeRow.dataset.ngayBanHanh = documentData.ngay_ban_hanh;
        }
        if (documentData.ngay_ky !== undefined) {
            activeRow.dataset.ngayKy = documentData.ngay_ky;
        }
        if (documentData.so_ky_hieu !== undefined) {
            activeRow.dataset.soKyHieu = documentData.so_ky_hieu;
        }
        if (documentData.trich_yeu !== undefined) {
            activeRow.dataset.trichYeu = documentData.trich_yeu;
        }
        if (documentData.noi_nhan !== undefined) {
            activeRow.dataset.noiNhan = documentData.noi_nhan;
        }
        if (documentData.nguoi_ky_id !== undefined) {
            activeRow.dataset.nguoiKyId = documentData.nguoi_ky_id;
        }
        if (documentData.nguoi_ky_display !== undefined) {
            activeRow.dataset.nguoiKyDisplay = documentData.nguoi_ky_display;
            const signerDisplayField = document.getElementById("m-nguoi-ky-display");
            if (signerDisplayField) {
                signerDisplayField.value = documentData.nguoi_ky_display;
            }
        }
        if (documentData.ban_du_thao_name !== undefined) {
            activeRow.dataset.banDuThaoName = documentData.ban_du_thao_name;
            activeRow.dataset.banDuThaoUrl = documentData.ban_du_thao_url;
            activeRow.dataset.banDuThaoAttachmentsJson = documentData.ban_du_thao_attachments_json || "[]";
        }
        if (documentData.ban_chinh_thuc_name !== undefined) {
            activeRow.dataset.banChinhThucName = documentData.ban_chinh_thuc_name;
            activeRow.dataset.banChinhThucUrl = documentData.ban_chinh_thuc_url;
            activeRow.dataset.banChinhThucAttachmentsJson = documentData.ban_chinh_thuc_attachments_json || "[]";
        }

        if (documentData.da_phat_hanh_ben_ngoai !== undefined) {
            activeRow.dataset.daPhatHanhBenNgoai = documentData.da_phat_hanh_ben_ngoai ? "1" : "0";
        }
        if (documentData.da_ban_hanh_noi_bo !== undefined) {
            activeRow.dataset.daBanHanhNoiBo = documentData.da_ban_hanh_noi_bo ? "1" : "0";
        }
        if (documentData.da_gui_phan_cong !== undefined) {
            activeRow.dataset.daGuiPhanCong = documentData.da_gui_phan_cong ? "1" : "0";
        }

        const statusCell = activeRow.querySelector('[data-col="trang-thai"]');
        statusCell.innerHTML = `<span class="status-badge ${documentData.status_class || ""}">${documentData.trang_thai_hien_thi || documentData.trang_thai_vb_di}</span>`;
        if (window.applyStatusThemes) {
            window.applyStatusThemes();
        }

        const ngayBanHanhCell = activeRow.querySelector('[data-col="ngay-ban-hanh"]');
        const ngayKyCell = activeRow.querySelector('[data-col="ngay-ky"]');
        const soKyHieuCell = activeRow.querySelector('[data-col="so-ky-hieu"]');

        if (documentData.ngay_ban_hanh !== undefined) {
            ngayBanHanhCell.textContent = documentData.ngay_ban_hanh || "NULL";
            ngayBanHanhCell.classList.toggle("color", !documentData.ngay_ban_hanh);
        }

        if (documentData.ngay_ky !== undefined) {
            ngayKyCell.textContent = documentData.ngay_ky || "NULL";
            ngayKyCell.classList.toggle("color", !documentData.ngay_ky);
        }

        if (documentData.so_ky_hieu !== undefined) {
            soKyHieuCell.textContent = documentData.so_ky_hieu || "NULL";
            soKyHieuCell.classList.toggle("color", !documentData.so_ky_hieu);
        }

        if (documentData.trich_yeu !== undefined) {
            activeRow.querySelector('[data-col="trich-yeu"]').textContent = documentData.trich_yeu;
        }

        if (documentData.noi_nhan !== undefined) {
            activeRow.querySelector('[data-col="noi-nhan"]').textContent = documentData.noi_nhan;
        }
    }

    tableBody.addEventListener("click", function (event) {
        const row = event.target.closest("tr[data-update-url]");
        if (!row) {
            return;
        }
        activeRow = row;
        populateModalFromRow(row);
        setEditMode(false);
        modal.classList.add("show");
    });

    if (editButton) {
        editButton.addEventListener("click", function () {
            setEditMode(true);
        });
    }

    cancelButton.addEventListener("click", function () {
        if (activeRow) {
            populateModalFromRow(activeRow);
        }
        setEditMode(false);
    });

    transferButton.addEventListener("click", function () {
        const csrfToken = editForm.querySelector("[name=csrfmiddlewaretoken]").value;
        fetch(transferUrlInput.value, {
            method: "POST",
            headers: {
                "X-CSRFToken": csrfToken,
                "X-Requested-With": "XMLHttpRequest",
            },
        })
            .then(async function (response) {
                const payload = await response.json();
                if (!response.ok) {
                    throw payload;
                }
                return payload;
            })
            .then(function (payload) {
                applyUpdatedRow({
                    ...(payload.document || {}),
                    da_gui_phan_cong: true,
                });
                populateModalFromRow(activeRow);
                showNotification(payload.message || "Cap nhat thanh cong!");
            })
            .catch(function (payload) {
                errorBox.textContent = (payload && payload.message) || "Khong the luan chuyen van ban.";
            });
    });

    function closeRecipientModal() {
        if (!recipientModal) {
            return;
        }
        recipientModal.classList.remove("show");
        recipientModal.classList.add("hidden");
        if (recipientErrorBox) {
            recipientErrorBox.textContent = "";
        }
    }

    if (externalPublishButton && recipientModal) {
        externalPublishButton.addEventListener("click", function () {
            recipientModal.classList.add("show");
            recipientModal.classList.remove("hidden");
            if (recipientErrorBox) {
                recipientErrorBox.textContent = "";
            }
            if (dispatchNote) {
                dispatchNote.value = "";
            }
            document.querySelectorAll(".recipient-checkbox").forEach(function (checkbox) {
                checkbox.checked = false;
            });
            if (recipientSearchInput) {
                recipientSearchInput.value = "";
                recipientItems.forEach(function (item) {
                    item.classList.remove("hidden");
                });
            }
        });
    }

    if (closeRecipientModalButton) {
        closeRecipientModalButton.addEventListener("click", closeRecipientModal);
    }

    if (recipientModal) {
        recipientModal.addEventListener("click", function (event) {
            if (event.target === recipientModal) {
                closeRecipientModal();
            }
        });
    }

    if (recipientSearchInput) {
        recipientSearchInput.addEventListener("input", function () {
            const keyword = (recipientSearchInput.value || "").trim().toLowerCase();
            recipientItems.forEach(function (item) {
                const haystack = (item.dataset.search || "").toLowerCase();
                item.classList.toggle("hidden", Boolean(keyword) && !haystack.includes(keyword));
            });
        });
    }

    if (submitRecipientSelectionButton) {
        submitRecipientSelectionButton.addEventListener("click", function () {
            const csrfToken = editForm.querySelector("[name=csrfmiddlewaretoken]").value;
            const checkedRecipients = Array.from(document.querySelectorAll(".recipient-checkbox:checked"));
            if (!checkedRecipients.length) {
                recipientErrorBox.textContent = "Vui long chon it nhat mot noi nhan.";
                return;
            }

            const formData = new FormData();
            checkedRecipients.forEach(function (checkbox) {
                formData.append("noi_nhan_ids[]", checkbox.value);
            });
            formData.append("ghi_chu", dispatchNote ? dispatchNote.value.trim() : "");

            fetch(externalPublishUrlInput.value, {
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
                    applyUpdatedRow({
                        trang_thai_vb_di: activeRow.dataset.trangThai,
                        status_class:
                            activeRow.querySelector('[data-col="trang-thai"] .status-badge')?.className.replace("status-badge ", "") || "",
                        da_phat_hanh_ben_ngoai: true,
                    });
                    closeRecipientModal();
                    populateModalFromRow(activeRow);
                    showNotification(payload.message || "Phat hanh ben ngoai thanh cong!");
                })
                .catch(function (payload) {
                    recipientErrorBox.textContent =
                        (payload && payload.message) || "Khong the phat hanh ben ngoai van ban.";
                });
        });
    }

    if (internalPublishButton) {
        internalPublishButton.addEventListener("click", function () {
            const csrfToken = editForm.querySelector("[name=csrfmiddlewaretoken]").value;
            fetch(internalPublishUrlInput.value, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
            })
                .then(async function (response) {
                    const payload = await response.json();
                    if (!response.ok) {
                        throw payload;
                    }
                    return payload;
                })
                .then(function (payload) {
                    applyUpdatedRow({
                        trang_thai_vb_di: activeRow.dataset.trangThai,
                        status_class:
                            activeRow.querySelector('[data-col="trang-thai"] .status-badge')?.className.replace("status-badge ", "") || "",
                        da_ban_hanh_noi_bo: payload.document && payload.document.da_ban_hanh_noi_bo,
                    });
                    populateModalFromRow(activeRow);
                    showNotification(payload.message || "Cap nhat ban hanh noi bo thanh cong!");
                })
                .catch(function (payload) {
                    errorBox.textContent = (payload && payload.message) || "Khong the cap nhat ban hanh noi bo.";
                });
        });
    }

    closeModalButton.addEventListener("click", closeModal);
    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeModal();
        }
    });

    draftUploadTrigger.addEventListener("click", function () {
        if (!draftUploadTrigger.disabled) {
            draftUploadInput.click();
        }
    });

    finalUploadTrigger.addEventListener("click", function () {
        if (!finalUploadTrigger.disabled) {
            finalUploadInput.click();
        }
    });

    if (officialAttachmentUploadTrigger) {
        officialAttachmentUploadTrigger.addEventListener("click", function () {
            if (!officialAttachmentUploadTrigger.disabled && officialAttachmentUploadInput) {
                officialAttachmentUploadInput.click();
            }
        });
    }

    draftUploadInput.addEventListener("change", function () {
        const file = draftUploadInput.files && draftUploadInput.files[0];
        if (file) {
            document.getElementById("m-ban-du-thao-name").value = file.name;
        }
    });

    finalUploadInput.addEventListener("change", function () {
        const file = finalUploadInput.files && finalUploadInput.files[0];
        if (file) {
            document.getElementById("m-ban-chinh-thuc-name").value = file.name;
        }
    });

    function handleAttachmentDelete(event, type) {
        const deleteButton = event.target.closest(".attachment-delete-btn");
        if (!deleteButton) {
            return;
        }
        const attachmentId = deleteButton.dataset.attachmentId;
        if (!attachmentId) {
            return;
        }
        deletedAttachmentIds.add(attachmentId);
        if (attachmentDeleteIdsInput) {
            attachmentDeleteIdsInput.value = Array.from(deletedAttachmentIds).join(",");
        }
        currentOfficialAttachments = currentOfficialAttachments.filter((item) => item.id !== attachmentId);
        renderAttachmentList(officialAttachmentList, currentOfficialAttachments, true);
    }

    if (officialAttachmentList) {
        officialAttachmentList.addEventListener("click", function (event) {
            handleAttachmentDelete(event, "chinh_thuc");
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterRows);
    }

    if (searchButton) {
        searchButton.addEventListener("click", filterRows);
    }

    editForm.addEventListener("submit", function (event) {
        event.preventDefault();

        const csrfToken = editForm.querySelector("[name=csrfmiddlewaretoken]").value;
        const formData = new FormData(editForm);
        if (attachmentDeleteIdsInput) {
            formData.set("tep_dinh_kem_xoa_ids", attachmentDeleteIdsInput.value || "");
        }

        fetch(updateUrlInput.value, {
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
                applyUpdatedRow(payload.document);
                populateModalFromRow(activeRow);
                setEditMode(false);
                showNotification(payload.message || "Luu thanh cong!");
            })
            .catch(function (payload) {
                if (payload && payload.errors) {
                    const firstError = Object.values(payload.errors)[0];
                    errorBox.textContent = Array.isArray(firstError) ? firstError[0] : "Du lieu khong hop le.";
                    return;
                }
                errorBox.textContent = "Khong the luu du lieu. Vui long thu lai.";
            });
    });
})();
