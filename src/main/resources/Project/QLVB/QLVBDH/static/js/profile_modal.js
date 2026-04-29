document.addEventListener("DOMContentLoaded", () => {
    const root = document.getElementById("personal-profile-root");
    const trigger = document.querySelector("[data-open-profile='true']");
    if (!root || !trigger) {
        return;
    }

    const profileModal = document.getElementById("personal-profile-modal");
    const passwordModal = document.getElementById("change-password-modal");
    const profileFeedback = document.getElementById("personal-profile-feedback");
    const passwordFeedback = document.getElementById("change-password-feedback");
    const headerName = document.getElementById("name");

    const fields = {
        maGv: document.getElementById("profile-ma-gv"),
        hoTen: document.getElementById("profile-ho-ten"),
        lastLogin: document.getElementById("profile-last-login"),
        groupDisplay: document.getElementById("profile-group-display"),
        oldPassword: document.getElementById("old-password"),
        newPassword: document.getElementById("new-password"),
        confirmNewPassword: document.getElementById("confirm-new-password"),
    };

    const buttons = {
        edit: document.getElementById("btn-edit-profile"),
        save: document.getElementById("btn-save-profile"),
        cancel: document.getElementById("btn-cancel-profile"),
        openPassword: document.getElementById("btn-open-change-password"),
        savePassword: document.getElementById("btn-save-password"),
    };

    let isEditing = false;
    let profileState = readProfileFromInputs();

    function readProfileFromInputs() {
        return {
            ma_gv: fields.maGv.value,
            ho_ten: fields.hoTen.value,
            lan_cuoi_dang_nhap: fields.lastLogin.value,
            nhom_quyen_display: fields.groupDisplay.value,
        };
    }

    function fillProfile(profile) {
        profileState = { ...profile };
        fields.maGv.value = profile.ma_gv || "";
        fields.hoTen.value = profile.ho_ten || "";
        fields.lastLogin.value = profile.lan_cuoi_dang_nhap || "";
        fields.groupDisplay.value = profile.nhom_quyen_display || "";
        if (headerName) {
            headerName.textContent = (profile.ho_ten || "").toUpperCase();
        }
    }

    function toggleFeedback(node, message, level) {
        if (!message) {
            node.textContent = "";
            node.classList.add("hidden");
            node.classList.remove("success", "error");
            return;
        }
        node.textContent = message;
        node.classList.remove("hidden", "success", "error");
        node.classList.add(level);
    }

    function toggleEditMode(editing) {
        isEditing = editing;
        fields.hoTen.readOnly = !editing;
        fields.hoTen.classList.toggle("profile-readonly", !editing);
        buttons.edit.classList.toggle("hidden", editing);
        buttons.save.classList.toggle("hidden", !editing);
        buttons.cancel.classList.toggle("hidden", !editing);
    }

    function openModal(modal) {
        modal.classList.remove("hidden");
    }

    function closeModal(modal) {
        modal.classList.add("hidden");
    }

    function resetPasswordForm() {
        fields.oldPassword.value = "";
        fields.newPassword.value = "";
        fields.confirmNewPassword.value = "";
        toggleFeedback(passwordFeedback, "", "");
    }

    async function saveProfile() {
        const formData = new FormData();
        formData.append("ho_ten", fields.hoTen.value.trim());

        try {
            const response = await fetch(root.dataset.updateUrl, {
                method: "POST",
                headers: { "X-CSRFToken": root.dataset.csrfToken },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                const errors = data.errors ? Object.values(data.errors).flat().join(" ") : data.message;
                toggleFeedback(profileFeedback, errors || "Khong the cap nhat thong tin ca nhan.", "error");
                return;
            }

            fillProfile(data.profile);
            toggleEditMode(false);
            toggleFeedback(profileFeedback, data.message, "success");
        } catch (error) {
            toggleFeedback(profileFeedback, "Khong the cap nhat thong tin ca nhan.", "error");
        }
    }

    async function changePassword() {
        const formData = new FormData();
        formData.append("mat_khau_cu", fields.oldPassword.value);
        formData.append("mat_khau_moi", fields.newPassword.value);
        formData.append("nhap_lai_mat_khau_moi", fields.confirmNewPassword.value);

        try {
            const response = await fetch(root.dataset.changePasswordUrl, {
                method: "POST",
                headers: { "X-CSRFToken": root.dataset.csrfToken },
                body: formData,
            });
            const data = await response.json();
            if (!response.ok || !data.success) {
                toggleFeedback(passwordFeedback, data.message || "Khong the doi mat khau.", "error");
                return;
            }

            resetPasswordForm();
            closeModal(passwordModal);
            toggleFeedback(profileFeedback, data.message, "success");
        } catch (error) {
            toggleFeedback(passwordFeedback, "Khong the doi mat khau.", "error");
        }
    }

    trigger.addEventListener("click", () => {
        toggleEditMode(false);
        toggleFeedback(profileFeedback, "", "");
        fillProfile(profileState);
        openModal(profileModal);
    });

    trigger.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            trigger.click();
        }
    });

    document.querySelectorAll("[data-close-profile]").forEach((button) => {
        button.addEventListener("click", () => {
            closeModal(document.getElementById(button.dataset.closeProfile));
        });
    });

    [profileModal, passwordModal].forEach((modal) => {
        modal.addEventListener("click", (event) => {
            if (event.target === modal) {
                closeModal(modal);
            }
        });
    });

    buttons.edit.addEventListener("click", () => {
        toggleFeedback(profileFeedback, "", "");
        toggleEditMode(true);
    });

    buttons.cancel.addEventListener("click", () => {
        fillProfile(profileState);
        toggleFeedback(profileFeedback, "", "");
        toggleEditMode(false);
    });

    buttons.save.addEventListener("click", saveProfile);
    buttons.openPassword.addEventListener("click", () => {
        resetPasswordForm();
        openModal(passwordModal);
    });
    buttons.savePassword.addEventListener("click", changePassword);
});
