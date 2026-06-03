(function () {
    "use strict";

    const fileInput = document.getElementById("avatar-file-input");
    const preview = document.getElementById("avatar-preview");
    const hiddenInput = document.getElementById("profile_base64");
    const infoForm = document.getElementById("profile-info-form");
    const infoSubmit = document.getElementById("profile-info-submit");
    const pwForm = document.getElementById("change-password-form");
    const pwSubmit = document.getElementById("change-password-submit");

    const MAX_BYTES = 15 * 1024 * 1024; // 2 MB

    // ── Avatar upload preview ───────────────────────────────────

    if (fileInput) {
        fileInput.addEventListener("change", function () {
            const file = this.files[0];
            if (!file) return;

            if (file.size > MAX_BYTES) {
                alert("Photo must be under 2 MB.");
                this.value = "";
                return;
            }

            const reader = new FileReader();
            reader.onload = function (e) {
                preview.src = e.target.result;
                hiddenInput.value = e.target.result;
            };
            reader.readAsDataURL(file);
        });
    }

    // ── Loading state on info form ──────────────────────────────

    if (infoForm && infoSubmit) {
        infoForm.addEventListener("submit", function () {
            infoSubmit.disabled = true;
            infoSubmit.textContent = "Saving...";
        });
    }

    // ── Password form: client-side match check ──────────────────

    if (pwForm && pwSubmit) {
        pwForm.addEventListener("submit", function (e) {
            const newPw = document.getElementById("new_password").value;
            const confPw = document.getElementById("confirm_password").value;
            const slot = document.getElementById("confirm_password-error");

            if (slot) slot.textContent = "";
            document.getElementById("confirm_password").classList.remove("has-error");

            if (newPw && confPw && newPw !== confPw) {
                e.preventDefault();
                document.getElementById("confirm_password").classList.add("has-error");
                if (slot) slot.textContent = "Passwords do not match.";
                return;
            }

            pwSubmit.disabled = true;
            pwSubmit.textContent = "Updating...";
        });
    }
})();
