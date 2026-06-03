(function () {
    "use strict";

    const form   = document.getElementById("forgot-password-form");
    const submit = document.getElementById("forgot-submit");
    const emailInput = document.getElementById("email");
    const emailError = document.getElementById("email-error");

    form.addEventListener("submit", function (e) {
        emailError.textContent = "";
        emailInput.classList.remove("has-error");

        const email = emailInput.value.trim();
        if (!email) {
            e.preventDefault();
            emailInput.classList.add("has-error");
            emailError.textContent = "Email address is required.";
            emailInput.focus();
            return;
        }

        submit.classList.add("is-loading");
        submit.disabled = true;
        submit.textContent = "Sending...";
    });
})();
