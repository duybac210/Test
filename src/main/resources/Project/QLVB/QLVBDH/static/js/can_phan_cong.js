(function () {
    const page = document.querySelector(".assignment-page");
    const tableBody = document.getElementById("data-table-body");
    const detailModal = document.getElementById("detailModal");
    const confirmModal = document.getElementById("confirmModal");
    const peopleModal = document.getElementById("peopleModal");
    const previewModal = document.getElementById("previewModal");
    const closeDetailButton = document.getElementById("close-detail-modal");
    const closePeopleButton = document.getElementById("close-people-modal");
    const closePreviewButton = document.getElementById("close-preview-modal");
    const openConfirmButton = document.getElementById("open-confirm-button");
    const openPeopleButton = document.getElementById("open-people-modal");
    const cancelConfirmButton = document.getElementById("cancel-confirm-button");
    const acceptConfirmButton = document.getElementById("accept-confirm-button");
    const cancelPeopleButton = document.getElementById("cancel-people-button");
    const acceptPeopleButton = document.getElementById("accept-people-button");
    const previewButton = document.getElementById("m-file-preview");
    const errorBox = document.getElementById("modal-errors");
    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");
    const peopleSearchInput = document.getElementById("people-search-input");
    const peopleCheckboxes = Array.from(document.querySelectorAll(".people-checkbox"));
    const peopleItems = Array.from(document.querySelectorAll(".people-item"));
    const peopleInstructionInputs = Array.from(document.querySelectorAll(".people-instruction-input"));

    if (!page || !tableBody || !detailModal) {
        return;
    }

    const fields = {
        recordId: document.getElementById("m-record-id"),
        loaiRecord: document.getElementById("m-loai-record"),
        ngay: document.getElementById("m-ngay"),
        soVanBan: document.getElementById("m-sovanban"),
        kyHieu: document.getElementById("m-kyhieu"),
        loai: document.getElementById("m-loai"),
        coQuan: document.getElementById("m-coquan"),
        trichYeu: document.getElementById("m-trichyeu"),
        file: document.getElementById("m-file"),
        fileLink: document.getElementById("m-file-link"),
        donVi: document.getElementById("m-donvi"),
        donViDisplay: document.getElementById("m-donvi-display"),
        hanHoanThanh: document.getElementById("m-hanhoanthanh"),
    };

    const previewPlaceholder = document.getElementById("preview-placeholder");
    const previewImage = document.getElementById("preview-image");
    const previewPdf = document.getElementById("preview-pdf");
    const previewWord = document.getElementById("preview-word");
    const previewMessage = document.getElementById("preview-message");

    let selectedRow = null;
    let selectedAssignments = {};

    function resetPreview() {
        previewPlaceholder.classList.add("hidden");
        previewImage.classList.add("hidden");
        previewPdf.classList.add("hidden");
        previewWord.classList.add("hidden");
        previewMessage.classList.add("hidden");
        previewImage.removeAttribute("src");
        previewPdf.removeAttribute("src");
        previewWord.innerHTML = "";
        previewMessage.textContent = "";
    }

    function setSelectedValues(valuesCsv, assignmentDetailsCsv) {
        const selectedValues = new Set((valuesCsv || "").split(",").filter(Boolean));
        let assignmentDetails = [];
        if (assignmentDetailsCsv) {
            try {
                assignmentDetails = JSON.parse(assignmentDetailsCsv);
            } catch (error) {
                assignmentDetails = [];
            }
        }

        selectedAssignments = {};
        assignmentDetails.forEach((detail) => {
            selectedAssignments[String(detail.id)] = {
                id: String(detail.id),
                name: detail.name || "",
                instruction: detail.instruction || "",
                selected: true,
            };
        });

        Array.from(fields.donVi.options).forEach((option) => {
            option.selected = selectedValues.has(option.value);
            if (!selectedAssignments[option.value]) {
                selectedAssignments[option.value] = {
                    id: option.value,
                    name: option.text,
                    instruction: "",
                    selected: option.selected,
                };
            } else {
                selectedAssignments[option.value].selected = option.selected;
                selectedAssignments[option.value].name = selectedAssignments[option.value].name || option.text;
            }
        });
        peopleCheckboxes.forEach((checkbox) => {
            checkbox.checked = selectedValues.has(checkbox.value);
            if (!selectedAssignments[checkbox.value]) {
                selectedAssignments[checkbox.value] = {
                    id: checkbox.value,
                    name: checkbox.dataset.name,
                    instruction: "",
                    selected: checkbox.checked,
                };
            } else {
                selectedAssignments[checkbox.value].selected = checkbox.checked;
                selectedAssignments[checkbox.value].name = selectedAssignments[checkbox.value].name || checkbox.dataset.name;
            }
        });
        peopleInstructionInputs.forEach((input) => {
            const personId = input.dataset.personId;
            input.value = (selectedAssignments[personId] && selectedAssignments[personId].instruction) || "";
        });
        updateSelectedDisplay();
    }

    function updateSelectedDisplay() {
        const selectedNames = peopleCheckboxes
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => checkbox.dataset.name);
        fields.donViDisplay.value = selectedNames.length ? selectedNames.join(", ") : "";
        fields.donViDisplay.placeholder = selectedNames.length ? "" : "Chua chon nguoi xu ly";
    }

    function syncSelectFromCheckboxes() {
        const selectedValues = new Set(
            peopleCheckboxes.filter((checkbox) => checkbox.checked).map((checkbox) => checkbox.value)
        );
        Array.from(fields.donVi.options).forEach((option) => {
            option.selected = selectedValues.has(option.value);
        });
        peopleCheckboxes.forEach((checkbox) => {
            if (!selectedAssignments[checkbox.value]) {
                selectedAssignments[checkbox.value] = {
                    id: checkbox.value,
                    name: checkbox.dataset.name,
                    instruction: "",
                    selected: checkbox.checked,
                };
            } else {
                selectedAssignments[checkbox.value].selected = checkbox.checked;
            }
        });
        updateSelectedDisplay();
    }

    function buildAssignmentPayload() {
        return peopleCheckboxes
            .filter((checkbox) => checkbox.checked)
            .map((checkbox) => {
                const assignment = selectedAssignments[checkbox.value] || {};
                return {
                    id: checkbox.value,
                    name: checkbox.dataset.name,
                    instruction: (assignment.instruction || "").trim(),
                };
            });
    }

    function openPeopleModal() {
        peopleSearchInput.value = "";
        peopleItems.forEach((item) => {
            item.classList.remove("hidden");
        });
        peopleModal.classList.add("show");
    }

    function closePeopleModal() {
        peopleModal.classList.remove("show");
    }

    function showPreview(fileName, fileUrl) {
        resetPreview();

        if (!fileUrl) {
            previewPlaceholder.textContent = "Van ban nay chua co file de xem truoc.";
            previewPlaceholder.classList.remove("hidden");
            return;
        }

        const lowerName = (fileName || "").toLowerCase();
        if (/\.(png|jpg|jpeg|gif|webp|bmp)$/.test(lowerName)) {
            previewImage.src = fileUrl;
            previewImage.classList.remove("hidden");
            return;
        }

        if (/\.(pdf)$/.test(lowerName)) {
            previewPdf.src = `${fileUrl}#toolbar=0`;
            previewPdf.classList.remove("hidden");
            return;
        }

        if (/\.(doc|docx)$/.test(lowerName) && window.mammoth) {
            fetch(fileUrl)
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("Khong the tai tep.");
                    }
                    return response.arrayBuffer();
                })
                .then((arrayBuffer) => window.mammoth.convertToHtml({ arrayBuffer: arrayBuffer }))
                .then((result) => {
                    previewWord.innerHTML = result.value || "<p>Khong co noi dung de hien thi.</p>";
                    previewWord.classList.remove("hidden");
                })
                .catch(() => {
                    previewMessage.textContent = `Khong the xem truoc tep ${fileName}.`;
                    previewMessage.classList.remove("hidden");
                });
            return;
        }

        previewMessage.textContent = `Khong ho tro preview truc tiep cho tep ${fileName}.`;
        previewMessage.classList.remove("hidden");
    }

    function populateModal(row) {
        fields.recordId.value = row.dataset.recordId || "";
        fields.loaiRecord.value = row.dataset.loai || "";
        fields.ngay.value = row.dataset.ngay || "";
        fields.soVanBan.value = row.dataset.soVanBan || "";
        fields.kyHieu.value = row.dataset.kyHieu || "";
        fields.loai.value = row.dataset.loaiVb || "";
        fields.coQuan.value = row.dataset.coQuan || "";
        fields.trichYeu.value = row.dataset.trichYeu || "";
        fields.file.value = row.dataset.fileName || "";
        fields.hanHoanThanh.value = row.dataset.thoiHan || "";
        setSelectedValues(row.dataset.assignedIds || "", row.dataset.assignmentDetails || "");

        if (row.dataset.fileUrl) {
            fields.fileLink.href = row.dataset.fileUrl;
            fields.fileLink.classList.remove("disabled");
        } else {
            fields.fileLink.href = "#";
            fields.fileLink.classList.add("disabled");
        }

        errorBox.textContent = "";
        updateSelectedDisplay();
    }

    function openAssignmentDetail(row) {
        if (!row) {
            return;
        }
        selectedRow = row;
        populateModal(row);
        detailModal.classList.add("show");
    }

    window.openAssignmentDetail = openAssignmentDetail;

    function updateRowAssignedState() {
        if (!selectedRow) {
            return;
        }

        const badge = selectedRow.querySelector(".status-badge");
        badge.textContent = "Da phan cong";
        badge.classList.add("assigned");
        if (window.applyStatusThemes) {
            window.applyStatusThemes();
        }
        selectedRow.dataset.thoiHan = fields.hanHoanThanh.value;
        selectedRow.dataset.assignedIds = Array.from(fields.donVi.selectedOptions)
            .map((option) => option.value)
            .join(",");
        selectedRow.dataset.assignmentDetails = JSON.stringify(buildAssignmentPayload());
    }

    function closeAllModals() {
        detailModal.classList.remove("show");
        confirmModal.classList.remove("show");
        peopleModal.classList.remove("show");
        previewModal.classList.remove("show");
        errorBox.textContent = "";
    }

    function ensureSearchEmptyState() {
        const rows = Array.from(tableBody.querySelectorAll("tr[data-record-id]"));
        const hasVisibleRows = rows.some((row) => !row.classList.contains("hidden"));
        let emptyRow = tableBody.querySelector('tr[data-search-empty="true"]');

        if (hasVisibleRows) {
            if (emptyRow) {
                emptyRow.remove();
            }
            return;
        }

        if (!emptyRow) {
            emptyRow = document.createElement("tr");
            emptyRow.dataset.searchEmpty = "true";
            emptyRow.innerHTML = '<td colspan="8" class="empty-state">Khong tim thay van ban phu hop.</td>';
            tableBody.appendChild(emptyRow);
        }
    }

    function filterAssignmentRows() {
        const keyword = ((searchInput && searchInput.value) || "").trim().toLowerCase();
        const rows = Array.from(tableBody.querySelectorAll("tr[data-record-id]"));

        rows.forEach((row) => {
            const haystack = [
                row.dataset.ngay,
                row.dataset.soVanBan,
                row.dataset.kyHieu,
                row.dataset.loaiVb,
                row.dataset.coQuan,
                row.dataset.trichYeu,
            ]
                .join(" ")
                .toLowerCase();

            row.classList.toggle("hidden", Boolean(keyword) && !haystack.includes(keyword));
        });

        ensureSearchEmptyState();
    }

    tableBody.addEventListener("click", function (event) {
        const row = event.target.closest("tr[data-record-id]");
        if (!row) {
            return;
        }

        openAssignmentDetail(row);
    });

    if (closeDetailButton) {
        closeDetailButton.addEventListener("click", closeAllModals);
    }
    if (closePeopleButton) {
        closePeopleButton.addEventListener("click", closePeopleModal);
    }
    if (closePreviewButton) {
        closePreviewButton.addEventListener("click", function () {
            previewModal.classList.remove("show");
        });
    }
    if (cancelConfirmButton) {
        cancelConfirmButton.addEventListener("click", function () {
            confirmModal.classList.remove("show");
        });
    }
    if (cancelPeopleButton) {
        cancelPeopleButton.addEventListener("click", closePeopleModal);
    }
    if (openPeopleButton) {
        openPeopleButton.addEventListener("click", openPeopleModal);
    }
    if (acceptPeopleButton) {
        acceptPeopleButton.addEventListener("click", function () {
            syncSelectFromCheckboxes();
            closePeopleModal();
        });
    }

    if (detailModal) {
        detailModal.addEventListener("click", function (event) {
            if (event.target === detailModal) {
                closeAllModals();
            }
        });
    }
    if (peopleModal) {
        peopleModal.addEventListener("click", function (event) {
            if (event.target === peopleModal) {
                closePeopleModal();
            }
        });
    }
    if (confirmModal) {
        confirmModal.addEventListener("click", function (event) {
            if (event.target === confirmModal) {
                confirmModal.classList.remove("show");
            }
        });
    }
    if (previewModal) {
        previewModal.addEventListener("click", function (event) {
            if (event.target === previewModal) {
                previewModal.classList.remove("show");
            }
        });
    }

    if (previewButton) {
        previewButton.addEventListener("click", function () {
            showPreview(fields.file.value, fields.fileLink.href !== "#" ? fields.fileLink.href : "");
            previewModal.classList.add("show");
        });
    }

    if (peopleSearchInput) {
        peopleSearchInput.addEventListener("input", function () {
            const keyword = this.value.trim().toLowerCase();
            peopleItems.forEach((item) => {
                const haystack = item.dataset.search || "";
                item.classList.toggle("hidden", Boolean(keyword) && !haystack.includes(keyword));
            });
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterAssignmentRows);
    }

    if (searchButton) {
        searchButton.addEventListener("click", filterAssignmentRows);
    }

        if (openConfirmButton) {
        openConfirmButton.addEventListener("click", function () {
            const assignmentPayload = buildAssignmentPayload();
            if (!assignmentPayload.length) {
                errorBox.textContent = "Vui long chon it nhat mot nguoi xu ly.";
                return;
            }
            if (assignmentPayload.some((item) => !item.instruction)) {
                errorBox.textContent = "Vui long nhap noi dung chi dao cho tung nguoi xu ly.";
                return;
            }
            if (!fields.hanHoanThanh.value) {
                errorBox.textContent = "Vui long chon thoi han xu ly.";
                return;
            }
            confirmModal.classList.add("show");
        });
    }

    if (acceptConfirmButton) {
        acceptConfirmButton.addEventListener("click", function () {
            const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]").value;
            const formData = new FormData();
            formData.append("loai", fields.loaiRecord.value);
            formData.append("record_id", fields.recordId.value);
            formData.append("assignment_payload", JSON.stringify(buildAssignmentPayload()));
            formData.append("thoi_han", fields.hanHoanThanh.value);

            fetch(page.dataset.saveUrl, {
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
                .then(() => {
                    updateRowAssignedState();
                    closeAllModals();
                })
                .catch((payload) => {
                    errorBox.textContent = (payload && payload.message) || "Khong the luu phan cong xu ly.";
                    confirmModal.classList.remove("show");
                });
        });
    }

    updateSelectedDisplay();
    ensureSearchEmptyState();

    peopleCheckboxes.forEach((checkbox) => {
        checkbox.addEventListener("change", function () {
            if (!selectedAssignments[checkbox.value]) {
                selectedAssignments[checkbox.value] = {
                    id: checkbox.value,
                    name: checkbox.dataset.name,
                    instruction: "",
                    selected: checkbox.checked,
                };
            } else {
                selectedAssignments[checkbox.value].selected = checkbox.checked;
            }
        });
    });

    peopleInstructionInputs.forEach((input) => {
        input.addEventListener("input", function () {
            const personId = input.dataset.personId;
            if (!selectedAssignments[personId]) {
                selectedAssignments[personId] = {
                    id: personId,
                    name: "",
                    instruction: input.value,
                    selected: false,
                };
            } else {
                selectedAssignments[personId].instruction = input.value;
            }
        });
    });
})();
