(function () {
    let pending = 0;
    let showAt = 0;
    let hideTimer = null;

    const MIN_SHOW_MS = 250;

    function getEl() {
        return document.getElementById("periodProgress");
    }

    function render() {
        const el = getEl();
        if (!el) return;

        if (pending > 0) {
            // show immediately
            if (hideTimer) {
                clearTimeout(hideTimer);
                hideTimer = null;
            }
            el.classList.add("is-loading");
            showAt = Date.now();
            return;
        }

        // pending === 0 → hide, but not before MIN_SHOW_MS
        const elapsed = Date.now() - showAt;
        const wait = Math.max(0, MIN_SHOW_MS - elapsed);

        if (hideTimer) clearTimeout(hideTimer);
        hideTimer = setTimeout(() => {
            const el2 = getEl();
            if (el2) el2.classList.remove("is-loading");
            hideTimer = null;
        }, wait);
    }

    // start hidden on load
    document.addEventListener("DOMContentLoaded", () => {
        const el = getEl();
        if (el) el.classList.remove("is-loading");
    });

    window.periodProgressStart = function () {
        pending += 1;
        render();
    };

    window.periodProgressEnd = function () {
        pending = Math.max(0, pending - 1);
        render();
    };

    window.fetchWithPeriodProgress = function (url, options) {
        window.periodProgressStart();
        return fetch(url, options).finally(() => window.periodProgressEnd());
    };
})();
