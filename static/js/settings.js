/* Patreon Credits Generator — Settings Tab */
(function () {
  'use strict';

  // ---- FFmpeg ----
  function checkFfmpeg() {
    var badge = document.getElementById('settingsFfmpegBadge');
    var okDiv = document.getElementById('settingsFfmpegOk');
    var missingDiv = document.getElementById('settingsFfmpegMissing');
    if (!badge) return;

    fetch('/check-ffmpeg')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.installed) {
          badge.textContent = 'Installed';
          badge.className = 'badge bg-success';
          if (okDiv) okDiv.classList.remove('d-none');
          if (missingDiv) missingDiv.classList.add('d-none');
        } else {
          badge.textContent = 'Not Found';
          badge.className = 'badge bg-danger';
          if (okDiv) okDiv.classList.add('d-none');
          if (missingDiv) missingDiv.classList.remove('d-none');
        }
      })
      .catch(function () {
        badge.textContent = 'Error';
        badge.className = 'badge bg-danger';
      });
  }

  function installFfmpeg() {
    var btn = document.getElementById('settingsInstallFfmpegBtn');
    var progress = document.getElementById('settingsFfmpegProgress');
    var fill = document.getElementById('settingsFfmpegProgressFill');
    var msg = document.getElementById('settingsFfmpegMsg');
    if (!btn) return;

    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Downloading...';
    if (progress) progress.classList.add('active');
    if (fill) fill.style.width = '30%';
    if (msg) { msg.className = 'alert d-none'; }

    fetch('/install-ffmpeg', { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (fill) fill.style.width = '100%';
        if (data.success) {
          if (msg) {
            msg.className = 'alert alert-success mt-2';
            msg.textContent = 'FFmpeg installed successfully!';
          }
          setTimeout(checkFfmpeg, 500);
        } else {
          if (msg) {
            msg.className = 'alert alert-danger mt-2';
            msg.textContent = data.error || 'Installation failed.';
          }
          btn.disabled = false;
          btn.textContent = 'Retry Download';
        }
      })
      .catch(function (e) {
        if (fill) fill.style.width = '0%';
        if (msg) {
          msg.className = 'alert alert-danger mt-2';
          msg.textContent = 'Network error: ' + e.message;
        }
        btn.disabled = false;
        btn.textContent = 'Retry Download';
      });
  }

  // ---- Campaign detection ----
  function detectCampaign() {
    var token = document.getElementById('settingsPatreonToken').value.trim();
    var msg = document.getElementById('settingsPatreonMsg');
    var btn = document.getElementById('settingsDetectBtn');
    if (!token) {
      if (msg) {
        msg.className = 'alert alert-danger mt-2';
        msg.textContent = 'Please enter your Patreon token first.';
      }
      return;
    }
    btn.disabled = true;
    btn.textContent = 'Detecting...';
    if (msg) msg.className = 'alert d-none';

    fetch('/detect-campaign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: token }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.campaign_id) {
          document.getElementById('settingsCampaignId').value = data.campaign_id;
          if (msg) {
            msg.className = 'alert alert-success mt-2';
            msg.textContent = 'Campaign detected: ' + data.campaign_id;
          }
        } else {
          if (msg) {
            msg.className = 'alert alert-danger mt-2';
            msg.textContent = data.error || 'Could not detect campaign.';
          }
        }
      })
      .catch(function (e) {
        if (msg) {
          msg.className = 'alert alert-danger mt-2';
          msg.textContent = 'Network error: ' + e.message;
        }
      })
      .finally(function () {
        btn.disabled = false;
        btn.textContent = 'Detect Campaign';
      });
  }

  // ---- Data directory ----
  function saveDataDir() {
    var msg = document.getElementById('settingsDataDirMsg');
    var path = document.getElementById('settingsDataDir').value.trim();
    if (!path) {
      if (msg) {
        msg.className = 'alert alert-danger mt-2';
        msg.textContent = 'Please enter a directory path.';
      }
      return;
    }
    fetch('/data-dir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: path }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          if (msg) {
            msg.className = 'alert alert-success mt-2';
            msg.textContent = 'Directory updated to: ' + data.path;
          }
        } else {
          if (msg) {
            msg.className = 'alert alert-danger mt-2';
            msg.textContent = data.error || 'Failed to set directory.';
          }
        }
      })
      .catch(function (e) {
        if (msg) {
          msg.className = 'alert alert-danger mt-2';
          msg.textContent = 'Error: ' + e.message;
        }
      });
  }

  // ---- Save credentials ----
  function saveCredentials() {
    var msg = document.getElementById('settingsSaveMsg');
    var payload = {
      patreon_token: document.getElementById('settingsPatreonToken').value.trim(),
      campaign_id: document.getElementById('settingsCampaignId').value.trim(),
      use_dummy_data: document.getElementById('settingsUseDummyData').checked,
    };

    fetch('/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          if (msg) {
            msg.className = 'alert alert-success mt-2';
            msg.textContent = 'Settings saved!';
          }
        } else {
          if (msg) {
            msg.className = 'alert alert-danger mt-2';
            msg.textContent = data.error || 'Failed to save.';
          }
        }
      })
      .catch(function (e) {
        if (msg) {
          msg.className = 'alert alert-danger mt-2';
          msg.textContent = 'Error: ' + e.message;
        }
      });
  }

  // ---- Load existing values ----
  function loadExisting() {
    fetch('/settings', { headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var tokenEl = document.getElementById('settingsPatreonToken');
        var campaignEl = document.getElementById('settingsCampaignId');
        var dummyEl = document.getElementById('settingsUseDummyData');
        if (data.patreon_token && tokenEl) tokenEl.value = data.patreon_token;
        if (data.campaign_id && campaignEl) campaignEl.value = data.campaign_id;
        if (data.use_dummy_data && dummyEl) dummyEl.checked = true;
      })
      .catch(function () {});

    fetch('/data-dir')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var el = document.getElementById('settingsDataDir');
        if (el) el.value = data.path || '';
      })
      .catch(function () {});
  }

  // ---- Init ----
  document.addEventListener('DOMContentLoaded', function () {
    // Only init if settings elements are present
    if (!document.getElementById('settingsFfmpegBadge')) return;

    // Show when settings tab is shown
    var settingsTab = document.querySelector('[data-bs-target="#settings-tab-pane"]');
    if (settingsTab) {
      settingsTab.addEventListener('shown.bs.tab', function () {
        checkFfmpeg();
        loadExisting();
      });
    }

    // Also load if we land directly on the settings tab (hash link)
    if (window.location.hash === '#settings-tab') {
      var tab = document.querySelector('[data-bs-target="#settings-tab-pane"]');
      if (tab) {
        var bsTab = new bootstrap.Tab(tab);
        bsTab.show();
      }
      checkFfmpeg();
      loadExisting();
    }

    // Server URL
    var serverUrl = document.getElementById('settingsServerUrl');
    if (serverUrl) serverUrl.value = window.location.origin;

    // Wire up buttons
    var installBtn = document.getElementById('settingsInstallFfmpegBtn');
    if (installBtn) installBtn.addEventListener('click', installFfmpeg);

    var detectBtn = document.getElementById('settingsDetectBtn');
    if (detectBtn) detectBtn.addEventListener('click', detectCampaign);

    var dataDirBtn = document.getElementById('settingsDataDirBtn');
    if (dataDirBtn) dataDirBtn.addEventListener('click', saveDataDir);

    var saveBtn = document.getElementById('settingsSaveBtn');
    if (saveBtn) saveBtn.addEventListener('click', saveCredentials);
  });
})();
