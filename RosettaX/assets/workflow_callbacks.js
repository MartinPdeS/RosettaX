/* Card actions use browser-owned profile data and need no server request. */
window.dash_clientside = Object.assign({}, window.dash_clientside, {
    rosettax: Object.assign({}, window.dash_clientside?.rosettax, {
        toggleCalibrationCard: function (toggleClicks, stepClicks, library, selectedProfile, isOpen) {
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
                let name = String(selectedProfile || library?.selected_profile || "").trim();
                if (name && !name.endsWith(".json")) name += ".json";
                const profile = library?.profiles?.[name];
                if (!profile) return [noUpdate, noUpdate];
                const collapsed = profile.ui?.collapse_calibration_cards ??
                    profile.misc?.ui?.collapse_calibration_cards ?? false;
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
