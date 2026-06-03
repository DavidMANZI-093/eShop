(function () {
    "use strict";

    // ── Elements ───────────────────────────────────────────────

    const dropzone   = document.getElementById("image-dropzone");
    const fileInput  = document.getElementById("product-image-input");
    const preview    = document.getElementById("product-image-preview");
    const hiddenData = document.getElementById("imageData");
    const hint       = document.getElementById("image-upload-hint");
    const errorSpan  = document.getElementById("imageData-error");
    const MAX_BYTES  = 2 * 1024 * 1024; // 2 MB raw file limit

    // ── Image processing ───────────────────────────────────────

    function processFile(file) {
        if (!file) return;

        if (!file.type.startsWith("image/")) {
            showImageError("Only image files are accepted.");
            return;
        }

        if (file.size > MAX_BYTES) {
            showImageError("Image must be under 2 MB.");
            fileInput.value = "";
            return;
        }

        clearImageError();

        const reader = new FileReader();
        reader.onload = function (e) {
            const dataUrl = e.target.result;
            preview.src = dataUrl;
            preview.classList.add("has-image");
            hiddenData.value = dataUrl;
            dropzone.classList.remove("has-error");
            hint.innerHTML = "<span>Image selected \u2014 click or drag to replace</span>";
        };
        reader.readAsDataURL(file);
    }

    function showImageError(msg) {
        if (!errorSpan) return;
        errorSpan.textContent = msg;
        errorSpan.style.visibility = "visible";
        if (dropzone) dropzone.classList.add("has-error");
    }

    function clearImageError() {
        if (!errorSpan) return;
        errorSpan.style.visibility = "hidden";
        if (dropzone) dropzone.classList.remove("has-error");
    }

    // ── Click to browse ────────────────────────────────────────

    if (dropzone) {
        dropzone.addEventListener("click", function (e) {
            // Don't re-trigger if the click came from the file input itself
            if (e.target !== fileInput) {
                fileInput.click();
            }
        });

        dropzone.addEventListener("keydown", function (e) {
            if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                fileInput.click();
            }
        });
    }

    if (fileInput) {
        fileInput.addEventListener("change", function () {
            processFile(this.files[0]);
        });
    }

    // ── Drag and drop ──────────────────────────────────────────

    if (dropzone) {
        dropzone.addEventListener("dragenter", function (e) {
            e.preventDefault();
            dropzone.classList.add("drag-over");
        });

        dropzone.addEventListener("dragover", function (e) {
            e.preventDefault();
            dropzone.classList.add("drag-over");
        });

        dropzone.addEventListener("dragleave", function (e) {
            // Only remove class if leaving the dropzone entirely (not a child)
            if (!dropzone.contains(e.relatedTarget)) {
                dropzone.classList.remove("drag-over");
            }
        });

        dropzone.addEventListener("drop", function (e) {
            e.preventDefault();
            dropzone.classList.remove("drag-over");
            const file = e.dataTransfer.files[0];
            processFile(file);
        });
    }

    // Mark dropzone as errored if server returned an image error
    if (errorSpan && errorSpan.style.visibility !== "hidden") {
        if (dropzone) dropzone.classList.add("has-error");
    }

    // ── Description character counter ──────────────────────────

    const descInput = document.getElementById("description");
    const descCtr   = document.getElementById("desc-counter");
    const MAX_DESC  = 5000;

    function updateDescCounter() {
        if (!descInput || !descCtr) return;
        const len = descInput.value.length;
        descCtr.textContent = `${len} / ${MAX_DESC}`;
        descCtr.className = "char-counter";
        if (len >= MAX_DESC)              descCtr.classList.add("at-limit");
        else if (len >= MAX_DESC * 0.9)   descCtr.classList.add("near-limit");
    }

    if (descInput) {
        descInput.addEventListener("input", updateDescCounter);
        updateDescCounter();
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
        if (len >= MAX_TITLE)              titleCtr.classList.add("at-limit");
        else if (len >= MAX_TITLE * 0.85)  titleCtr.classList.add("near-limit");
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
    }

    // ── Form submit loading state ──────────────────────────────

    const form   = document.getElementById("product-form");
    const submit = document.getElementById("product-submit");

    if (form && submit) {
        form.addEventListener("submit", function () {
            // Small delay so any in-progress file read can finish
            setTimeout(function () {
                submit.disabled    = true;
                submit.textContent = "Saving\u2026";
            }, 80);
        });
    }

})();
