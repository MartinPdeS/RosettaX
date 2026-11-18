document.addEventListener("click", (event) => {
    const stepCard = event.target.closest("[data-target-section]");
    if (!stepCard) {
        return;
    }

    window.setTimeout(() => {
        document
            .getElementById(stepCard.dataset.targetSection)
            ?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 150);
});
