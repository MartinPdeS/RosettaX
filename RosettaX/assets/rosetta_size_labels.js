(() => {
    const observedPlots = new WeakSet();
    const pendingPlots = new WeakSet();
    const labelName = "rosetta-size-guide";

    function overlaps(label, other) {
        const horizontal = label.position - other.position;
        const vertical = other.rise - label.rise;
        // Project the distance between the label anchors onto the rotated text axes.
        const along = (horizontal - vertical) * Math.SQRT1_2 + (label.width - other.width) / 2;
        const across = (horizontal + vertical) * Math.SQRT1_2 - (label.height - other.height) / 2;
        return Math.abs(along) < (label.width + other.width) / 2 + 3 &&
            Math.abs(across) < (label.height + other.height) / 2 + 3;
    }

    function placeLabel(label, placed) {
        const nearestRight = placed.at(-1);
        const largestShift = Math.min(label.rightLimit, nearestRight ? Math.floor(nearestRight.position - label.guide) : Infinity);
        let closest;
        let shortestDistance = Infinity;
        for (const candidateShift of [0, -8, 8, -16, 16, -24, 24, -32, 32]) {
            const shift = Math.max(label.leftLimit, Math.min(largestShift, candidateShift));
            const candidate = {...label, shift, position: label.guide + shift, rise: 4};
            while (placed.some(other => overlaps(candidate, other))) candidate.rise += 6;
            const distance = Math.hypot(1.2 * shift, candidate.rise - 4);
            if (distance < shortestDistance) {
                closest = candidate;
                shortestDistance = distance;
            }
        }
        return closest;
    }

    function placeLabels(plot) {
        const annotations = plot.layout?.annotations;
        const axis = plot._fullLayout?.xaxis;
        if (!plot.isConnected || typeof axis?.r2p !== "function" ||
            !annotations?.some(annotation => annotation.name === labelName)) return;

        const labels = [];
        annotations.forEach((annotation, index) => {
            if (annotation.name !== labelName) return;
            const guide = axis.r2p(annotation.x);
            if (!Number.isFinite(guide) || guide < 0 || guide > axis._length) return;
            const text = plot.querySelector(`g.annotation[data-index="${index}"] .annotation-text`);
            if (!text) return;

            const {width, height} = text.getBBox();
            const canvasPosition = axis._offset + guide;
            const leftLimit = Math.ceil(height * Math.SQRT1_2 + 4 - canvasPosition);
            const rightLimit = Math.floor(plot._fullLayout.width - canvasPosition - width * Math.SQRT1_2 - 4);
            labels.push({annotation, index, width, height, guide, leftLimit, rightLimit});
        });

        const updates = {};
        const placed = [];
        let topMargin = 60;
        // Work from right to left so labels stay in the same order as their guides.
        for (const guideLabel of labels.sort((left, right) => right.guide - left.guide)) {
            const label = placeLabel(guideLabel, placed);
            placed.push(label);

            const labelHeight = (label.width + label.height) * Math.SQRT1_2;
            topMargin = Math.max(topMargin, Math.ceil(label.rise + labelHeight + 24));
            if (label.annotation.ax !== label.shift) updates[`annotations[${label.index}].ax`] = label.shift;
            if (label.annotation.ay !== -label.rise) updates[`annotations[${label.index}].ay`] = -label.rise;
        }

        if (plot.layout.margin?.t !== topMargin) updates["margin.t"] = topMargin;
        if (Object.keys(updates).length) {
            window.Plotly.relayout(plot, updates).catch(error => {
                if (plot.isConnected) console.warn("Could not position Rosetta size labels", error);
            });
        }
    }

    function schedulePlacement(plot) {
        if (pendingPlots.has(plot)) return;
        pendingPlots.add(plot);
        requestAnimationFrame(() => {
            pendingPlots.delete(plot);
            placeLabels(plot);
        });
    }

    function observePlots() {
        for (const plot of document.querySelectorAll(".js-plotly-plot")) {
            if (observedPlots.has(plot) || typeof plot.on !== "function" ||
                !plot.layout?.annotations?.some(annotation => annotation.name === labelName)) continue;
            observedPlots.add(plot);
            plot.on("plotly_afterplot", () => schedulePlacement(plot));
            schedulePlacement(plot);
        }
    }

    const observer = new MutationObserver(observePlots);
    observer.observe(document.documentElement, {childList: true, subtree: true});
    observePlots();
})();
