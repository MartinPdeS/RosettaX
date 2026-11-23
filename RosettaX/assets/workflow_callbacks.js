/* Card actions use browser-owned profile data and need no server request. */
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    rosettax: Object.assign({}, window.dash_clientside?.rosettax, {
        capturePeakViewport: function (changes, figure, graphId, viewport) {
            const triggered = window.dash_clientside.callback_context.triggered;
            if (triggered.some(item => item.prop_id === `${graphId}.figure`) &&
                viewport && viewport.revision !== figure?.layout?.uirevision) {
                return null;
            }
            if (!triggered.some(item => item.prop_id === `${graphId}.relayoutData`) ||
                !changes || !Object.keys(changes).some(key => /^(xaxis|yaxis)\.(range|autorange)/.test(key))) {
                return window.dash_clientside.no_update;
            }
            const graph = document.getElementById(graphId)?.querySelector(".js-plotly-plot");
            const layout = graph?._fullLayout;
            if (!layout?.uirevision || !layout.xaxis?.range || !layout.yaxis?.range) {
                return window.dash_clientside.no_update;
            }
            return {
                revision: layout.uirevision,
                axis_ranges: {xaxis: [...layout.xaxis.range], yaxis: [...layout.yaxis.range]}
            };
        },
        toggleCalibrationCard: function (toggleClicks, stepClicks, runtimeConfig, isOpen, cardId) {
            const noUpdate = window.dash_clientside.no_update;
            const triggered = window.dash_clientside.callback_context.triggered_id;
            let nextOpen;
            if (triggered && typeof triggered === "object") {
                if (triggered.type === "workflow-step-card" && stepClicks) {
                    nextOpen = !isOpen;
                } else if (triggered.type === "calibration-card-toggle" && toggleClicks) {
                    nextOpen = !isOpen;
                } else {
                    // Recreated workflow headers have zero clicks.
                    return [noUpdate, noUpdate];
                }
            } else {
                if (cardId?.section === "1" && ["scattering_calibration", "fluorescent_calibration", "cross-calibration"].includes(cardId.page)) {
                    return [noUpdate, noUpdate];
                }
                if (!runtimeConfig) return [noUpdate, noUpdate];
                const collapsed = runtimeConfig.ui?.collapse_calibration_cards ??
                    runtimeConfig.misc?.ui?.collapse_calibration_cards ?? false;
                const flag = typeof collapsed === "string" ?
                    ["true", "1", "yes", "on", "enabled"].includes(collapsed.trim().toLowerCase()) :
                    Boolean(collapsed);
                nextOpen = !flag;
            }
            if (nextOpen === Boolean(isOpen)) return [noUpdate, noUpdate];
            return [nextOpen, nextOpen ? "Hide" : "Show"];
        }
    })
});
