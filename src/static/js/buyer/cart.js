(function () {
    "use strict";

    /* ── Cart page JS ────────────────────────────────────────────
     *
     * Handles:
     *  – Quantity +/− steppers (fetch → update DOM, no full reload)
     *  – Remove item button (fetch → remove row from DOM)
     *  – Two-step "Clear cart" confirm (inline, no modal)
     *  – Sidebar badge count update after every mutation
     */

    const CART_UPDATE_URL = "/buyer/cart/update";
    const CART_REMOVE_URL = "/buyer/cart/remove";
    const CART_CLEAR_URL  = "/buyer/cart/clear";

    // ── Utilities ───────────────────────────────────────────────

    function fmt(value) {
        return "R " + parseFloat(value).toFixed(2);
    }

    function updateBadge(count) {
        document.querySelectorAll(".cart-badge").forEach(function (el) {
            el.textContent = count;
            el.dataset.count = count;
        });
    }

    function updateCartTotal(total) {
        var el = document.getElementById("cart-total-value");
        if (el) el.textContent = fmt(total);
        var summary = document.getElementById("cart-summary-total-val");
        if (summary) summary.textContent = fmt(total);
    }

    function post(url, body, callback) {
        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: new URLSearchParams(body).toString(),
        })
        .then(function (r) { return r.json(); })
        .then(callback)
        .catch(function () {
            // Silent fail — let the user retry
        });
    }

    // ── Quantity stepper ────────────────────────────────────────

    document.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-cart-action]");
        if (!btn) return;

        var action    = btn.dataset.cartAction;
        var row       = btn.closest(".cart-item");
        var productId = row ? row.dataset.productId : null;

        if (!productId) return;

        // ── Decrease ─────────────────────────────────
        if (action === "decrease") {
            var qtyEl = row.querySelector(".cart-qty-value");
            var qty   = parseInt(qtyEl.textContent, 10);
            var newQty = qty - 1;

            if (newQty <= 0) {
                // Treat as remove
                removeRow(row, productId);
                return;
            }

            btn.disabled = true;
            post(CART_UPDATE_URL, { product_id: productId, quantity: newQty },
                function (data) {
                    btn.disabled = false;
                    if (!data.ok) return;
                    qtyEl.textContent = data.quantity;
                    var lineTotalEl = row.querySelector(".cart-item-line-total");
                    if (lineTotalEl) lineTotalEl.textContent = fmt(data.line_total);
                    updateCartTotal(data.cart_total);
                    updateBadge(data.cart_count);
                    syncDecreaseBtn(row, data.quantity);
                }
            );
        }

        // ── Increase ─────────────────────────────────
        if (action === "increase") {
            var qtyEl = row.querySelector(".cart-qty-value");
            var qty   = parseInt(qtyEl.textContent, 10);
            var newQty = qty + 1;
            var stock  = parseInt(row.dataset.stock || 99, 10);

            if (newQty > stock || newQty > 99) return;

            btn.disabled = true;
            post(CART_UPDATE_URL, { product_id: productId, quantity: newQty },
                function (data) {
                    btn.disabled = false;
                    if (!data.ok) return;
                    qtyEl.textContent = data.quantity;
                    var lineTotalEl = row.querySelector(".cart-item-line-total");
                    if (lineTotalEl) lineTotalEl.textContent = fmt(data.line_total);
                    updateCartTotal(data.cart_total);
                    updateBadge(data.cart_count);
                    syncIncreaseBtn(row, data.quantity, stock);
                }
            );
        }

        // ── Remove ───────────────────────────────────
        if (action === "remove") {
            removeRow(row, productId);
        }
    });

    function removeRow(row, productId) {
        row.classList.add("is-removing");
        post(CART_REMOVE_URL, { product_id: productId }, function (data) {
            if (!data.ok) {
                row.classList.remove("is-removing");
                return;
            }
            row.style.transition = "opacity 200ms ease, max-height 300ms ease";
            row.style.maxHeight  = row.offsetHeight + "px";
            requestAnimationFrame(function () {
                row.style.maxHeight = "0";
                row.style.opacity   = "0";
                row.style.overflow  = "hidden";
                row.style.padding   = "0";
                row.style.margin    = "0";
                row.style.border    = "none";
            });
            setTimeout(function () {
                row.remove();
                updateCartTotal(data.cart_total);
                updateBadge(data.cart_count);
                checkEmptyCart(data.cart_count);
            }, 320);
        });
    }

    function syncDecreaseBtn(row, qty) {
        var btn = row.querySelector("[data-cart-action='decrease']");
        if (btn) btn.disabled = qty <= 1;
    }

    function syncIncreaseBtn(row, qty, stock) {
        var btn = row.querySelector("[data-cart-action='increase']");
        if (btn) btn.disabled = qty >= stock || qty >= 99;
    }

    function checkEmptyCart(count) {
        if (count > 0) return;
        var container = document.getElementById("cart-items-container");
        var summary   = document.getElementById("cart-summary-panel");
        if (container) {
            container.innerHTML =
                '<div class="empty-state" id="cart-empty-state">' +
                '<svg class="empty-state-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">' +
                '<circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/>' +
                '<path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>' +
                '</svg>' +
                '<h2 class="empty-state-title">Your cart is empty</h2>' +
                '<p class="empty-state-body">Head to the shop to find something you\'d like.</p>' +
                '<a href="/buyer/shop" class="btn btn-primary" id="shop-from-empty-cart-btn">Browse shop</a>' +
                '</div>';
        }
        if (summary) {
            summary.style.display = "none";
        }
    }

    // ── Two-step clear cart ─────────────────────────────────────

    var clearBtn    = document.getElementById("clear-cart-btn");
    var confirmGrp  = document.getElementById("clear-confirm-group");
    var confirmYes  = document.getElementById("clear-confirm-yes");
    var confirmNo   = document.getElementById("clear-confirm-no");

    if (clearBtn) {
        clearBtn.addEventListener("click", function () {
            clearBtn.style.display = "none";
            if (confirmGrp) confirmGrp.classList.add("is-visible");
        });
    }

    if (confirmNo) {
        confirmNo.addEventListener("click", function () {
            if (confirmGrp) confirmGrp.classList.remove("is-visible");
            if (clearBtn) clearBtn.style.display = "";
        });
    }

    if (confirmYes) {
        confirmYes.addEventListener("click", function () {
            confirmYes.disabled = true;
            post(CART_CLEAR_URL, {}, function (data) {
                if (!data.ok) return;
                updateBadge(0);
                checkEmptyCart(0);
            });
        });
    }

})();
