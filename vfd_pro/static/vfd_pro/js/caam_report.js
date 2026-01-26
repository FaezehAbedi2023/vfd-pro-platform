/* ============================================================================
  caam_report.js
  - Consolidated client_summary scripts into a single file
  - Uses EXACT existing element IDs + POST keys from your working HTML scripts
  - Safe: won’t throw if elements / Chart.js / fetchWithPeriodProgress missing
============================================================================ */

/* =========================
   Utilities (shared)
========================= */
(function () {
    "use strict";

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie("csrftoken");

    function debounce(fn, delay) {
        let timer = null;
        return function (...args) {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }

    // matches your scripts (Yes/No / Y/N)
    function normalizeYesNo(v) {
        const s = String(v ?? "").trim().toLowerCase();
        if (s === "y" || s === "yes" || s === "true" || s === "1") return "Yes";
        if (s === "n" || s === "no" || s === "false" || s === "0") return "No";
        return v;
    }

    // for tick / cross in spans
    function setFlagIcon(el, yesNo) {
        if (!el) return;
        const isYes = String(yesNo || "").trim().toLowerCase() === "yes";
        el.textContent = isYes ? "✔" : "✖";
        el.classList.remove("check-yes", "check-no");
        el.classList.add(isYes ? "check-yes" : "check-no");
    }

    function formatAmount(x) {
        if (x === null || x === undefined || x === "") return "";
        const num = Number(x);
        if (isNaN(num)) return x;

        return num.toLocaleString("en-UK", {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
        });
    }


    function safeFormatAmount(v) {
        // keep same behavior as your inline scripts
        return formatAmount(v);
    }

    // Use fetchWithPeriodProgress if available; otherwise fallback to fetch
    function postForm(url, formData, useProgress) {
        const opts = {
            method: "POST",
            headers: { "X-CSRFToken": csrftoken },
            body: formData,
        };

        if (useProgress && typeof window.fetchWithPeriodProgress === "function") {
            return window.fetchWithPeriodProgress(url, opts);
        }
        return fetch(url, opts);
    }

    /* ============================================================================
       AJAX: Opportunity / Performance
       (IDs + POST KEYS exactly as your working scripts)
    ============================================================================ */

    // Django URLs come from template strings in HTML normally.
    // We support both:
    //   1) window.CAAM_URLS populated in template (recommended),
    //   2) fallback to reading data attributes (if you set them),
    //   3) otherwise: you MUST set window.CAAM_URLS.* in HTML before this script.
    //
    // Suggested in HTML:
    // <script>
    //   window.CAAM_URLS = {
    //     revenueUrl: "{% url 'caam:ajax_revenue_criteria' client_id=client_id %}",
    //     gmUrl: "{% url 'caam:ajax_gm_criteria' client_id=client_id %}",
    //     overheadUrl: "{% url 'caam:ajax_oh_val_criteria' client_id=client_id %}",
    //     overheadPctUrl: "{% url 'caam:ajax_oh_pct_criteria' client_id=client_id %}",
    //     ebitdaUrl: "{% url 'caam:ajax_ebitda_criteria' client_id=client_id %}",
    //     newcustUrl: "{% url 'caam:ajax_newcust_criteria' client_id=client_id %}",
    //     retentionUrl: "{% url 'caam:ajax_retention_criteria' client_id=client_id %}",
    //     cashUrl: "{% url 'caam:ajax_cash_criteria' client_id=client_id %}",
    //     debtorUrl: "{% url 'caam:ajax_debtordays_criteria' client_id=client_id %}",
    //     creditorUrl: "{% url 'caam:ajax_creditordays_criteria' client_id=client_id %}",
    //     stockUrl: "{% url 'caam:ajax_stockdays_criteria' client_id=client_id %}",
    //   };
    // </script>
    const URLS = (window.CAAM_URLS || {});

    function callPerfRevenueSp() {
        const revenueUrl = URLS.revenueUrl;
        if (!revenueUrl) return;

        const enabledEl = document.getElementById("p_revenue_enable");
        const periodEl = document.getElementById("p_period");
        const dirEl = document.getElementById("p_revenue_sign_mode");
        const thresholdEl = document.getElementById("p_revenue_threshold_percent");

        if (!enabledEl || !periodEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("rev_enabled", enabledEl.value);
        formData.append("rev_period", periodEl.value);
        formData.append("rev_dir", dirEl.value);
        formData.append("rev_threshold", thresholdEl.value);

        postForm(revenueUrl, formData, true)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const flagIconEl = document.getElementById("opp_rev_flag_icon");
                const profitImpactEl = document.getElementById("opp_Revenue_Impact_Profit");
                const valImpactEl = document.getElementById("opp_Revenue_val_impact");

                setFlagIcon(flagIconEl, data.rev_flag);
                if (profitImpactEl) profitImpactEl.value = data.rev_profit_impact ?? "";
                if (valImpactEl) valImpactEl.value = data.rev_val_impact ?? "";

                // keep Multiple derived fields in sync (if you use it)
                if (typeof window.updateMultipleDerivedFields === "function") {
                    window.updateMultipleDerivedFields();
                }
            })
            .catch(() => { });
    }

    function callPerfGmSp() {
        const gmUrl = URLS.gmUrl;
        if (!gmUrl) return;

        const enabledEl = document.getElementById("p_gm_enable");
        const periodEl = document.getElementById("p_period");
        const dirEl = document.getElementById("p_gm_sign_mode");
        const thresholdEl = document.getElementById("p_gm_threshold_percent");

        if (!enabledEl || !periodEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("gm_enabled", normalizeYesNo(enabledEl.value));
        formData.append("gm_period", periodEl.value);
        formData.append("gm_dir", dirEl.value);
        formData.append("gm_threshold", thresholdEl.value);

        postForm(gmUrl, formData, true)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const out12 = document.getElementById("opp_gm_last12");
                const out6 = document.getElementById("opp_gm_last6");
                const out3 = document.getElementById("opp_gm_last3");
                const flag = document.getElementById("opp_gm_flag_icon");
                const pi = document.getElementById("opp_gm_profit_impact");
                const vi = document.getElementById("opp_gm_val_impact");

                if (out12) out12.value = data.gm_last_12 ?? "";
                if (out6) out6.value = data.gm_last_6 ?? "";
                if (out3) out3.value = data.gm_last_3 ?? "";

                setFlagIcon(flag, data.gm_flag);
                if (pi) pi.value = data.gm_profit_impact ?? "";
                if (vi) vi.value = data.gm_val_impact ?? "";

                if (typeof window.updateMultipleDerivedFields === "function") {
                    window.updateMultipleDerivedFields();
                }
            })
            .catch(() => { });
    }

    function callPerfOverheadSp() {
        const overheadUrl = URLS.overheadUrl;
        if (!overheadUrl) return;

        const enabledEl = document.getElementById("p_oh_enable");
        const periodEl = document.getElementById("p_period");
        const dirEl = document.getElementById("p_oh_sign_mode");
        const thresholdEl = document.getElementById("p_oh_threshold_percent");
        const valAdjEl = document.getElementById("val_adj"); // optional

        if (!enabledEl || !periodEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("oh_val_enabled", normalizeYesNo(enabledEl.value));
        formData.append("oh_val_period", periodEl.value);
        formData.append("oh_val_dir", dirEl.value);
        formData.append("oh_val_threshold", thresholdEl.value);
        if (valAdjEl && valAdjEl.value !== "") formData.append("val_adj", valAdjEl.value);

        postForm(overheadUrl, formData, true)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const flagIconEl = document.getElementById("opp_oh_flag_icon");
                const profitImpactEl = document.getElementById("opp_Overheads_profit_impact");
                const valImpactEl = document.getElementById("opp_Overheads_val_impact");

                setFlagIcon(flagIconEl, data.oh_val_flag);
                if (profitImpactEl) profitImpactEl.value = data.oh_val_profit_impact ?? "";
                if (valImpactEl) valImpactEl.value = data.oh_val_val_impact ?? "";

                if (typeof window.updateMultipleDerivedFields === "function") {
                    window.updateMultipleDerivedFields();
                }
            })
            .catch(() => { });
    }

    function callOverheadPctSp() {
        const overheadPctUrl = URLS.overheadPctUrl;
        if (!overheadPctUrl) return;

        const enabledEl = document.getElementById("p_oh_pct_enable");
        const periodEl = document.getElementById("p_period");
        const dirEl = document.getElementById("p_oh_pct_sign_mode");
        const thresholdEl = document.getElementById("p_oh_pct_threshold_percent");
        const valAdjEl = document.getElementById("val_adj"); // optional

        if (!enabledEl || !periodEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("oh_pct_enabled", normalizeYesNo(enabledEl.value));
        formData.append("oh_pct_period", periodEl.value);
        formData.append("oh_pct_dir", dirEl.value);
        formData.append("oh_pct_threshold", thresholdEl.value);
        if (valAdjEl && valAdjEl.value !== "") formData.append("val_adj", valAdjEl.value);

        postForm(overheadPctUrl, formData, true)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const out12 = document.getElementById("opp_ohp_last12");
                const out6 = document.getElementById("opp_ohp_last6");
                const out3 = document.getElementById("opp_ohp_last3");

                const flagIconEl = document.getElementById("opp_ohp_flag_icon");
                const profitImpactEl = document.getElementById("opp_Overhead_pct_profit_impact");
                const valImpactEl = document.getElementById("opp_Overhead_pct_val_impact");

                if (out12) out12.value = data.oh_pct_last_12 ?? "";
                if (out6) out6.value = data.oh_pct_last_6 ?? "";
                if (out3) out3.value = data.oh_pct_last_3 ?? "";

                setFlagIcon(flagIconEl, data.oh_pct_flag);
                if (profitImpactEl) profitImpactEl.value = data.oh_pct_profit_impact ?? "";
                if (valImpactEl) valImpactEl.value = data.oh_pct_val_impact ?? "";

                if (typeof window.updateMultipleDerivedFields === "function") {
                    window.updateMultipleDerivedFields();
                }
            })
            .catch(() => { });
    }

    function callEbitdaSp() {
        const ebitdaUrl = URLS.ebitdaUrl;
        if (!ebitdaUrl) return;

        const enabledEl = document.getElementById("p_ebitda_enable");
        const dirEl = document.getElementById("p_ebitda_sign_mode");
        const thresholdEl = document.getElementById("p_ebitda_threshold_percent");

        if (!enabledEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("ebitda_enabled", normalizeYesNo(enabledEl.value));
        formData.append("ebitda_dir", dirEl.value);
        formData.append("ebitda_threshold", thresholdEl.value);
        formData.append("ebitda_period", "12"); // per your script

        postForm(ebitdaUrl, formData, false)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const tyEl = document.getElementById("opp_ebitda_ty_12m");
                const lyEl = document.getElementById("opp_ebitda_ly_12m");
                const vpctEl = document.getElementById("opp_ebitda_var_pct");
                const vvalEl = document.getElementById("opp_ebitda_var_val");

                const flagIconEl = document.getElementById("opp_eb_flag_icon");
                const impactEl = document.getElementById("opp_ebitda_impact");

                if (tyEl) tyEl.value = safeFormatAmount(data.ebitda_ty);
                if (lyEl) lyEl.value = safeFormatAmount(data.ebitda_ly);
                if (vpctEl) vpctEl.value = data.ebitda_var_pct ?? "";
                if (vvalEl) vvalEl.value = safeFormatAmount(data.ebitda_var_val);

                setFlagIcon(flagIconEl, data.ebitda_flag);
                if (impactEl) impactEl.value = data.ebitda_impact ?? "";

                // IHT depends on EBITDA TY
                calcIht();

                if (typeof window.updateMultipleDerivedFields === "function") {
                    window.updateMultipleDerivedFields();
                }
            })
            .catch(() => { });
    }

    function callNewcustSp() {
        const newcustUrl = URLS.newcustUrl;
        if (!newcustUrl) return;

        const enabledEl = document.getElementById("p_ncust_enable");
        const periodEl = document.getElementById("p_period");
        const dirEl = document.getElementById("p_ncust_sign_mode");
        const thresholdEl = document.getElementById("p_ncust_threshold_percent");

        if (!enabledEl || !periodEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("newcust_enabled", normalizeYesNo(enabledEl.value));
        formData.append("newcust_period", periodEl.value);
        formData.append("newcust_dir", dirEl.value);
        formData.append("newcust_threshold", thresholdEl.value);

        postForm(newcustUrl, formData, false)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const tyEl = document.getElementById("opp_ncust_ty");
                const lyEl = document.getElementById("opp_ncust_ly");
                const vpctEl = document.getElementById("opp_ncust_var_pct");
                const flagIconEl = document.getElementById("opp_nc_flag_icon");

                if (tyEl) tyEl.value = data.newcust_ty ?? "";
                if (lyEl) lyEl.value = data.newcust_ly ?? "";
                if (vpctEl) vpctEl.value = data.newcust_var_pct ?? "";

                setFlagIcon(flagIconEl, data.newcust_flag);
            })
            .catch(() => { });
    }

    function callRetentionSp() {
        const retentionUrl = URLS.retentionUrl;
        if (!retentionUrl) return;

        const enabledEl = document.getElementById("p_retention_enable");
        const periodEl = document.getElementById("p_period");
        const dirEl = document.getElementById("p_retention_sign_mode");
        const thresholdEl = document.getElementById("p_retention_threshold_percent");

        if (!enabledEl || !periodEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("retention_enabled", normalizeYesNo(enabledEl.value));
        formData.append("retention_period", periodEl.value);
        formData.append("retention_dir", dirEl.value);
        formData.append("retention_threshold", thresholdEl.value);

        postForm(retentionUrl, formData, false)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const tyEl = document.getElementById("opp_ret_ty");
                const lyEl = document.getElementById("opp_ret_ly");
                const vpctEl = document.getElementById("opp_ret_var_pct");
                const flagIconEl = document.getElementById("opp_ret_flag_icon");

                if (tyEl) tyEl.value = data.retention_ty ?? "";
                if (lyEl) lyEl.value = data.retention_ly ?? "";
                if (vpctEl) vpctEl.value = data.retention_var_pct ?? "";

                setFlagIcon(flagIconEl, data.retention_flag);
            })
            .catch(() => { });
    }

    function callCashSp() {
        const cashUrl = URLS.cashUrl;
        if (!cashUrl) return;

        const enabledEl = document.getElementById("p_cp_enable");
        const dirEl = document.getElementById("p_cp_sign_mode");
        const thresholdEl = document.getElementById("p_cp_var_percent");

        if (!enabledEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("cash_enabled", normalizeYesNo(enabledEl.value));
        formData.append("cash_dir", dirEl.value);
        formData.append("cash_threshold", thresholdEl.value);

        postForm(cashUrl, formData, false)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const tyEl = document.getElementById("opp_cp_ty");
                const lyEl = document.getElementById("opp_cp_ly");
                const vpctEl = document.getElementById("opp_cp_var_pct");
                const vvalEl = document.getElementById("opp_cp_var_val");
                const flagIconEl = document.getElementById("opp_cp_flag_icon");

                if (tyEl) tyEl.value = safeFormatAmount(data.cash_ty);
                if (lyEl) lyEl.value = safeFormatAmount(data.cash_ly);
                if (vpctEl) vpctEl.value = data.cash_var_pct ?? "";
                if (vvalEl) vvalEl.value = safeFormatAmount(data.cash_var_val);

                setFlagIcon(flagIconEl, data.cash_flag);
            })
            .catch(() => { });
    }

    function callDebtorDaysSp() {
        const debtorUrl = URLS.debtorUrl;
        if (!debtorUrl) return;

        const enabledEl = document.getElementById("p_ddays_enable");
        const dirEl = document.getElementById("p_ddays_sign_mode");
        const thresholdEl = document.getElementById("p_ddays_var_percent");

        if (!enabledEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("debtordays_enabled", normalizeYesNo(enabledEl.value));
        formData.append("debtordays_dir", dirEl.value);
        formData.append("debtordays_threshold", thresholdEl.value);

        postForm(debtorUrl, formData, false)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const tyEl = document.getElementById("opp_dd_ty");
                const lyEl = document.getElementById("opp_dd_ly");
                const vpctEl = document.getElementById("opp_dd_var_pct");
                const vvalEl = document.getElementById("opp_dd_var_val");
                const flagIconEl = document.getElementById("opp_dd_flag_icon");

                if (tyEl) tyEl.value = safeFormatAmount(data.debtordays_ty);
                if (lyEl) lyEl.value = safeFormatAmount(data.debtordays_ly);
                if (vpctEl) vpctEl.value = data.debtordays_var_pct ?? "";
                if (vvalEl) vvalEl.value = safeFormatAmount(data.debtordays_var_val);

                setFlagIcon(flagIconEl, data.debtordays_flag);
            })
            .catch(() => { });
    }

    function callCreditorDaysSp() {
        const creditorUrl = URLS.creditorUrl;
        if (!creditorUrl) return;

        const enabledEl = document.getElementById("p_cdays_enable");
        const dirEl = document.getElementById("p_cdays_sign_mode");
        const thresholdEl = document.getElementById("p_cdays_var_percent");

        if (!enabledEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("creditordays_enabled", normalizeYesNo(enabledEl.value));
        formData.append("creditordays_dir", dirEl.value);
        formData.append("creditordays_threshold", thresholdEl.value);

        postForm(creditorUrl, formData, false)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const tyEl = document.getElementById("opp_cd_ty");
                const lyEl = document.getElementById("opp_cd_ly");
                const vpctEl = document.getElementById("opp_cd_var_pct");
                const vvalEl = document.getElementById("opp_cd_var_val");
                const flagIconEl = document.getElementById("opp_cd_flag_icon");

                if (tyEl) tyEl.value = safeFormatAmount(data.creditordays_ty);
                if (lyEl) lyEl.value = safeFormatAmount(data.creditordays_ly);
                if (vpctEl) vpctEl.value = data.creditordays_var_pct ?? "";
                if (vvalEl) vvalEl.value = safeFormatAmount(data.creditordays_var_val);

                setFlagIcon(flagIconEl, data.creditordays_flag);
            })
            .catch(() => { });
    }

    function callStockDaysSp() {
        const stockUrl = URLS.stockUrl;
        if (!stockUrl) return;

        const enabledEl = document.getElementById("p_sdays_enable");
        const dirEl = document.getElementById("p_sdays_sign_mode");
        const thresholdEl = document.getElementById("p_sdays_var_percent");

        if (!enabledEl || !dirEl || !thresholdEl) return;

        const formData = new FormData();
        // EXACT keys
        formData.append("stockdays_enabled", normalizeYesNo(enabledEl.value));
        formData.append("stockdays_dir", dirEl.value);
        formData.append("stockdays_threshold", thresholdEl.value);

        postForm(stockUrl, formData, false)
            .then((res) => res.json())
            .then((data) => {
                if (!data?.ok) return;

                const tyEl = document.getElementById("opp_sd_ty");
                const lyEl = document.getElementById("opp_sd_ly");
                const vpctEl = document.getElementById("opp_sd_var_pct");
                const vvalEl = document.getElementById("opp_sd_var_val");
                const flagIconEl = document.getElementById("opp_sd_flag_icon");

                if (tyEl) tyEl.value = safeFormatAmount(data.stockdays_ty);
                if (lyEl) lyEl.value = safeFormatAmount(data.stockdays_ly);
                if (vpctEl) vpctEl.value = data.stockdays_var_pct ?? "";
                if (vvalEl) vvalEl.value = safeFormatAmount(data.stockdays_var_val);

                setFlagIcon(flagIconEl, data.stockdays_flag);
            })
            .catch(() => { });
    }

    /* ============================================================================
       IHT (exact IDs)
    ============================================================================ */
    function toNumberSafe(x) {
        if (x === null || x === undefined || x === "") return 0;
        const n = Number(String(x).replace(/,/g, ""));
        return isNaN(n) ? 0 : n;
    }

    function setIhtIcon(isPass, enabled) {
        const iconEl = document.getElementById("iht_risk_icon");
        if (!iconEl) return;

        if (!enabled) {
            iconEl.textContent = "";
            iconEl.classList.remove("check-yes", "check-no");
            return;
        }

        iconEl.textContent = isPass ? "✔" : "✖";
        iconEl.classList.toggle("check-yes", isPass);
        iconEl.classList.toggle("check-no", !isPass);
    }

    function calcIht() {
        const enabledEl = document.getElementById("iht_enable");
        const ebitdaEl = document.getElementById("iht_ebitda_ty");
        const thresholdEl = document.getElementById("iht_valuation_threshold");

        const valAdjEl = document.getElementById("val_adj");
        const multEl = document.getElementById("iht_multiple");
        const estEl = document.getElementById("iht_est_valuation");

        if (!enabledEl || !ebitdaEl || !thresholdEl || !estEl) return;

        const enabled = enabledEl.value === "Yes";
        const ebitda = toNumberSafe(ebitdaEl.value);
        const multiple = valAdjEl ? toNumberSafe(valAdjEl.value) : toNumberSafe(multEl ? multEl.value : 3);
        const threshold = toNumberSafe(thresholdEl.value);

        if (multEl) multEl.value = multiple;

        const est = ebitda * multiple;
        estEl.value = enabled ? est.toLocaleString("en-UK") : "";

        const isPass = enabled && est >= threshold;
        setIhtIcon(isPass, enabled);
    }

    /* ============================================================================
       Donuts (exact IDs) + target inputs
       NOTE: scores/targets come from window.CAAM_PAGE if you set it; otherwise
             it will try to read from template-injected globals if you kept them.
    ============================================================================ */
    const centerTextPlugin = {
        id: "centerText",
        afterDraw(chart, args, pluginOptions) {
            const { ctx } = chart;
            const meta = chart.getDatasetMeta(0);
            if (!meta || !meta.data || !meta.data[0]) return;

            const x = meta.data[0].x;
            const y = meta.data[0].y;

            ctx.save();
            ctx.font = "700 14px system-ui, -apple-system, Segoe UI, sans-serif";
            ctx.fillStyle = pluginOptions?.color || "#111827";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(pluginOptions?.text || "", x, y);
            ctx.restore();
        },
    };

    function donut(elId, value, colorDone, colorRest) {
        const el = document.getElementById(elId);
        if (!el) return null;
        if (typeof window.Chart !== "function" && typeof window.Chart !== "object") return null;

        const v = Math.max(0, Math.min(100, Number(value || 0)));

        return new window.Chart(el, {
            type: "doughnut",
            data: {
                labels: ["Done", "Remaining"],
                datasets: [{
                    data: [v, 100 - v],
                    backgroundColor: [colorDone, colorRest],
                    borderWidth: 0,
                    hoverOffset: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "72%",
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false },
                    centerText: { text: v + "%", color: "#111827" },
                },
            },
            plugins: [centerTextPlugin],
        });
    }

    const GREEN_DONE = "#22c55e";
    const GREEN_REST = "#bbf7d0";
    const YELLOW_DONE = "#f59e0b";
    const YELLOW_REST = "#fde68a";

    let suitChart = null;
    let oppChart = null;
    let readChart = null;

    function pickDonutColors(score, target) {
        return (Number(score) >= Number(target))
            ? { done: GREEN_DONE, rest: GREEN_REST }
            : { done: YELLOW_DONE, rest: YELLOW_REST };
    }

    function renderDonuts() {
        // Prefer window.CAAM_PAGE if you set it in template
        const p = window.CAAM_PAGE || {};
        const suitability = Number(p.suitability ?? 0);
        const opportunity = Number(p.opportunity ?? 0);
        const readiness = Number(p.readiness ?? 0);

        const defaultTSuit = Number(p.targetSuitability ?? 50);
        const defaultTOpp = Number(p.targetOpportunity ?? 50);
        const defaultTRead = Number(p.targetReadiness ?? 50);

        const tSuitEl = document.getElementById("target_suitability");
        const tOppEl = document.getElementById("target_opportunity");
        const tReadEl = document.getElementById("target_readiness");

        const tSuit = tSuitEl ? Number(tSuitEl.value || defaultTSuit) : defaultTSuit;
        const tOpp = tOppEl ? Number(tOppEl.value || defaultTOpp) : defaultTOpp;
        const tRead = tReadEl ? Number(tReadEl.value || defaultTRead) : defaultTRead;

        const c1 = pickDonutColors(suitability, tSuit);
        const c2 = pickDonutColors(opportunity, tOpp);
        const c3 = pickDonutColors(readiness, tRead);

        if (suitChart) suitChart.destroy();
        if (oppChart) oppChart.destroy();
        if (readChart) readChart.destroy();

        suitChart = donut("kpiSuitabilityChart", suitability, c1.done, c1.rest);
        oppChart = donut("kpiOpportunityChart", opportunity, c2.done, c2.rest);
        readChart = donut("kpiReadinessChart", readiness, c3.done, c3.rest);
    }

    /* ============================================================================
       KPI box coloring (exact class/attrs)
    ============================================================================ */
    function normYN(v) {
        return String(v || "").trim().toLowerCase();
    }

    function applyFlagColors() {
        document.querySelectorAll(".kpi-box.js-flag").forEach((box) => {
            const rule = box.getAttribute("data-rule");
            const valEl = box.querySelector(".kpi-value");
            const v = normYN(valEl ? valEl.textContent : "");

            box.classList.remove("is-green", "is-yellow", "is-red");

            if (rule === "yes-green-no-yellow") {
                if (v === "yes") box.classList.add("is-green");
                else if (v === "no") box.classList.add("is-yellow");
            }

            if (rule === "no-green-yes-yellow") {
                if (v === "no") box.classList.add("is-green");
                else if (v === "yes") box.classList.add("is-yellow");
            }

            if (rule === "yes-red-no-green") {
                if (v === "yes") box.classList.add("is-red");
                else if (v === "no") box.classList.add("is-green");
            }
        });
    }

    /* ============================================================================
       Sales chart (exact IDs: sales-data, salesChart)
    ============================================================================ */
    function renderSalesChart() {
        const canvas = document.getElementById("salesChart");
        if (!canvas) return;
        if (typeof window.Chart !== "function" && typeof window.Chart !== "object") return;

        const salesDataElement = document.getElementById("sales-data");
        const salesData = salesDataElement ? JSON.parse(salesDataElement.textContent) : [];

        const labels = salesData.map((x) => x.offset);
        const monthly = salesData.map((x) => x.sales_month);
        const rolling = salesData.map((x) => x.rolling_12 || x.sales_rolling_12_months);

        const ctx = canvas.getContext("2d");
        if (!ctx) return;

        // Prevent double rendering if hot reload or re-init
        if (canvas.__chartInstance && typeof canvas.__chartInstance.destroy === "function") {
            canvas.__chartInstance.destroy();
        }

        canvas.__chartInstance = new window.Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        type: "bar",
                        label: "Sales",
                        data: monthly,
                        backgroundColor: "#16a34a",
                        borderRadius: 4,
                        maxBarThickness: 34,
                    },
                    {
                        type: "line",
                        label: "Rolling 12 Months",
                        data: rolling,
                        borderColor: "#22c55e",
                        borderWidth: 3,
                        pointRadius: 3,
                        pointHoverRadius: 4,
                        tension: 0.25,
                        yAxisID: "y1",
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: "index", intersect: false },
                scales: {
                    x: { ticks: { font: { size: 12 }, maxRotation: 0 }, grid: { display: false } },
                    y: {
                        ticks: { font: { size: 12 }, callback: (value) => Number(value).toLocaleString() },
                        grid: { color: "rgba(148, 163, 184, 0.15)" },
                    },
                    y1: {
                        position: "right",
                        ticks: { font: { size: 12 }, callback: (value) => Number(value).toLocaleString() },
                        grid: { drawOnChartArea: false },
                    },
                },
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { usePointStyle: true, boxWidth: 10, font: { size: 12 } },
                    },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                const label = ctx.dataset.label || "";
                                const value = Number(ctx.parsed.y).toLocaleString();
                                return `${label}: ${value}`;
                            },
                        },
                    },
                },
            },
        });
    }

    /* ============================================================================
       Multiple -> valuation impacts (exact IDs)
    ============================================================================ */
    function getMultiple() {
        const oppEl = document.getElementById("opp_multiple");
        const ihtEl = document.getElementById("iht_multiple");

        const srcEl =
            (oppEl && !oppEl.disabled) ? oppEl :
                (ihtEl && !ihtEl.disabled) ? ihtEl :
                    (oppEl || ihtEl);

        if (!srcEl) return null;
        const v = Number(srcEl.value);
        return Number.isFinite(v) ? v : null;
    }

    function setMultipleEverywhere(val) {
        const oppEl = document.getElementById("opp_multiple");
        const ihtEl = document.getElementById("iht_multiple");
        if (oppEl) oppEl.value = val;
        if (ihtEl) ihtEl.value = val;
    }

    const KPI_VALUATION_MAP = [
        { profitId: "opp_Revenue_Impact_Profit", valuationId: "opp_Revenue_val_impact" },
        { profitId: "opp_gm_profit_impact", valuationId: "opp_gm_val_impact" },
        { profitId: "opp_Overheads_profit_impact", valuationId: "opp_Overheads_val_impact" },
        { profitId: "opp_Overhead_pct_profit_impact", valuationId: "opp_Overhead_pct_val_impact" },
    ];

    function updateOppValuations(multiple) {
        KPI_VALUATION_MAP.forEach(({ profitId, valuationId }) => {
            const profitEl = document.getElementById(profitId);
            const valuationEl = document.getElementById(valuationId);
            if (!profitEl || !valuationEl) return;

            const profit = toNumberSafe(profitEl.value);

            if (!Number.isFinite(multiple) || profitEl.value === "" || isNaN(profit)) {
                valuationEl.value = "";
                return;
            }

            const v = profit * multiple;

            valuationEl.value = safeFormatAmount(v);
        });
    }


    const IHT_MAP = { ebitda12Id: "iht_ebitda_ty", estimatedValueId: "iht_est_valuation" };

    function updateIhtEstimate(multiple) {
        const e12El = document.getElementById(IHT_MAP.ebitda12Id);
        const estEl = document.getElementById(IHT_MAP.estimatedValueId);
        if (!e12El || !estEl) return;

        const ebitda12 = toNumberSafe(e12El.value);
        const v = ebitda12 * multiple;

        estEl.value = Number.isFinite(v) ? safeFormatAmount(v) : "";
    }


    function updateMultipleDerivedFields() {
        const multiple = getMultiple();
        if (multiple === null) return;
        setMultipleEverywhere(multiple);
        updateOppValuations(multiple);
        updateIhtEstimate(multiple);
        // IHT icon recalculation (because estimated changes)
        calcIht();
    }

    /* ============================================================================
       INIT: bind events
    ============================================================================ */
    function bindIfExists(id, evt, handler, opts) {
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener(evt, handler, opts);
    }

    function init() {
        // ---------------- Revenue ----------------
        bindIfExists("p_revenue_enable", "change", callPerfRevenueSp);
        bindIfExists("p_period", "change", callPerfRevenueSp);
        bindIfExists("p_revenue_sign_mode", "change", callPerfRevenueSp);
        bindIfExists("p_revenue_threshold_percent", "input", debounce(callPerfRevenueSp, 500));
        bindIfExists("p_revenue_threshold_percent", "change", callPerfRevenueSp);

        // ---------------- GM ----------------
        bindIfExists("p_gm_enable", "change", callPerfGmSp);
        bindIfExists("p_period", "change", callPerfGmSp);
        bindIfExists("p_gm_sign_mode", "change", callPerfGmSp);
        bindIfExists("p_gm_threshold_percent", "input", debounce(callPerfGmSp, 500));
        bindIfExists("p_gm_threshold_percent", "change", callPerfGmSp);

        // ---------------- Overhead £ ----------------
        bindIfExists("p_oh_enable", "change", callPerfOverheadSp);
        bindIfExists("p_period", "change", callPerfOverheadSp);
        bindIfExists("p_oh_sign_mode", "change", callPerfOverheadSp);
        bindIfExists("p_oh_threshold_percent", "input", debounce(callPerfOverheadSp, 500));
        bindIfExists("p_oh_threshold_percent", "change", callPerfOverheadSp);

        // ---------------- Overhead % ----------------
        bindIfExists("p_oh_pct_enable", "change", callOverheadPctSp);
        bindIfExists("p_period", "change", callOverheadPctSp);
        bindIfExists("p_oh_pct_sign_mode", "change", callOverheadPctSp);
        bindIfExists("p_oh_pct_threshold_percent", "input", debounce(callOverheadPctSp, 500));
        bindIfExists("p_oh_pct_threshold_percent", "change", callOverheadPctSp);

        // ---------------- EBITDA ----------------
        bindIfExists("p_ebitda_enable", "change", callEbitdaSp);
        bindIfExists("p_ebitda_sign_mode", "change", callEbitdaSp);
        bindIfExists("p_ebitda_threshold_percent", "input", debounce(callEbitdaSp, 500));
        bindIfExists("p_ebitda_threshold_percent", "change", callEbitdaSp);

        // ---------------- New Customers ----------------
        bindIfExists("p_ncust_enable", "change", callNewcustSp);
        bindIfExists("p_period", "change", callNewcustSp);
        bindIfExists("p_ncust_sign_mode", "change", callNewcustSp);
        bindIfExists("p_ncust_threshold_percent", "input", debounce(callNewcustSp, 500));
        bindIfExists("p_ncust_threshold_percent", "change", callNewcustSp);

        // ---------------- Retention ----------------
        bindIfExists("p_retention_enable", "change", callRetentionSp);
        bindIfExists("p_period", "change", callRetentionSp);
        bindIfExists("p_retention_sign_mode", "change", callRetentionSp);
        bindIfExists("p_retention_threshold_percent", "input", debounce(callRetentionSp, 500));
        bindIfExists("p_retention_threshold_percent", "change", callRetentionSp);

        // ---------------- Cash ----------------
        bindIfExists("p_cp_enable", "change", callCashSp);
        bindIfExists("p_cp_sign_mode", "change", callCashSp);
        bindIfExists("p_cp_var_percent", "input", debounce(callCashSp, 500));
        bindIfExists("p_cp_var_percent", "change", callCashSp);

        // ---------------- Debtor Days ----------------
        bindIfExists("p_ddays_enable", "change", callDebtorDaysSp);
        bindIfExists("p_ddays_sign_mode", "change", callDebtorDaysSp);
        bindIfExists("p_ddays_var_percent", "input", debounce(callDebtorDaysSp, 500));
        bindIfExists("p_ddays_var_percent", "change", callDebtorDaysSp);

        // ---------------- Creditor Days ----------------
        bindIfExists("p_cdays_enable", "change", callCreditorDaysSp);
        bindIfExists("p_cdays_sign_mode", "change", callCreditorDaysSp);
        bindIfExists("p_cdays_var_percent", "input", debounce(callCreditorDaysSp, 500));
        bindIfExists("p_cdays_var_percent", "change", callCreditorDaysSp);

        // ---------------- Stock Days ----------------
        bindIfExists("p_sdays_enable", "change", callStockDaysSp);
        bindIfExists("p_sdays_sign_mode", "change", callStockDaysSp);
        bindIfExists("p_sdays_var_percent", "input", debounce(callStockDaysSp, 500));
        bindIfExists("p_sdays_var_percent", "change", callStockDaysSp);

        // ---------------- IHT ----------------
        bindIfExists("iht_enable", "change", calcIht);
        bindIfExists("iht_valuation_threshold", "input", calcIht);
        bindIfExists("val_adj", "input", calcIht);

        // ---------------- Donuts targets ----------------
        ["target_suitability", "target_opportunity", "target_readiness"].forEach((id) => {
            bindIfExists(id, "input", renderDonuts);
            bindIfExists(id, "change", renderDonuts);
        });

        // ---------------- Multiple ----------------
        bindIfExists("opp_multiple", "input", debounce(updateMultipleDerivedFields, 150));
        bindIfExists("opp_multiple", "change", updateMultipleDerivedFields);
        bindIfExists("iht_multiple", "input", debounce(updateMultipleDerivedFields, 150));
        bindIfExists("iht_multiple", "change", updateMultipleDerivedFields);

        // Initial UI renders (safe)
        applyFlagColors();
        renderDonuts();
        renderSalesChart();
        updateMultipleDerivedFields();
        calcIht();

        // Expose for other scripts if needed
        window.updateMultipleDerivedFields = updateMultipleDerivedFields;
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
/* =========================================================
   CAAM Report - Save Criteria (build JSON + POST)

   ✔ Reads values from existing HTML IDs
   ✔ Collects Readiness / Suitability from tables:
        #outer-readiness
        #outer-suitability
   ✔ Builds full config JSON
   ✔ Sends to ajax_save_config endpoint
   ✔ Prevents default form submit
   ========================================================= */

(function () {
    "use strict";

    // ---------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------
    function getSummarySavingModal() {
        const el = document.getElementById("summarySavingModal");
        if (!el || !window.bootstrap) return null;
        return bootstrap.Modal.getOrCreateInstance(el);
    }

    function initSummarySaveCriteria() {
        const btn = document.getElementById("btnSummarySaveCriteria");
        if (!btn) return;

        btn.addEventListener("click", async (e) => {
            e.preventDefault();

            const m = getSummarySavingModal();
            btn.disabled = true;

            try {
                m && m.show();
                await saveConfig();

            } catch (err) {
                console.error("[Summary Save] failed:", err);
                alert(err?.message || "Save failed");
            } finally {
                m && m.hide();
                btn.disabled = false;
            }
        });
    }





    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === name + "=") {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function yn(v) {
        const s = String(v ?? "").trim().toLowerCase();
        if (s === "y" || s === "yes" || s === "true" || s === "1") return "Yes";
        if (s === "n" || s === "no" || s === "false" || s === "0") return "No";
        return v ?? "";
    }

    function num(v, fallback = 0) {
        if (v === null || v === undefined || v === "") return fallback;
        const cleaned = String(v).replace(/[^0-9.\-]/g, "").trim();
        const n = Number(cleaned);
        return Number.isFinite(n) ? n : fallback;
    }

    function val(id) {
        const el = document.getElementById(id);
        return el ? el.value : null;
    }

    function getQSInt(key, fallback = null) {
        const url = new URL(window.location.href);
        const v = url.searchParams.get(key);
        if (v === null || v === "") return fallback;
        const n = Number(v);
        return Number.isFinite(n) ? n : fallback;
    }

    // ---------------------------------------------------------
    // Collect Readiness / Suitability from tables
    // ---------------------------------------------------------
    function collectChecksFromTable(tableSelector) {
        const out = [];
        const table = document.querySelector(tableSelector);
        if (!table) return out;

        table.querySelectorAll("tbody tr").forEach((tr) => {
            const tds = tr.querySelectorAll("td");
            if (!tds || tds.length < 2) return;

            const sel = tr.querySelector("select");
            const fieldName = (tds[1].textContent || "").trim();
            if (!fieldName) return;

            out.push({
                enable: sel ? yn(sel.value) : "No",
                field_name: fieldName
            });
        });

        return out;
    }

    // ---------------------------------------------------------
    // Opportunity builders
    // ---------------------------------------------------------
    function buildOpportunityPerformanceItems() {
        return [
            { enable: yn(val("p_revenue_enable")), dir: val("p_revenue_sign_mode") ?? "-", field_name: "Revenue", threshold_percent: num(val("p_revenue_threshold_percent"), 1.0) },
            { enable: yn(val("p_gm_enable")), dir: val("p_gm_sign_mode") ?? "-", field_name: "Gross Margin %", threshold_percent: num(val("p_gm_threshold_percent"), 1.0) },
            { enable: yn(val("p_oh_enable")), dir: val("p_oh_sign_mode") ?? "-", field_name: "Overhead £", threshold_percent: num(val("p_oh_threshold_percent"), 1.0) },
            { enable: yn(val("p_oh_pct_enable")), dir: val("p_oh_pct_sign_mode") ?? "-", field_name: "Overhead %", threshold_percent: num(val("p_oh_pct_threshold_percent"), 1.0) },
            { enable: yn(val("p_ebitda_enable")), dir: val("p_ebitda_sign_mode") ?? "-", field_name: "EBITDA £", threshold_percent: num(val("p_ebitda_threshold_percent"), 1.0) },
            { enable: yn(val("p_ncust_enable")), dir: val("p_ncust_sign_mode") ?? "-", field_name: "New Customers", threshold_percent: num(val("p_ncust_threshold_percent"), 1.0) },
            { enable: yn(val("p_retention_enable")), dir: val("p_retention_sign_mode") ?? "-", field_name: "Client Retention", threshold_percent: num(val("p_retention_threshold_percent"), 1.0) },
        ];
    }

    function buildOpportunityWorkingCapitalItems() {
        return [
            { enable: yn(val("p_cp_enable")), dir: val("p_cp_sign_mode") ?? "-", field_name: "Cash Position", var_percent: num(val("p_cp_var_percent"), 1.0) },
            { enable: yn(val("p_ddays_enable")), dir: val("p_ddays_sign_mode") ?? "-", field_name: "Debtor Days", var_percent: num(val("p_ddays_var_percent"), 1.0) },
            { enable: yn(val("p_cdays_enable")), dir: val("p_cdays_sign_mode") ?? "-", field_name: "Creditor Days", var_percent: num(val("p_cdays_var_percent"), 1.0) },
            { enable: yn(val("p_sdays_enable")), dir: val("p_sdays_sign_mode") ?? "-", field_name: "Stock Days", var_percent: num(val("p_sdays_var_percent"), 1.0) },
        ];
    }

    // ---------------------------------------------------------
    // Build full Config JSON from UI
    // ---------------------------------------------------------
    function buildConfigJson() {
        const targetSuit = num(val("target_suitability"), 50);
        const targetOpp = num(val("target_opportunity"), 35);
        const targetRead = num(val("target_readiness"), 25);

        const timePeriod = num(val("p_period"), 12);
        const multiple = num(val("val_adj") ?? val("opp_multiple"), 3);

        const ihtEnable = yn(val("iht_enable"));
        const ihtThreshold = num(val("iht_valuation_threshold"), 900000);

        const suitabilityChecks = collectChecksFromTable("#outer-suitability");
        const readinessChecks = collectChecksFromTable("#outer-readiness");

        return {

            p_period: timePeriod,
            multiple: multiple,

            IHT: {
                enable: ihtEnable,
                valuation_threshold: ihtThreshold
            },
            Readiness: {
                checks: readinessChecks,
                target_percent: targetRead
            },
            Opportunity: {

                time_period: timePeriod,
                multiple: multiple,

                target_percent: targetOpp,
                performance: { items: buildOpportunityPerformanceItems() },
                working_capital: { items: buildOpportunityWorkingCapitalItems() }
            },
            Suitability: {
                checks: suitabilityChecks,
                target_percent: targetSuit
            }
        };
    }


    // ---------------------------------------------------------
    // Save Config
    // ---------------------------------------------------------
    // async function saveConfig() {
    async function saveConfig(opts = {}) {
        const url = window.CAAM_ENDPOINTS && window.CAAM_ENDPOINTS.save_config;
        if (!url) {
            alert("Save endpoint not configured.");
            return;
        }

        const csrftoken = getCookie("csrftoken");

        const companyId =
            (window.CAAM_PAGE && Number.isFinite(window.CAAM_PAGE.companyId) && window.CAAM_PAGE.companyId) ||
            getQSInt("company_id", null);

        if (companyId === null) {
            alert("company_id not found.");
            return;
        }

        const version =
            (window.CAAM_PAGE && Number.isFinite(window.CAAM_PAGE.version))
                ? window.CAAM_PAGE.version
                : 0;

        const config = buildConfigJson();

        // payload 
        const payload = {
            company_id: companyId,
            version: version,
            config: config
        };

        if (opts && typeof opts.resetFlag !== "undefined") {
            payload.reset_flag = opts.resetFlag;
        }

        console.log("[SaveConfig] payload =", payload);

        try {
            const res = await fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(payload)
            });

            const data = await res.json().catch(() => ({}));

            if (!res.ok || !data.ok) {
                console.error("[SaveConfig] failed", res.status, data);
                alert(data.error || "Save failed.");
                return;
            }

            alert("Saved successfully.");
            window.location.reload();


        } catch (err) {
            console.error("[SaveConfig] network error", err);
            alert("Save failed (network/server error).");
        }
    }

    window.saveConfig = saveConfig;
    // ---------------------------------------------------------
    // Init
    // ---------------------------------------------------------
    function initSaveCriteria() {

        const form = document.querySelector("#opportunityCriteriaModal form");
        if (!form) {
            console.warn("[SaveConfig] form not found");
            return;
        }


        form.addEventListener("submit", function (e) {
            e.preventDefault();
            saveConfig();
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSaveCriteria);
    } else {
        initSaveCriteria();
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initSummarySaveCriteria);
    } else {
        initSummarySaveCriteria();
    }


})();
