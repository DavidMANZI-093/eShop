(function () {
    "use strict";

    const form   = document.getElementById("login-form");
    const submit = document.getElementById("login-submit");

    form.addEventListener("submit", function (e) {
        const user_name = form.user_name.value.trim();
        const password  = form.password.value;

        const errors = {};

        if (!user_name) errors.user_name = "Username is required.";
        if (!password)  errors.password  = "Password is required.";

        if (Object.keys(errors).length) {
            e.preventDefault();
            renderErrors(errors);
            focusFirstError(errors);
            return;
        }

        setLoading(true);
    });

    function renderErrors(errors) {
        clearErrors();
        for (const field in errors) {
            const input = form.elements[field];
            const slot  = document.getElementById(field + "-error");
            if (input)  input.classList.add("has-error");
            if (slot)   slot.textContent = errors[field];
        }
    }

    function clearErrors() {
        form.querySelectorAll(".field-input").forEach(function (el) {
            el.classList.remove("has-error");
        });
        form.querySelectorAll(".field-error-message").forEach(function (el) {
            el.textContent = "";
        });
    }

    function focusFirstError(errors) {
        const firstField = Object.keys(errors)[0];
        const input = form.elements[firstField];
        if (input) input.focus();
    }

    function setLoading(on) {
        submit.classList.toggle("is-loading", on);
        submit.disabled = on;
        submit.textContent = on ? "Signing in..." : "Sign in";
    }
})();
