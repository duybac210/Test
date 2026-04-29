(function () {
    const page = document.querySelector(".progress-page");
    const tableBody = document.getElementById("progress-table-body");
    const modal = document.getElementById("progress-detail-modal");
    const closeButton = document.getElementById("close-progress-detail-modal");
    const detailBody = document.getElementById("progress-detail-body");
    const searchInput = document.getElementById("search-input");
    const searchButton = document.getElementById("search-button");

    if (!page || !tableBody || !modal || !detailBody) {
        return;
    }

    const fields = {
        ngayBanHanh: document.getElementById("d-ngay-ban-hanh"),
        soVanBan: document.getElementById("d-so-van-ban"),
        loaiVanBan: document.getElementById("d-loai-van-ban"),
        soKyHieu: document.getElementById("d-so-ky-hieu"),
        trichYeu: document.getElementById("d-trich-yeu"),
        coQuanBanHanh: document.getElementById("d-co-quan-ban-hanh"),
        trangThai: document.getElementById("d-trang-thai"),
    };

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
            emptyRow.innerHTML = '<td colspan="9" class="empty-state">Khong tim thay van ban phu hop.</td>';
            tableBody.appendChild(emptyRow);
        }
    }

    function filterRows() {
        const keyword = ((searchInput && searchInput.value) || "").trim().toLowerCase();
        const rows = Array.from(tableBody.querySelectorAll("tr[data-record-id]"));

        rows.forEach((row) => {
            const haystack = [
                row.dataset.ngayBanHanh,
                row.dataset.soVanBan,
                row.dataset.loaiVanBan,
                row.dataset.soKyHieu,
                row.dataset.trichYeu,
                row.dataset.coQuanBanHanh,
                row.dataset.nguoiXuLy,
                row.dataset.trangThai,
            ]
                .join(" ")
                .toLowerCase();

            row.classList.toggle("hidden", Boolean(keyword) && !haystack.includes(keyword));
        });

        ensureSearchEmptyState();
    }

    function renderDetails(details) {
        if (!Array.isArray(details) || !details.length) {
            detailBody.innerHTML = '<tr><td colspan="5" class="empty-state">Chua co chi tiet tien do.</td></tr>';
            return;
        }

        detailBody.innerHTML = details
            .map((detail) => {
                return `
                    <tr>
                        <td>${detail.nguoi_xu_ly || ""}</td>
                        <td class="text-center"><span class="status-badge ${detail.status_class || ""}">${detail.trang_thai || ""}</span></td>
                        <td>${detail.noi_dung_cd || ""}</td>
                        <td>${detail.thoi_han || ""}</td>
                        <td>${detail.thoi_gian_phan_cong || ""}</td>
                    </tr>
                `;
            })
            .join("");
    }

    function openDetail(row) {
        fields.ngayBanHanh.value = row.dataset.ngayBanHanh || "";
        fields.soVanBan.value = row.dataset.soVanBan || "";
        fields.loaiVanBan.value = row.dataset.loaiVanBan || "";
        fields.soKyHieu.value = row.dataset.soKyHieu || "";
        fields.trichYeu.value = row.dataset.trichYeu || "";
        fields.coQuanBanHanh.value = row.dataset.coQuanBanHanh || "";
        fields.trangThai.value = row.dataset.trangThai || "";
        detailBody.innerHTML = '<tr><td colspan="5" class="empty-state">Dang tai chi tiet xu ly...</td></tr>';
        modal.classList.add("show");

        const queryString = new URLSearchParams({
            loai: row.dataset.loai || "",
            record_id: row.dataset.recordId || "",
        });

        fetch(`${page.dataset.detailUrl}?${queryString.toString()}`, {
            headers: {
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
                renderDetails(payload.details || []);
            })
            .catch((payload) => {
                detailBody.innerHTML = `
                    <tr>
                        <td colspan="5" class="empty-state">${(payload && payload.message) || "Khong tai duoc chi tiet xu ly."}</td>
                    </tr>
                `;
            });
    }

    function closeDetail() {
        modal.classList.remove("show");
    }

    tableBody.addEventListener("click", function (event) {
        const row = event.target.closest("tr[data-record-id]");
        if (!row) {
            return;
        }
        openDetail(row);
    });

    if (closeButton) {
        closeButton.addEventListener("click", closeDetail);
    }

    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            closeDetail();
        }
    });

    if (searchInput) {
        searchInput.addEventListener("input", filterRows);
    }

    if (searchButton) {
        searchButton.addEventListener("click", filterRows);
    }

    ensureSearchEmptyState();
})();
