(() => {
    const selector = '[data-severity="warning"], [data-severity="error"], .alert-warning, .alert-danger';
    const routed = "data-diagnostics-routed";
    let pending = false;
    let fingerprint = "";

    function visible(source) {
        // A routed source is hidden by our CSS. Check its own explicit state
        // and its ancestors separately so it remains available to the drawer.
        if (source.hidden || source.style.display === "none") return false;
        if (!source.hasAttribute(routed) && getComputedStyle(source).display === "none") return false;
        for (let parent = source.parentElement; parent; parent = parent.parentElement) {
            if (parent.hidden || getComputedStyle(parent).display === "none") return false;
        }
        return true;
    }

    function sourceName(source) {
        if (source.dataset.diagnosticsSource) return source.dataset.diagnosticsSource;
        const header = source.closest(".card")?.querySelector(":scope > .card-header");
        const title = header?.querySelector(".rosettax-workflow-card-title") || header;
        return title?.textContent.trim() || "RosettaX";
    }

    function synchronize() {
        pending = false;
        const drawer = document.getElementById("app-diagnostics");
        const messages = document.getElementById("app-diagnostics-messages");
        const badge = document.getElementById("app-diagnostics-badge");
        const empty = document.getElementById("app-diagnostics-empty");
        if (!drawer || !messages || !badge || !empty) return;

        const notices = [];
        const sources = new Set();
        for (const node of document.querySelectorAll(selector)) {
            if (drawer.contains(node) || node.closest(".app-diagnostics-inline")) continue;
            if (!visible(node) || !node.textContent.trim()) continue;
            if (node.parentElement?.closest(selector)) continue;
            // Control feedback remains attached to its interactive controls.
            if (node.querySelector("button, input, select, textarea, a[href]")) continue;
            const severity = node.dataset.severity === "error" || node.classList.contains("alert-danger")
                ? "error" : "warning";
            sources.add(node);
            notices.push({node, severity, title: sourceName(node)});
        }

        for (const node of document.querySelectorAll(`[${routed}]`)) {
            if (!sources.has(node)) node.removeAttribute(routed);
        }
        for (const node of sources) {
            if (!node.hasAttribute(routed)) node.setAttribute(routed, "");
        }

        const nextFingerprint = JSON.stringify(notices.map(({node, severity, title}) => [severity, title, node.innerHTML]));
        if (nextFingerprint === fingerprint && notices.length === messages.childElementCount) return;
        fingerprint = nextFingerprint;
        const fragment = document.createDocumentFragment();
        for (const {node, severity, title} of notices) {
            const article = document.createElement("article");
            article.className = "app-diagnostics-message";
            const heading = document.createElement("h3");
            heading.textContent = `${title} · ${severity === "error" ? "Error" : "Warning"}`;
            const detail = node.cloneNode(true);
            detail.removeAttribute(routed);
            detail.removeAttribute("id");
            for (const child of detail.querySelectorAll("[id]")) child.removeAttribute("id");
            article.append(heading, detail);
            fragment.append(article);
        }
        messages.replaceChildren(fragment);
        const errors = notices.filter(notice => notice.severity === "error").length;
        const warnings = notices.length - errors;
        drawer.dataset.severity = errors ? "error" : warnings ? "warning" : "";
        empty.hidden = notices.length > 0;
        badge.hidden = notices.length === 0;
        badge.textContent = [
            errors ? `${errors} ${errors === 1 ? "error" : "errors"}` : "",
            warnings ? `${warnings} ${warnings === 1 ? "warning" : "warnings"}` : "",
        ].filter(Boolean).join(" · ");
    }

    const observer = new MutationObserver(records => {
        const drawer = document.getElementById("app-diagnostics");
        if (pending || records.every(record => drawer?.contains(record.target))) return;
        pending = true;
        requestAnimationFrame(synchronize);
    });
    observer.observe(document.documentElement, {
        subtree: true, childList: true, characterData: true, attributes: true,
        attributeFilter: ["class", "style", "hidden", "data-severity"],
    });
    synchronize();
})();
