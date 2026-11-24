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

    const overlays = new WeakMap();
    const svgNamespace = "http://www.w3.org/2000/svg";
    const guideSelector = "[data-peak-guides]";

    function addSvg(parent, type, attributes, text) {
        const element = document.createElementNS(svgNamespace, type);
        for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
        if (text !== undefined) element.textContent = text;
        parent.append(element);
        return element;
    }

    function placeLabels(plot) {
        const state = overlays.get(plot);
        const layout = plot._fullLayout;
        const xAxis = layout?.xaxis;
        const yAxis = layout?.yaxis;
        if (!state || !xAxis || !yAxis || !plot.isConnected) return;

        const svg = state.svg;
        const surface = plot.querySelector(".plot-container > .svg-container");
        if (!surface) return;
        if (svg.parentNode !== surface) surface.append(svg);
        svg.replaceChildren();
        let guides;
        try {
            guides = JSON.parse(state.container.dataset.peakGuides);
        } catch (_) {
            return;
        }
        svg.style.width = `${layout.width}px`;
        svg.style.height = `${layout.height}px`;
        svg.setAttribute("viewBox", `0 0 ${layout.width} ${layout.height}`);
        const left = xAxis._offset, right = left + xAxis._length;
        const top = yAxis._offset, bottom = top + yAxis._length;
        const button = state.highlight;
        if (button?.isConnected && button.closest("details")?.open && state.revision === layout.uirevision) {
            const position = Number(button.dataset.scatterPosition);
            const x = left + xAxis.d2p(position);
            if ((xAxis.type !== "log" || position > 0) && x >= left && x <= right) {
                addSvg(svg, "line", {
                    class: "rosetta-inspected-peak", x1: x, x2: x, y1: top, y2: bottom,
                    stroke: "#d97706", "stroke-width": 5, opacity: 0.8,
                });
            }
        }
        if (!guides || guides.revision !== layout.uirevision) return;
        const dashes = {dot: "2 4", dash: "7 5", dashdot: "7 4 2 4"};
        for (const shape of guides.lines) {
            const vertical = shape.xref === "x";
            const axis = vertical ? xAxis : yAxis;
            const offset = axis.d2p(vertical ? shape.x0 : shape.y0);
            if (!Number.isFinite(offset) || offset < 0 || offset > axis._length) continue;
            const position = axis._offset + offset;
            addSvg(svg, "line", {
                x1: vertical ? position : left, x2: vertical ? position : right,
                y1: vertical ? top : position, y2: vertical ? bottom : position,
                stroke: shape.line?.color ?? "#444", "stroke-width": shape.line?.width ?? 1,
                "stroke-dasharray": dashes[shape.line?.dash] ?? "",
            });
        }

        const labels = [];
        const labelGroup = addSvg(svg, "g", {class: "rosetta-size-label"});
        for (const annotation of guides.annotations) {
            const guide = left + xAxis.r2p(annotation.x);
            if (!Number.isFinite(guide) || guide < left || guide > right) continue;
            const color = annotation.font?.color ?? "#444";
            const text = addSvg(labelGroup, "text", {
                fill: color, "font-size": annotation.font?.size ?? 13,
            }, annotation.text);
            const {width, height} = text.getBBox();
            labels.push({text, color, guide, width, height,
                leftLimit: Math.ceil(height * Math.SQRT1_2 + 4 - guide),
                rightLimit: Math.floor(layout.width - guide - width * Math.SQRT1_2 - 4),
            });
        }
        const placed = [];
        for (const guideLabel of labels.sort((left, right) => right.guide - left.guide)) {
            const label = placeLabel(guideLabel, placed);
            placed.push(label);
            const y = Math.max(12, top - label.rise - 4);
            label.text.setAttribute("transform", `translate(${label.position}, ${y}) rotate(-45)`);
            addSvg(labelGroup, "line", {
                x1: label.guide, x2: label.position, y1: top, y2: y + 2,
                stroke: label.color, "stroke-width": 1,
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

    function bindOverlay(container) {
        const plot = container.querySelector(".js-plotly-plot");
        if (!plot || typeof plot.on !== "function") return;
        if (!observedPlots.has(plot)) {
            observedPlots.add(plot);
            const svg = document.createElementNS(svgNamespace, "svg");
            svg.setAttribute("class", "rosetta-guide-overlay");
            svg.setAttribute("aria-hidden", "true");
            overlays.set(plot, {svg, container});
            plot.on("plotly_afterplot", () => schedulePlacement(plot));
            plot.on("plotly_relayouting", () => schedulePlacement(plot));
        }
        schedulePlacement(plot);
    }

    function clearHighlight(plot) {
        const state = overlays.get(plot);
        if (!state?.highlight) return;
        clearTimeout(state.timer);
        state.highlight.setAttribute("aria-pressed", "false");
        state.highlight = null;
        schedulePlacement(plot);
    }

    document.addEventListener("click", event => {
        const workflow = event.target.closest(".peak-workflow");
        const plot = workflow?.querySelector(guideSelector + " .js-plotly-plot");
        const state = overlays.get(plot);
        if (!state) return;
        const button = event.target.closest("tr")?.querySelector("[data-scatter-position]");
        if (!button || !workflow.contains(button)) {
            if (event.target.closest("summary, .peak-action-button")) clearHighlight(plot);
            return;
        }
        const alreadySelected = state.highlight === button;
        clearHighlight(plot);
        if (alreadySelected) return;
        state.highlight = button;
        state.revision = plot._fullLayout?.uirevision;
        button.setAttribute("aria-pressed", "true");
        schedulePlacement(plot);
        const bounds = plot.getBoundingClientRect();
        if (bounds.top > window.innerHeight * 0.75 || bounds.bottom < 0) {
            plot.scrollIntoView({block: "center"});
        }
        state.timer = setTimeout(() => clearHighlight(plot), 6000);
    });

    const observer = new MutationObserver(records => {
        const containers = new Set();
        for (const record of records) {
            if (record.type === "attributes") {
                containers.add(record.target);
                continue;
            }
            for (const node of record.addedNodes) {
                if (!(node instanceof HTMLElement)) continue;
                const container = node.closest(guideSelector);
                if (container) containers.add(container);
                node.querySelectorAll(guideSelector).forEach(item => containers.add(item));
            }
        }
        containers.forEach(bindOverlay);
    });
    observer.observe(document.documentElement, {
        childList: true, subtree: true, attributes: true, attributeFilter: ["data-peak-guides"],
    });
    document.querySelectorAll(guideSelector).forEach(bindOverlay);
})();
