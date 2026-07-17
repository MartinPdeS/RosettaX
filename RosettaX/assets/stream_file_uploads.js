(function () {
    "use strict";

    var UPLOAD_SELECTOR = ".rosettax-stream-upload";
    var ERROR_PREFIX = "rosettax-upload-error://";

    function setUploadProps(uploadId, properties) {
        if (
            window.dash_clientside &&
            typeof window.dash_clientside.set_props === "function"
        ) {
            window.dash_clientside.set_props(uploadId, properties);
            return true;
        }

        return false;
    }

    function findOrCreateProgress(uploadRoot) {
        var progress = uploadRoot.querySelector(".rosettax-stream-upload-progress");
        if (progress) {
            return progress;
        }

        progress = document.createElement("div");
        progress.className = "rosettax-stream-upload-progress";
        progress.style.fontSize = "0.82rem";
        progress.style.marginTop = "6px";
        progress.style.opacity = "0.78";
        uploadRoot.appendChild(progress);
        return progress;
    }

    function uploadFile(file, progress, fileIndex, fileCount) {
        return new Promise(function (resolve, reject) {
            var request = new XMLHttpRequest();
            request.open("POST", "/api/uploads/stream", true);
            request.setRequestHeader(
                "X-RosettaX-Filename",
                encodeURIComponent(file.name)
            );
            request.setRequestHeader("Content-Type", "application/octet-stream");

            request.upload.addEventListener("progress", function (event) {
                if (!event.lengthComputable) {
                    progress.textContent = "Uploading " + file.name + "…";
                    return;
                }

                var percentage = Math.round((event.loaded / event.total) * 100);
                var prefix = fileCount > 1
                    ? "File " + fileIndex + " of " + fileCount + ": "
                    : "";
                progress.textContent = prefix + file.name + " — " + percentage + "%";
            });

            request.addEventListener("load", function () {
                var payload = {};
                try {
                    payload = JSON.parse(request.responseText || "{}");
                } catch (_error) {
                    payload = {};
                }

                if (request.status < 200 || request.status >= 300 || !payload.token) {
                    reject(new Error(payload.error || "The server rejected the upload."));
                    return;
                }

                resolve(payload);
            });
            request.addEventListener("error", function () {
                reject(new Error("The upload connection failed."));
            });
            request.addEventListener("abort", function () {
                reject(new Error("The upload was cancelled."));
            });
            request.send(file);
        });
    }

    async function streamSelectedFiles(input, uploadRoot) {
        var files = Array.prototype.slice.call(input.files || []);
        if (!files.length || uploadRoot.dataset.rosettaxUploading === "true") {
            return;
        }

        uploadRoot.dataset.rosettaxUploading = "true";
        var progress = findOrCreateProgress(uploadRoot);
        var uploaded = [];

        try {
            for (var index = 0; index < files.length; index += 1) {
                uploaded.push(
                    await uploadFile(files[index], progress, index + 1, files.length)
                );
            }

            var multiple = Boolean(input.multiple);
            var contents = uploaded.map(function (item) { return item.token; });
            var filenames = uploaded.map(function (item) { return item.filename; });

            if (!setUploadProps(uploadRoot.id, {
                contents: multiple ? contents : contents[0],
                filename: multiple ? filenames : filenames[0]
            })) {
                throw new Error("Dash upload bridge is unavailable.");
            }

            progress.textContent = uploaded.length === 1
                ? "Upload complete."
                : uploaded.length + " uploads complete.";
        } catch (error) {
            var message = error && error.message ? error.message : "Upload failed.";
            var errorToken = ERROR_PREFIX + message;
            setUploadProps(uploadRoot.id, {
                contents: input.multiple
                    ? files.map(function () { return errorToken; })
                    : errorToken,
                filename: input.multiple
                    ? files.map(function (file) { return file.name; })
                    : files[0].name
            });
            progress.textContent = message;
        } finally {
            uploadRoot.dataset.rosettaxUploading = "false";
            input.value = "";
        }
    }

    window.addEventListener("change", function (event) {
        var input = event.target;
        if (!input || input.tagName !== "INPUT" || input.type !== "file") {
            return;
        }

        var uploadRoot = input.closest(UPLOAD_SELECTOR);
        if (!uploadRoot || !uploadRoot.id) {
            return;
        }

        event.preventDefault();
        event.stopImmediatePropagation();
        streamSelectedFiles(input, uploadRoot);
    }, true);
})();
