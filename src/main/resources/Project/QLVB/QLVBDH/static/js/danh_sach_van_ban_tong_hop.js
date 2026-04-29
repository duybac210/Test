(function () {
    const page = document.querySelector(".document-catalog-page");
    const tableBody = document.getElementById("catalog-table-body");
    const modal = document.getElementById("catalog-modal");
    const closeButton = document.getElementById("close-catalog-modal");
    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");

    if (!page || !tableBody || !modal) {
        return;
    }

    function filterRows() {
        const keyword = ((searchInput && searchInput.value) || "").trim().toLowerCase();
        const rows = tableBody.querySelectorAll("tr[data-record-id]");
        rows.forEach(function (row) {
            const haystack = [
                row.dataset.soVanBan,
                row.dataset.loaiVb,
                row.dataset.soKyHieu,
                row.dataset.trichYeu,
                row.dataset.nguon,
                row.dataset.trangThai,
            ]
                .join(" ")
                .toLowerCase();
            row.classList.toggle("hidden", Boolean(keyword) && !haystack.includes(keyword));
        });
    }

    function syncFileLink(fileName, fileUrl) {
        const link = document.getElementById("c-file-link");
        const field = document.getElementById("c-file-name");
        field.value = fileName || "";
        if (fileUrl) {
            link.href = fileUrl;
            link.classList.remove("disabled");
        } else {
            link.href = "#";
            link.classList.add("disabled");
        }
    }

    function openModal(row) {
        document.getElementById("c-so-van-ban").value = row.dataset.soVanBan || "";
        document.getElementById("c-ngay-ban-hanh").value = row.dataset.ngayBanHanh || "";
        document.getElementById("c-loai-vb").value = row.dataset.loaiVb || "";
        document.getElementById("c-so-ky-hieu").value = row.dataset.soKyHieu || "";
        document.getElementById("c-trich-yeu").value = row.dataset.trichYeu || "";
        document.getElementById("c-nguon").value = row.dataset.nguon || "";
        document.getElementById("c-trang-thai").value = row.dataset.trangThai || "";
        document.getElementById("c-co-quan-ban-hanh").value = row.dataset.coQuanBanHanh || "";
        syncFileLink(row.dataset.fileName || "", row.dataset.fileUrl || "");

        const editLink = document.getElementById("c-edit-link");
        if (editLink) {
            if (page.dataset.canEdit === "1" && row.dataset.editUrl) {
                editLink.href = row.dataset.editUrl;
                editLink.classList.remove("hidden");
            } else {
                editLink.href = "#";
                editLink.classList.add("hidden");
            }
        }
        modal.classList.add("show");
    }

    function closeModal() {
        modal.classList.remove("show");
    }

    tableBody.addEventListener("click", function (event) {
        const row = event.target.closest("tr[data-record-id]");
        if (!row) {
            return;
        }
        openModal(row);
    });

    closeButton.addEventListener("click", closeModal);
    modal.addEventListener("click", function (event) {
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
