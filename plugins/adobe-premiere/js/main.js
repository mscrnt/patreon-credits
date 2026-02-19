(function () {
    "use strict";

    var csInterface = new CSInterface();
    var API_BASE = "http://localhost:5000";

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

    // ---- Init ----
    checkServer();
    updateProjectInfo();
    // Recheck periodically
    setInterval(checkServer, 15000);
    setInterval(updateProjectInfo, 10000);

})();
