(function () {
    "use strict";

    // ── Two-step archive confirm ───────────────────────────────
    //
    // Pattern (per UI_UX.md HCI spec for destructive actions):
    //   1st click  → reveal "Archive this listing? [Confirm] [Cancel]" inline
    //   2nd click  → submit the hidden archive form
    //   Cancel     → revert to the original "Archive" button
    //
    // Works via data-attributes on the trigger button:
    //   data-archive-trigger
    //   data-archive-form   (id of the form to submit on confirm)
    //   data-archive-label  (product title for the confirm message)

    document.querySelectorAll("[data-archive-trigger]").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.preventDefault();

            const row      = btn.closest("tr") || btn.closest("[data-archive-row]");
            const formId   = btn.dataset.archiveForm;
            const title    = btn.dataset.archiveLabel || "this listing";
            const form     = document.getElementById(formId);

            if (!form) return;

            // Hide trigger button
            btn.style.display = "none";

            // Build inline confirm group
            const group = document.createElement("span");
            group.className = "archive-confirm-group is-visible";
            group.setAttribute("aria-live", "polite");
            group.innerHTML = `
                <span class="confirm-label">Archive <em>${_escape(title)}</em>?</span>
                <button
                    type="button"
                    class="action-btn action-btn-danger"
                    id="archive-confirm-yes-${formId}"
                    aria-label="Confirm archive"
                >Yes, archive</button>
                <button
                    type="button"
                    class="action-btn"
                    id="archive-confirm-no-${formId}"
                    aria-label="Cancel archive"
                >Cancel</button>
            `;

            btn.insertAdjacentElement("afterend", group);

            group.querySelector(`#archive-confirm-yes-${formId}`)
                .addEventListener("click", function () {
                    form.submit();
                });

            group.querySelector(`#archive-confirm-no-${formId}`)
                .addEventListener("click", function () {
                    group.remove();
                    btn.style.display = "";
                });
        });
    });

    // ── Toggle loading state ───────────────────────────────────

    document.querySelectorAll("[data-toggle-form]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            btn.disabled    = true;
            btn.textContent = "...";
        });
    });

    // ── Search form auto-submit on select change ───────────────

    const filterForm = document.getElementById("filter-form");
    if (filterForm) {
        filterForm.querySelectorAll("select").forEach(function (sel) {
            sel.addEventListener("change", function () {
                filterForm.submit();
            });
        });
    }

    // ── Utility ───────────────────────────────────────────────

    function _escape(str) {
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }

})();
