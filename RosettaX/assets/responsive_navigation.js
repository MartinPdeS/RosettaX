(() => {
    const narrowViewport = window.matchMedia("(max-width: 991px)");

    function synchronizeNavigation() {
        const navigation = document.querySelector(".rosettax-navigation");
        if (!navigation || navigation.dataset.responsiveReady) return;
        navigation.dataset.responsiveReady = "true";
        observer.disconnect();

        const updateViewport = () => { navigation.open = !narrowViewport.matches; };
        updateViewport();
        narrowViewport.addEventListener("change", updateViewport);
        navigation.addEventListener("click", (event) => {
            if (narrowViewport.matches && event.target.closest("a[href]")) {
                navigation.open = false;
            }
        });
    }

    const observer = new MutationObserver(synchronizeNavigation);
    observer.observe(document.documentElement, {childList: true, subtree: true});
    synchronizeNavigation();
})();
