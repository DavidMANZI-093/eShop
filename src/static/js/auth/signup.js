(function () {
    "use strict";

    const form          = document.getElementById("signup-form");
    const submit        = document.getElementById("signup-submit");
    const profileInput  = document.getElementById("profile");
    const profileBase64 = document.getElementById("profile_base64");
    const profilePreview = document.getElementById("profile-preview");

    const MAX_FILE_BYTES = 15 * 1024 * 1024;
    const MIN_PASSWORD_LENGTH = 8;

    // ── Profile image handling ──────────────────────────────────
    profileInput.addEventListener("change", function () {
        const file = this.files[0];

        if (!file) {
            profileBase64.value = "";
            return;
        }

        if (file.size > MAX_FILE_BYTES) {
            const mb = (file.size / (1024 * 1024)).toFixed(1);
            setFieldError("profile", "Image is too large (" + mb + " MB). Maximum is 15 MB.");
            this.value = "";
            profileBase64.value = "";
            return;
        }

        clearFieldError("profile");

        const reader = new FileReader();
        reader.onload = function (e) {
            profileBase64.value = e.target.result;
            profilePreview.src  = e.target.result;
        };
        reader.readAsDataURL(file);
    });

    // ── Form submission ─────────────────────────────────────────
    form.addEventListener("submit", function (e) {
        clearAllErrors();

        const errors = validateForm();

        if (Object.keys(errors).length) {
            e.preventDefault();
            renderErrors(errors);
            focusFirstError(errors);
            return;
        }

        setLoading(true);
    });

    function validateForm() {
        const errors = {};

        const fullName        = (form.full_name.value       || "").trim();
        const userName        = (form.user_name.value       || "").trim();
        const email           = (form.user_email.value      || "").trim();
        const password        = form.password.value         || "";
        const passwordConfirm = form.password_confirm.value || "";
        const roleInput       = form.querySelector('input[name="user_role"]:checked');

        if (!fullName) {
            errors.full_name = "Full name is required.";
        } else if (fullName.length > 64) {
            errors.full_name = "Full name must be 64 characters or less.";
        }

        if (!userName) {
            errors.user_name = "Username is required.";
        } else if (userName.length > 24) {
            errors.user_name = "Username must be 24 characters or less.";
        } else if (!/^[A-Za-z0-9_.\-]+$/.test(userName)) {
            errors.user_name = "Username may only contain letters, numbers, underscores, dots, and hyphens.";
        }

        if (!email) {
            errors.user_email = "Email is required.";
        } else if (!email.includes("@") || !email.split("@")[1]?.includes(".")) {
            errors.user_email = "Enter a valid email address.";
        }

        if (!password) {
            errors.password = "Password is required.";
        } else {
            const passwordError = validatePasswordStrength(password);
            if (passwordError) errors.password = passwordError;
        }

        if (!passwordConfirm) {
            errors.password_confirm = "Please confirm your password.";
        } else if (password && password !== passwordConfirm) {
            errors.password_confirm = "Passwords do not match.";
        }

        if (!roleInput) {
            errors.user_role = "Select a role to continue.";
        }

        return errors;
    }

    function validatePasswordStrength(password) {
        if (password.length < MIN_PASSWORD_LENGTH) {
            return "Password must be at least " + MIN_PASSWORD_LENGTH + " characters.";
        }
        if (!/[A-Z]/.test(password)) {
            return "Password must contain at least one uppercase letter.";
        }
        if (!/[a-z]/.test(password)) {
            return "Password must contain at least one lowercase letter.";
        }
        if (!/[0-9]/.test(password)) {
            return "Password must contain at least one digit.";
        }
        if (!/[^A-Za-z0-9]/.test(password)) {
            return "Password must contain at least one special character.";
        }
        return null;
    }

    // ── Error rendering ─────────────────────────────────────────
    function renderErrors(errors) {
        for (const field in errors) {
            setFieldError(field, errors[field]);
        }
    }

    function setFieldError(field, message) {
        const input = form.elements[field];
        const slot  = document.getElementById(field + "-error");

        if (input && input.type !== "radio" && input.type !== "file") {
            input.classList.add("has-error");
            input.setAttribute("aria-invalid", "true");
        }

        if (field === "user_role") {
            form.querySelectorAll('.role-option-label').forEach(function (el) {
                el.classList.add("has-error");
            });
        }

        if (slot) slot.textContent = message;
    }

    function clearFieldError(field) {
        const input = form.elements[field];
        const slot  = document.getElementById(field + "-error");
        if (input) {
            input.classList.remove("has-error");
            input.setAttribute("aria-invalid", "false");
        }
        if (slot) slot.textContent = "";
    }

    function clearAllErrors() {
        form.querySelectorAll(".field-input").forEach(function (el) {
            el.classList.remove("has-error");
            el.setAttribute("aria-invalid", "false");
        });
        form.querySelectorAll(".role-option-label").forEach(function (el) {
            el.classList.remove("has-error");
        });
        form.querySelectorAll(".field-error-message").forEach(function (el) {
            el.textContent = "";
        });
    }

    function focusFirstError(errors) {
        const firstField = Object.keys(errors)[0];
        const input = firstField === "user_role"
            ? form.querySelector('input[name="user_role"]')
            : form.elements[firstField];
        if (input) input.focus();
    }

    function setLoading(on) {
        submit.classList.toggle("is-loading", on);
        submit.disabled = on;
        submit.textContent = on ? "Creating account..." : "Create account";
    }
})();
