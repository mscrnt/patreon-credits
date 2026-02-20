(function () {
    "use strict";

    var csInterface = new CSInterface();
    var API_BASE = "http://localhost:8787";

    // ---- DOM refs ----
    var statusDot = document.getElementById("statusDot");
    var statusText = document.getElementById("statusText");
    var projectInfo = document.getElementById("projectInfo");
    var statusBar = document.getElementById("statusBar");
    var generateBtn = document.getElementById("generateBtn");
    var refreshBtn = document.getElementById("refreshBtn");
    var addTimelineBtn = document.getElementById("addTimelineBtn");

    var lastVideoFilename = null;
    var lastVideoUrl = null;
    var videoListEl = document.getElementById("videoList");
    var videoListEmpty = document.getElementById("videoListEmpty");
    var videoCountEl = document.getElementById("videoCount");
    var refreshVideosBtn = document.getElementById("refreshVideosBtn");

    // ---- Server connection ----
    function checkServer() {
        fetch(API_BASE + "/check-ffmpeg")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                statusDot.className = "status-dot connected";
                statusText.textContent = "Connected" + (data.installed ? " (FFmpeg OK)" : " (FFmpeg missing!)");
            })
            .catch(function () {
                statusDot.className = "status-dot disconnected";
                statusText.textContent = "Server offline - start python app.py";
            });
    }

    // ---- Premiere info ----
    function updateProjectInfo() {
        csInterface.evalScript("getProjectName()", function (name) {
            var text = name ? "Project: " + name : "No project open";
            csInterface.evalScript("getActiveSequenceName()", function (seq) {
                if (seq) text += " | Sequence: " + seq;
                projectInfo.textContent = text;
            });
        });
    }

    // ---- Status helpers ----
    function showStatus(msg, type) {
        statusBar.textContent = msg;
        statusBar.className = "status-bar " + (type || "info");
    }

    function hideStatus() {
        statusBar.className = "status-bar";
    }

    // ---- Collect form values ----
    function getFormData() {
        return {
            message: document.getElementById("message").value.trim(),
            custom_names: (document.getElementById("customNames") || {}).value || "",
            duration: parseInt(document.getElementById("duration").value, 10),
            resolution: document.getElementById("resolution").value,
            columns: parseInt(document.getElementById("columns").value, 10),
            name_align: document.getElementById("nameAlign").value,
            truncate_length: parseInt(document.getElementById("truncateLength").value, 10) || 0,
            word_wrap: document.getElementById("wordWrap").checked,
            name_spacing: document.getElementById("nameSpacing").checked,
            bg_color: document.getElementById("bgColor").value,
            use_cache: document.getElementById("useCache").checked,
            message_style: {
                size: parseInt(document.getElementById("messageSize").value, 10),
                color: document.getElementById("messageColor").value,
                font: document.getElementById("messageFont").value,
                bold: document.getElementById("messageBold").checked,
                align: document.getElementById("messageAlign").value
            },
            patron_style: {
                size: parseInt(document.getElementById("patronSize").value, 10),
                color: document.getElementById("patronColor").value,
                font: document.getElementById("patronFont").value,
                bold: document.getElementById("patronBold").checked
            }
        };
    }

    // ---- Generate video ----
    generateBtn.addEventListener("click", function () {
        var data = getFormData();
        if (!data.message) {
            showStatus("Please enter a header message.", "error");
            return;
        }

        generateBtn.disabled = true;
        addTimelineBtn.style.display = "none";
        showStatus("Generating credits video...", "info");

        fetch(API_BASE + "/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        })
        .then(function (r) { return r.json(); })
        .then(function (result) {
            if (result.error) {
                showStatus("Error: " + result.error, "error");
                generateBtn.disabled = false;
                return;
            }
            lastVideoFilename = result.filename;
            lastVideoUrl = API_BASE + result.video_url;
            showStatus("Video generated! " + result.patron_count + " patrons.", "success");
            addTimelineBtn.style.display = "block";
            generateBtn.disabled = false;
            loadVideoList();
        })
        .catch(function (err) {
            showStatus("Failed to connect: " + err.message, "error");
            generateBtn.disabled = false;
        });
    });

    // ---- Download & add to timeline ----
    addTimelineBtn.addEventListener("click", function () {
        if (!lastVideoUrl || !lastVideoFilename) return;

        addTimelineBtn.disabled = true;
        showStatus("Downloading and importing...", "info");

        // Download the video to a temp path via the API
        var downloadUrl = API_BASE + "/download/" + lastVideoFilename;

        // Use Premiere's temp folder
        var tempDir = csInterface.getSystemPath(SystemPath.USER_DATA);
        var destPath = tempDir + "/patreon_credits_" + lastVideoFilename;
        // Normalize path separators for Windows
        destPath = destPath.replace(/\//g, "\\");

        // Use XMLHttpRequest to download binary data and write to file via ExtendScript
        var xhr = new XMLHttpRequest();
        xhr.open("GET", downloadUrl, true);
        xhr.responseType = "blob";
        xhr.onload = function () {
            if (xhr.status !== 200) {
                showStatus("Download failed: HTTP " + xhr.status, "error");
                addTimelineBtn.disabled = false;
                return;
            }

            // Read blob as data URL, then save via Node.js (CEF) fs
            var reader = new FileReader();
            reader.onload = function () {
                var base64 = reader.result.split(",")[1];
                saveAndImport(base64, destPath);
            };
            reader.readAsDataURL(xhr.response);
        };
        xhr.onerror = function () {
            showStatus("Download failed.", "error");
            addTimelineBtn.disabled = false;
        };
        xhr.send();
    });

    function saveAndImport(base64Data, destPath) {
        // Use Node.js fs module available in CEP to write the file
        try {
            var buffer = Buffer.from(base64Data, "base64");
            var fs = require("fs");
            fs.writeFileSync(destPath, buffer);

            // Now tell Premiere to import and add to timeline
            var escaped = destPath.replace(/\\/g, "\\\\");
            csInterface.evalScript('importAndAddToTimeline("' + escaped + '")', function (result) {
                if (result.indexOf("ERROR:") === 0) {
                    showStatus(result, "error");
                } else {
                    showStatus(result.replace("OK: ", ""), "success");
                    updateProjectInfo();
                }
                addTimelineBtn.disabled = false;
            });
        } catch (e) {
            showStatus("File save failed: " + e.message, "error");
            addTimelineBtn.disabled = false;
        }
    }

    // ---- Refresh patrons ----
    refreshBtn.addEventListener("click", function () {
        refreshBtn.disabled = true;
        showStatus("Refreshing patron list...", "info");

        fetch(API_BASE + "/refresh-patrons", { method: "POST" })
            .then(function (r) { return r.json(); })
            .then(function (result) {
                if (result.error) {
                    showStatus("Error: " + result.error, "error");
                } else {
                    showStatus("Patron list refreshed: " + result.count + " patrons.", "success");
                }
                refreshBtn.disabled = false;
            })
            .catch(function (err) {
                showStatus("Failed to connect: " + err.message, "error");
                refreshBtn.disabled = false;
            });
    });

    // ---- File upload for custom names ----
    var namesFileInput = document.getElementById("namesFileInput");
    if (namesFileInput) {
        namesFileInput.addEventListener("change", function (e) {
            var file = e.target.files[0];
            if (!file) return;
            var reader = new FileReader();
            reader.onload = function () {
                var text = reader.result;
                if (file.name.match(/\.csv$/i)) {
                    var names = text.split(/[\r\n]+/)
                        .reduce(function (acc, line) { return acc.concat(line.split(",")); }, [])
                        .map(function (n) { return n.trim().replace(/^["']|["']$/g, ""); })
                        .filter(Boolean);
                    text = names.join("\n");
                }
                var ta = document.getElementById("customNames");
                ta.value = ta.value ? ta.value.trimEnd() + "\n" + text.trim() : text.trim();
            };
            reader.readAsText(file);
            e.target.value = "";
        });
    }

    // ---- Video history ----
    function formatBytes(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / 1048576).toFixed(1) + " MB";
    }

    function formatDate(isoStr) {
        try {
            var d = new Date(isoStr);
            return d.toLocaleDateString(undefined, {
                month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
            });
        } catch (_) { return isoStr; }
    }

    function loadVideoList() {
        fetch(API_BASE + "/api/videos")
            .then(function (r) { return r.json(); })
            .then(function (data) {
                var videos = data.videos || [];
                if (videoCountEl) videoCountEl.textContent = videos.length ? "(" + videos.length + ")" : "";

                if (videos.length === 0) {
                    if (videoListEmpty) videoListEmpty.style.display = "block";
                    // Clear any existing items but keep the empty message
                    var items = videoListEl.querySelectorAll(".video-item");
                    for (var i = 0; i < items.length; i++) items[i].remove();
                    return;
                }

                if (videoListEmpty) videoListEmpty.style.display = "none";
                // Clear and rebuild
                var items = videoListEl.querySelectorAll(".video-item");
                for (var i = 0; i < items.length; i++) items[i].remove();

                videos.forEach(function (v) {
                    var row = document.createElement("div");
                    row.className = "video-item";
                    row.innerHTML =
                        '<div class="video-item-info">' +
                            '<span class="video-item-name" title="' + v.filename + '">' + v.filename + '</span>' +
                            '<span class="video-item-meta">' + formatDate(v.created) + ' · ' + formatBytes(v.size) + '</span>' +
                        '</div>' +
                        '<div class="video-item-actions">' +
                            '<button class="btn-icon btn-import" title="Import to timeline" data-filename="' + v.filename + '">&#9654;</button>' +
                            '<button class="btn-icon btn-delete" title="Delete" data-filename="' + v.filename + '">&#10005;</button>' +
                        '</div>';
                    videoListEl.appendChild(row);
                });
            })
            .catch(function () {});
    }

    // Delegate clicks on video list
    if (videoListEl) {
        videoListEl.addEventListener("click", function (e) {
            var btn = e.target.closest(".btn-icon");
            if (!btn) return;
            var filename = btn.dataset.filename;
            if (!filename) return;

            if (btn.classList.contains("btn-import")) {
                // Import this video to timeline
                lastVideoFilename = filename;
                lastVideoUrl = API_BASE + "/output/" + filename;
                addTimelineBtn.style.display = "block";
                showStatus("Selected: " + filename + " — click Import & Add to Timeline.", "info");
            } else if (btn.classList.contains("btn-delete")) {
                if (!confirm("Delete " + filename + "?")) return;
                fetch(API_BASE + "/api/videos/" + encodeURIComponent(filename), { method: "DELETE" })
                    .then(function (r) { return r.json(); })
                    .then(function (data) {
                        if (data.success) {
                            showStatus("Deleted " + filename, "success");
                            loadVideoList();
                        } else {
                            showStatus("Delete failed: " + (data.error || "Unknown error"), "error");
                        }
                    })
                    .catch(function () { showStatus("Delete failed.", "error"); });
            }
        });
    }

    if (refreshVideosBtn) {
        refreshVideosBtn.addEventListener("click", loadVideoList);
    }

    // ---- Init ----
    checkServer();
    updateProjectInfo();
    loadVideoList();
    // Recheck periodically
    setInterval(checkServer, 15000);
    setInterval(updateProjectInfo, 10000);

})();
