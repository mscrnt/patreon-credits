/**
 * ExtendScript for Adobe Premiere Pro — Patreon Credits Generator
 *
 * Called from the CEP panel via csInterface.evalScript().
 */

/**
 * Import a video file into the current Premiere Pro project.
 * Returns the import path on success, or an error string prefixed with "ERROR:".
 */
function importVideo(filePath) {
    try {
        var proj = app.project;
        if (!proj) return "ERROR: No project open.";

        var success = proj.importFiles([filePath], true);
        if (!success) return "ERROR: Import failed for " + filePath;

        return filePath;
    } catch (e) {
        return "ERROR: " + e.message;
    }
}

/**
 * Import a video file and insert it at the end of the active sequence.
 * Creates a new sequence if none exists.
 * Returns a status message.
 */
function importAndAddToTimeline(filePath) {
    try {
        var proj = app.project;
        if (!proj) return "ERROR: No project open.";

        // Import the file
        var success = proj.importFiles([filePath], true);
        if (!success) return "ERROR: Import failed for " + filePath;

        // Find the imported item (most recently added root item)
        var rootItem = proj.rootItem;
        var importedItem = null;
        for (var i = rootItem.children.numItems - 1; i >= 0; i--) {
            var child = rootItem.children[i];
            if (child.getMediaPath && child.getMediaPath() === filePath) {
                importedItem = child;
                break;
            }
        }

        if (!importedItem) {
            // Fallback: take the last item added
            if (rootItem.children.numItems > 0) {
                importedItem = rootItem.children[rootItem.children.numItems - 1];
            } else {
                return "ERROR: Could not find imported item in project.";
            }
        }

        // Get or create a sequence
        var seq = proj.activeSequence;
        if (!seq) {
            // Create a new sequence from the clip
            proj.createNewSequenceFromClips("Patreon Credits", [importedItem]);
            return "OK: Created new sequence with credits video.";
        }

        // Insert at the end of video track 0
        var videoTrack = seq.videoTracks[0];
        if (!videoTrack) return "ERROR: No video tracks in sequence.";

        var endTime = seq.end;
        videoTrack.insertClip(importedItem, endTime);

        return "OK: Added credits to end of timeline.";
    } catch (e) {
        return "ERROR: " + e.message;
    }
}

/**
 * Get the active sequence name, or empty string if none.
 */
function getActiveSequenceName() {
    try {
        var seq = app.project.activeSequence;
        if (seq) return seq.name;
        return "";
    } catch (e) {
        return "";
    }
}

/**
 * Get the project name.
 */
function getProjectName() {
    try {
        if (app.project) return app.project.name;
        return "";
    } catch (e) {
        return "";
    }
}
