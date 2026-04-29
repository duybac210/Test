(function () {
    const notificationOverlay = document.getElementById("notification-overlay");
    const notificationMessage = document.getElementById("notification-message");
    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");
    const tableBody = document.getElementById("personal-table-body");

    if (!tableBody) {
        return;
    }

    function showNotification(message) {
        if (!notificationOverlay || !notificationMessage) {
            return;
        }
        notificationMessage.textContent = message;
        notificationOverlay.classList.remove("hidden");
        window.setTimeout(function () {
            notificationOverlay.classList.add("hidden");
        }, 1600);
    }

    function filterRows() {
        const keyword = ((searchInput && searchInput.value) || "").trim().toLowerCase();
        const rows = Array.from(tableBody.querySelectorAll("tr[data-record-id], tr[data-assignment-id]"));
        rows.forEach(function (row) {
            const haystack = [
                row.dataset.soVanBan,
                row.dataset.loaiVb,
                row.dataset.soKyHieu,
                row.dataset.trichYeu,
                row.dataset.nguoiPhanCong,
                row.dataset.nguoiYeuCau,
            ]
                .join(" ")
                .toLowerCase();
            row.classList.toggle("hidden", Boolean(keyword) && !haystack.includes(keyword));
        });
    }

    if (searchInput) {
        searchInput.addEventListener("input", filterRows);
    }
    if (searchButton) {
        searchButton.addEventListener("click", filterRows);
    }

    const processingPage = document.querySelector(".personal-work-page");
    if (processingPage) {
        const modal = document.getElementById("personal-modal");
        const closeButton = document.getElementById("close-personal-modal");
        const form = document.getElementById("personal-form");
        const errorBox = document.getElementById("personal-form-errors");
        const updateButton = document.getElementById("btn-update-progress");
        const transferButton = document.getElementById("btn-transfer-assignment");
        let activeRow = null;

        function buildUrl(template, value) {
            return template.replace("__assignment_id__", value);
        }

        function populateModal(row) {
            document.getElementById("p-assignment-id").value = row.dataset.assignmentId || "";
            document.getElementById("p-so-van-ban").value = row.dataset.soVanBan || "";
            document.getElementById("p-ngay-ban-hanh").value = row.dataset.ngayBanHanh || "";
            document.getElementById("p-loai-vb").value = row.dataset.loaiVb || "";
            document.getElementById("p-so-ky-hieu").value = row.dataset.soKyHieu || "";
            document.getElementById("p-trich-yeu").value = row.dataset.trichYeu || "";
            document.getElementById("p-co-quan").value = row.dataset.coQuanBanHanh || "";
            document.getElementById("p-nguoi-phan-cong").value = row.dataset.nguoiPhanCong || "";
            document.getElementById("p-noi-dung-cd").value = row.dataset.noiDungCd || "";
            document.getElementById("p-thoi-han").value = row.dataset.thoiHan || "";
            document.getElementById("p-trang-thai-xu-ly").value =
                row.dataset.trangThaiXuLy === "Da hoan thanh" ? "Da hoan thanh" : "Dang xu ly";

            const fileLink = document.getElementById("p-file-link");
            const fileName = document.getElementById("p-file-name");
            fileName.value = row.dataset.fileName || "";
            if (row.dataset.fileUrl) {
                fileLink.href = row.dataset.fileUrl;
                fileLink.classList.remove("disabled");
            } else {
                fileLink.href = "#";
                fileLink.classList.add("disabled");
            }
            errorBox.textContent = "";
        }

        function closeModal() {
            modal.classList.remove("show");
            activeRow = null;
        }

        tableBody.addEventListener("click", function (event) {
            const row = event.target.closest("tr[data-assignment-id]");
            if (!row) {
                return;
            }
            activeRow = row;
            populateModal(row);
            modal.classList.add("show");
        });

        closeButton.addEventListener("click", closeModal);
        modal.addEventListener("click", function (event) {
            if (event.target === modal) {
                closeModal();
            }
        });

        updateButton.addEventListener("click", function () {
            if (!activeRow) {
                return;
            }
            const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
            const formData = new FormData();
            formData.append("trang_thai_xl", document.getElementById("p-trang-thai-xu-ly").value);
            fetch(buildUrl(processingPage.dataset.updateUrlTemplate, document.getElementById("p-assignment-id").value), {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
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
                    activeRow.dataset.trangThaiXuLy = payload.trang_thai_xl;
                    const badge = activeRow.querySelector(".status-badge");
                    if (badge) {
                        badge.textContent = payload.trang_thai_xl;
                    }
                    if (window.applyStatusThemes) {
                        window.applyStatusThemes();
                    }
                    showNotification(payload.message || "Da cap nhat tien do.");
                    closeModal();
                })
                .catch(function (payload) {
                    errorBox.textContent = (payload && payload.message) || "Khong the cap nhat tien do.";
                });
        });

        if (transferButton) {
            transferButton.addEventListener("click", function () {
                if (!activeRow) {
                    return;
                }
                const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
                fetch(buildUrl(processingPage.dataset.transferUrlTemplate, document.getElementById("p-assignment-id").value), {
                    method: "POST",
                    headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
                })
                    .then(async function (response) {
                        const payload = await response.json();
                        if (!response.ok) {
                            throw payload;
                        }
                        return payload;
                    })
                    .then(function (payload) {
                        activeRow.dataset.trangThaiXuLy = "Cho xu ly";
                        const badge = activeRow.querySelector(".status-badge");
                        if (badge) {
                            badge.textContent = "Cho xu ly";
                        }
                        if (window.applyStatusThemes) {
                            window.applyStatusThemes();
                        }
                        showNotification(payload.message || "Da chuyen phan cong.");
                        closeModal();
                    })
                    .catch(function (payload) {
                        errorBox.textContent = (payload && payload.message) || "Khong the chuyen phan cong.";
                    });
            });
        }
        return;
    }

    const returnedPage = document.querySelector(".returned-work-page");
    if (!returnedPage) {
        return;
    }

    const modal = document.getElementById("returned-modal");
    const closeButton = document.getElementById("close-returned-modal");
    const form = document.getElementById("returned-form");
    const errorBox = document.getElementById("returned-form-errors");
    const completeButton = document.getElementById("btn-complete-revision");
    const uploadInput = document.getElementById("r-file-upload");
    const fileNameField = document.getElementById("r-file-name");
    let activeRow = null;

    function buildCompleteUrl(documentId) {
        return returnedPage.dataset.completeUrlTemplate.replace("__document_id__", documentId);
    }

    function populateReturnedModal(row) {
        document.getElementById("r-record-id").value = row.dataset.recordId || "";
        document.getElementById("r-so-van-ban").value = row.dataset.soVanBan || "";
        document.getElementById("r-ngay-ban-hanh").value = row.dataset.ngayBanHanh || "";
        document.getElementById("r-loai-vb").value = row.dataset.maLoaiVb || "";
        document.getElementById("r-so-ky-hieu").value = row.dataset.soKyHieu || "";
        document.getElementById("r-trich-yeu").value = row.dataset.trichYeu || "";
        document.getElementById("r-nguoi-yeu-cau").value = row.dataset.nguoiYeuCau || "";
        document.getElementById("r-noi-dung-yeu-cau").value = row.dataset.noiDungYeuCau || "";
        document.getElementById("r-trang-thai").value = row.dataset.trangThai || "";
        uploadInput.value = "";
        fileNameField.value = "Khong bat buoc tai lai tep";
        errorBox.textContent = "";
    }

    function closeReturnedModal() {
        modal.classList.remove("show");
        activeRow = null;
    }

    tableBody.addEventListener("click", function (event) {
        const row = event.target.closest("tr[data-record-id]");
        if (!row) {
            return;
        }
        activeRow = row;
        populateReturnedModal(row);
        modal.classList.add("show");
    });

    closeButton.addEventListener("click", closeReturnedModal);
    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeReturnedModal();
        }
    });

    uploadInput.addEventListener("change", function () {
        const file = uploadInput.files && uploadInput.files[0];
        fileNameField.value = file ? file.name : "";
    });

    completeButton.addEventListener("click", function () {
        if (!activeRow) {
            return;
        }
        if (document.activeElement && typeof document.activeElement.blur === "function") {
            document.activeElement.blur();
        }

        window.setTimeout(function () {
            const file = uploadInput.files && uploadInput.files[0];
            const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
            const trichYeuField = document.getElementById("r-trich-yeu");
            const loaiVanBanField = document.getElementById("r-loai-vb");
            const trichYeu = (trichYeuField.value || "").trim();
            const maLoaiVb = (loaiVanBanField.value || "").trim();
            const formData = new FormData(form);

            formData.set("trich_yeu", trichYeu);
            formData.set("ma_loai_vb", maLoaiVb);

            if (!trichYeu) {
                errorBox.textContent = "Vui long nhap trich yeu van ban.";
                return;
            }
            if (!maLoaiVb) {
                errorBox.textContent = "Vui long chon loai van ban.";
                return;
            }
            if (!file) {
                formData.delete("ban_du_thao");
            }
            fetch(buildCompleteUrl(document.getElementById("r-record-id").value), {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken, "X-Requested-With": "XMLHttpRequest" },
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
                    closeReturnedModal();
                })
                .catch(function (payload) {
                    errorBox.textContent = (payload && payload.message) || "Khong the hoan thanh chinh sua.";
                });
        }, 0);
    });
})();
