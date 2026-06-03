(function () {
    "use strict";

    // ── Image upload / preview ─────────────────────────────────

    const fileInput    = document.getElementById("product-image-input");
    const preview      = document.getElementById("product-image-preview");
    const hiddenData   = document.getElementById("imageData");
    const MAX_BYTES    = 2 * 1024 * 1024;

    if (fileInput && preview) {
        fileInput.addEventListener("change", function () {
            const file = this.files[0];
            if (!file) return;

            if (file.size > MAX_BYTES) {
                alert("Image must be under 2 MB.");
                this.value = "";
                return;
            }

            const reader = new FileReader();
            reader.onload = function (e) {
                preview.src = e.target.result;
                preview.classList.add("has-image");
                hiddenData.value = e.target.result;
            };
            reader.readAsDataURL(file);
        });

        // Click on preview also triggers file picker
        preview.addEventListener("click", () => fileInput.click());
    }

    // ── Description character counter ──────────────────────────

    const descInput = document.getElementById("description");
    const counter   = document.getElementById("desc-counter");
    const MAX_DESC  = 5000;

    function updateCounter() {
        if (!descInput || !counter) return;
        const len = descInput.value.length;
        counter.textContent = `${len} / ${MAX_DESC}`;
        counter.className = "char-counter";
        if (len >= MAX_DESC)          counter.classList.add("at-limit");
        else if (len >= MAX_DESC * 0.9) counter.classList.add("near-limit");
    }

    if (descInput) {
        descInput.addEventListener("input", updateCounter);
        updateCounter();
    }

    // ── Title character counter ────────────────────────────────

    const titleInput = document.getElementById("title");
    const titleCtr   = document.getElementById("title-counter");
    const MAX_TITLE  = 128;

    function updateTitleCounter() {
        if (!titleInput || !titleCtr) return;
        const len = titleInput.value.length;
        titleCtr.textContent = `${len} / ${MAX_TITLE}`;
        titleCtr.className = "char-counter";
        if (len >= MAX_TITLE)            titleCtr.classList.add("at-limit");
        else if (len >= MAX_TITLE * 0.85) titleCtr.classList.add("near-limit");
    }

    if (titleInput) {
        titleInput.addEventListener("input", updateTitleCounter);
        updateTitleCounter();
    }

    // ── Price: restrict to 2 decimal places ───────────────────

    const priceInput = document.getElementById("price");

    if (priceInput) {
        priceInput.addEventListener("blur", function () {
            const val = parseFloat(this.value);
            if (!isNaN(val) && val >= 0) {
                this.value = val.toFixed(2);
            }
        });

        priceInput.addEventListener("keypress", function (e) {
            const char  = String.fromCharCode(e.which);
            const value = this.value;
            const dot   = value.indexOf(".");
            // Block anything non-numeric except one decimal point
            if (!/[\d.]/.test(char)) { e.preventDefault(); return; }
            if (char === "." && dot !== -1) { e.preventDefault(); return; }
            // Block >2 decimal places
            if (dot !== -1 && value.length - dot > 2) { e.preventDefault(); }
        });
    }

    // ── Form loading state ─────────────────────────────────────

    const form   = document.getElementById("product-form");
    const submit = document.getElementById("product-submit");

    if (form && submit) {
        form.addEventListener("submit", function () {
            submit.disabled    = true;
            submit.textContent = "Saving...";
        });
    }

})();
