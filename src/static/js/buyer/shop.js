(function () {
    "use strict";

    /* ── Shop page JS ─────────────────────────────────────────────
     *
     * Handles:
     *  – Category select auto-submit
     *  – Add-to-cart fetch + button state feedback
     *  – Sidebar badge count update
     */

    // Auto-submit filter form on category change
    var filterForm     = document.getElementById("shop-filter-form");
    var categorySelect = document.getElementById("shop-category-select");

    if (categorySelect && filterForm) {
        categorySelect.addEventListener("change", function () {
            filterForm.submit();
        });
    }

    // Add-to-cart fetch (progressive enhancement)
    document.addEventListener("click", function (e) {
        var btn = e.target.closest(".btn-add-cart[data-product-id]");
        if (!btn) return;

        e.preventDefault();

        var productId = btn.dataset.productId;
        if (!productId || btn.classList.contains("is-loading")) return;

        var originalText = btn.innerHTML;
        btn.classList.add("is-loading");
        btn.innerHTML = "Adding\u2026";

        fetch("/buyer/cart/add", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: "product_id=" + encodeURIComponent(productId) + "&quantity=1",
        })
        .then(function (r) { return r.json(); })
        .then(function (data) {
            btn.classList.remove("is-loading");
            if (data.ok) {
                btn.classList.add("is-added");
                btn.innerHTML = "Added!";
                // Update sidebar badge
                document.querySelectorAll(".cart-badge").forEach(function (el) {
                    el.textContent = data.cart_count;
                    el.dataset.count = data.cart_count;
                });
                setTimeout(function () {
                    btn.classList.remove("is-added");
                    btn.innerHTML = originalText;
                }, 1800);
            } else {
                btn.innerHTML = originalText;
                // Server returned an error (e.g., not verified)
                if (data.error) {
                    // Redirect to dashboard so the flash message shows
                    window.location.href = "/buyer/cart/add";
                }
            }
        })
        .catch(function () {
            btn.classList.remove("is-loading");
            btn.innerHTML = originalText;
        });
    });

})();
