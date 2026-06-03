(function () {
    "use strict";

    const form   = document.getElementById("delete-account-form");
    const submit = document.getElementById("confirm-delete-btn");

    if (!form || !submit) return;

    form.addEventListener("submit", function () {
        submit.disabled    = true;
        submit.textContent = "Deleting...";
    });
})();
