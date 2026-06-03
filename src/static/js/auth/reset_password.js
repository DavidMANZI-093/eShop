(function () {
    "use strict";

    const form    = document.getElementById("reset-password-form");
    const submit  = document.getElementById("reset-submit");
    const pwInput = document.getElementById("password");
    const cfInput = document.getElementById("password_confirm");

    const MIN_LENGTH = 8;

    form.addEventListener("submit", function (e) {
        clearErrors();

        const password = pwInput.value;
        const confirm  = cfInput.value;
        const errors   = {};

        const strengthError = validateStrength(password);
        if (strengthError) {
            errors.password = strengthError;
        }

        if (!confirm) {
            errors.password_confirm = "Please confirm your password.";
        } else if (password && password !== confirm) {
            errors.password_confirm = "Passwords do not match.";
        }

        if (Object.keys(errors).length) {
            e.preventDefault();
            renderErrors(errors);
            return;
        }

        submit.classList.add("is-loading");
        submit.disabled = true;
        submit.textContent = "Saving...";
    });

    function validateStrength(password) {
        if (!password)                           return "Password is required.";
        if (password.length < MIN_LENGTH)        return `Password must be at least ${MIN_LENGTH} characters.`;
        if (!/[A-Z]/.test(password))             return "Password must contain at least one uppercase letter.";
        if (!/[a-z]/.test(password))             return "Password must contain at least one lowercase letter.";
        if (!/[0-9]/.test(password))             return "Password must contain at least one digit.";
        if (!/[^A-Za-z0-9]/.test(password))      return "Password must contain at least one special character.";
        return null;
    }

    function renderErrors(errors) {
        for (const field in errors) {
            const input = form.elements[field];
            const slot  = document.getElementById(field + "-error");
            if (input) { input.classList.add("has-error"); input.setAttribute("aria-invalid", "true"); }
            if (slot)  slot.textContent = errors[field];
        }
        const firstField = Object.keys(errors)[0];
        if (form.elements[firstField]) form.elements[firstField].focus();
    }

    function clearErrors() {
        [pwInput, cfInput].forEach(function (el) {
            el.classList.remove("has-error");
            el.setAttribute("aria-invalid", "false");
        });
        form.querySelectorAll(".field-error-message").forEach(function (el) {
            el.textContent = "";
        });
    }
})();
