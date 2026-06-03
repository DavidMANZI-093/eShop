(function () {
    "use strict";

    const DISMISSED_KEY = "eshop_verify_banner_dismissed";
    const banner        = document.getElementById("verification-banner");
    const dismissBtn    = document.getElementById("dismiss-verification-banner");

    if (!banner) return;

    if (sessionStorage.getItem(DISMISSED_KEY)) {
        banner.classList.add("is-hidden");
        return;
    }

    dismissBtn.addEventListener("click", function () {
        banner.classList.add("is-hidden");
        sessionStorage.setItem(DISMISSED_KEY, "1");
    });
})();
