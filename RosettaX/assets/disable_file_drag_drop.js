// Block file drag-and-drop so uploads can only be selected via the file picker.
(function () {
    function isFileDrag(event) {
        var dataTransfer = event.dataTransfer;

        if (!dataTransfer || !dataTransfer.types) {
            return false;
        }

        return Array.prototype.indexOf.call(dataTransfer.types, "Files") !== -1;
    }

    function preventFileDrop(event) {
        if (!isFileDrag(event)) {
            return;
        }

        event.preventDefault();
        event.stopPropagation();

        if (event.dataTransfer) {
            event.dataTransfer.dropEffect = "none";
        }
    }

    window.addEventListener("dragenter", preventFileDrop, true);
    window.addEventListener("dragover", preventFileDrop, true);
    window.addEventListener("drop", preventFileDrop, true);
})();
