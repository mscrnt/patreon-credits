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

  // ---- Ko-fi settings ----
  function setupKofiSettings() {
    var settingsKofiUrl = document.getElementById('settingsKofiWebhookUrl');
    if (settingsKofiUrl) settingsKofiUrl.value = window.location.origin + '/webhooks/kofi';

    var settingsKofiCopyBtn = document.getElementById('settingsKofiCopyBtn');
    if (settingsKofiCopyBtn && settingsKofiUrl) {
      settingsKofiCopyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(settingsKofiUrl.value).then(function () {
          settingsKofiCopyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
          setTimeout(function () { settingsKofiCopyBtn.innerHTML = '<i class="fa-solid fa-copy"></i>'; }, 1500);
        });
      });
    }

    loadKofiSchedule();

    // Clear button
    var clearBtn = document.getElementById('settingsKofiClearBtn');
    var clearDays = document.getElementById('settingsKofiClearDays');
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        var count = document.getElementById('settingsKofiCount');
        var n = count ? count.textContent : '0';
        if (n === '0') {
          showKofiMsg('No names to clear.', 'info');
          return;
        }
        var days = clearDays ? clearDays.value : '';
        var msg = days
          ? 'Clear names older than ' + days + ' days?'
          : 'Clear all ' + n + ' stored Ko-fi names?';
        if (!confirm(msg)) return;

        clearBtn.disabled = true;
        var body = days ? JSON.stringify({ days: parseInt(days) }) : '{}';
        fetch('/api/integrations/kofi/clear', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body,
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.success) {
              if (days) {
                var removed = data.removed || 0;
                showKofiMsg(removed + ' name(s) removed.', 'success');
                loadKofiSchedule();
              } else {
                if (count) count.textContent = '0';
                var contentBadge = document.getElementById('kofiNameCount');
                if (contentBadge) contentBadge.textContent = '0';
                showKofiMsg('All names cleared.', 'success');
              }
            } else {
              showKofiMsg(data.error || 'Failed to clear.', 'danger');
            }
          })
          .catch(function (e) { showKofiMsg('Error: ' + e.message, 'danger'); })
          .finally(function () { clearBtn.disabled = false; });
      });
    }

    // Schedule dropdown
    var scheduleSelect = document.getElementById('settingsKofiSchedule');
    var customWrap = document.getElementById('settingsKofiCustomDaysWrap');
    var customDays = document.getElementById('settingsKofiCustomDays');

    if (scheduleSelect) {
      scheduleSelect.addEventListener('change', function () {
        if (scheduleSelect.value === 'custom') {
          if (customWrap) customWrap.classList.remove('d-none');
        } else {
          if (customWrap) customWrap.classList.add('d-none');
          saveKofiSchedule(scheduleSelect.value);
        }
      });
    }
    if (customDays) {
      customDays.addEventListener('change', function () {
        var days = parseInt(customDays.value);
        if (days && days > 0) saveKofiSchedule(days);
      });
    }
  }

  function loadKofiSchedule() {
    fetch('/api/integrations/kofi/schedule')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var count = document.getElementById('settingsKofiCount');
        if (count) count.textContent = data.count || 0;

        var select = document.getElementById('settingsKofiSchedule');
        var customWrap = document.getElementById('settingsKofiCustomDaysWrap');
        var customDays = document.getElementById('settingsKofiCustomDays');
        var info = document.getElementById('settingsKofiScheduleInfo');

        if (select) {
          var schedule = data.auto_clear || 'never';
          if (typeof schedule === 'number') {
            select.value = 'custom';
            if (customWrap) customWrap.classList.remove('d-none');
            if (customDays) customDays.value = schedule;
          } else {
            select.value = schedule;
            if (customWrap) customWrap.classList.add('d-none');
          }
        }

        if (info && data.last_cleared) {
          var d = new Date(data.last_cleared + 'Z');
          info.textContent = 'Last cleared: ' + d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
        } else if (info) {
          info.textContent = '';
        }

        var contentBadge = document.getElementById('kofiNameCount');
        if (contentBadge) contentBadge.textContent = data.count || 0;
      })
      .catch(function () {});
  }

  function saveKofiSchedule(schedule) {
    fetch('/api/integrations/kofi/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ schedule: schedule }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          showKofiMsg('Schedule updated.', 'success');
        } else {
          showKofiMsg(data.error || 'Failed to save schedule.', 'danger');
        }
      })
      .catch(function (e) { showKofiMsg('Error: ' + e.message, 'danger'); });
  }

  function showKofiMsg(text, type) {
    var el = document.getElementById('settingsKofiMsg');
    if (!el) return;
    el.className = 'alert alert-' + type + ' mt-1 mb-3 py-1 px-2 small';
    el.textContent = text;
    setTimeout(function () { el.className = 'alert d-none mt-1 mb-3 py-1 px-2 small'; }, 4000);
  }

  // ---- BMC webhook settings ----
  function setupBmcSettings() {
    var bmcUrl = document.getElementById('settingsBmcWebhookUrl');
    if (bmcUrl) bmcUrl.value = window.location.origin + '/webhooks/bmc';

    var bmcCopyBtn = document.getElementById('settingsBmcCopyBtn');
    if (bmcCopyBtn && bmcUrl) {
      bmcCopyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(bmcUrl.value).then(function () {
          bmcCopyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
          setTimeout(function () { bmcCopyBtn.innerHTML = '<i class="fa-solid fa-copy"></i>'; }, 1500);
        });
      });
    }

    loadBmcSchedule();

    // Clear button
    var clearBtn = document.getElementById('settingsBmcClearBtn');
    var clearDays = document.getElementById('settingsBmcClearDays');
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        var count = document.getElementById('settingsBmcCount');
        var n = count ? count.textContent : '0';
        if (n === '0') {
          showBmcMsg('No names to clear.', 'info');
          return;
        }
        var days = clearDays ? clearDays.value : '';
        var msg = days
          ? 'Clear names older than ' + days + ' days?'
          : 'Clear all ' + n + ' stored BMC names?';
        if (!confirm(msg)) return;

        clearBtn.disabled = true;
        var body = days ? JSON.stringify({ days: parseInt(days) }) : '{}';
        fetch('/api/integrations/bmc/clear', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body,
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.success) {
              if (days) {
                showBmcMsg((data.removed || 0) + ' name(s) removed.', 'success');
                loadBmcSchedule();
              } else {
                if (count) count.textContent = '0';
                var contentBadge = document.getElementById('bmcWebhookCount');
                if (contentBadge) contentBadge.textContent = '0';
                showBmcMsg('All names cleared.', 'success');
              }
            } else {
              showBmcMsg(data.error || 'Failed to clear.', 'danger');
            }
          })
          .catch(function (e) { showBmcMsg('Error: ' + e.message, 'danger'); })
          .finally(function () { clearBtn.disabled = false; });
      });
    }

    // Schedule dropdown
    var scheduleSelect = document.getElementById('settingsBmcSchedule');
    var customWrap = document.getElementById('settingsBmcCustomDaysWrap');
    var customDays = document.getElementById('settingsBmcCustomDays');

    if (scheduleSelect) {
      scheduleSelect.addEventListener('change', function () {
        if (scheduleSelect.value === 'custom') {
          if (customWrap) customWrap.classList.remove('d-none');
        } else {
          if (customWrap) customWrap.classList.add('d-none');
          saveBmcSchedule(scheduleSelect.value);
        }
      });
    }
    if (customDays) {
      customDays.addEventListener('change', function () {
        var days = parseInt(customDays.value);
        if (days && days > 0) saveBmcSchedule(days);
      });
    }
  }

  function loadBmcSchedule() {
    fetch('/api/integrations/bmc/schedule')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var count = document.getElementById('settingsBmcCount');
        if (count) count.textContent = data.count || 0;

        var select = document.getElementById('settingsBmcSchedule');
        var customWrap = document.getElementById('settingsBmcCustomDaysWrap');
        var customDays = document.getElementById('settingsBmcCustomDays');
        var info = document.getElementById('settingsBmcScheduleInfo');

        if (select) {
          var schedule = data.auto_clear || 'never';
          if (typeof schedule === 'number') {
            select.value = 'custom';
            if (customWrap) customWrap.classList.remove('d-none');
            if (customDays) customDays.value = schedule;
          } else {
            select.value = schedule;
            if (customWrap) customWrap.classList.add('d-none');
          }
        }

        if (info && data.last_cleared) {
          var d = new Date(data.last_cleared + 'Z');
          info.textContent = 'Last cleared: ' + d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
        } else if (info) {
          info.textContent = '';
        }

        var contentBadge = document.getElementById('bmcWebhookCount');
        if (contentBadge) contentBadge.textContent = data.count || 0;
      })
      .catch(function () {});
  }

  function saveBmcSchedule(schedule) {
    fetch('/api/integrations/bmc/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ schedule: schedule }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          showBmcMsg('Schedule updated.', 'success');
        } else {
          showBmcMsg(data.error || 'Failed to save schedule.', 'danger');
        }
      })
      .catch(function (e) { showBmcMsg('Error: ' + e.message, 'danger'); });
  }

  function showBmcMsg(text, type) {
    var el = document.getElementById('settingsBmcMsg');
    if (!el) return;
    el.className = 'alert alert-' + type + ' mt-1 mb-3 py-1 px-2 small';
    el.textContent = text;
    setTimeout(function () { el.className = 'alert d-none mt-1 mb-3 py-1 px-2 small'; }, 4000);
  }

  // ---- StreamElements settings ----
  function setupSeSettings() {
    loadSeSchedule();

    // Clear button
    var clearBtn = document.getElementById('settingsSeClearBtn');
    var clearDays = document.getElementById('settingsSeClearDays');
    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        var count = document.getElementById('settingsSeCount');
        var n = count ? count.textContent : '0';
        if (n === '0') {
          showSeMsg('No names to clear.', 'info');
          return;
        }
        var days = clearDays ? clearDays.value : '';
        var msg = days
          ? 'Clear names older than ' + days + ' days?'
          : 'Clear all ' + n + ' stored SE names?';
        if (!confirm(msg)) return;

        clearBtn.disabled = true;
        var body = days ? JSON.stringify({ days: parseInt(days) }) : '{}';
        fetch('/api/integrations/se/clear', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: body,
        })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.success) {
              if (days) {
                var removed = data.removed || 0;
                showSeMsg(removed + ' name(s) removed.', 'success');
                loadSeSchedule();
              } else {
                if (count) count.textContent = '0';
                var contentBadge = document.getElementById('seNameCount');
                if (contentBadge) contentBadge.textContent = '0';
                showSeMsg('All names cleared.', 'success');
              }
            } else {
              showSeMsg(data.error || 'Failed to clear.', 'danger');
            }
          })
          .catch(function (e) { showSeMsg('Error: ' + e.message, 'danger'); })
          .finally(function () { clearBtn.disabled = false; });
      });
    }

    // Schedule dropdown
    var scheduleSelect = document.getElementById('settingsSeSchedule');
    var customWrap = document.getElementById('settingsSeCustomDaysWrap');
    var customDays = document.getElementById('settingsSeCustomDays');

    if (scheduleSelect) {
      scheduleSelect.addEventListener('change', function () {
        if (scheduleSelect.value === 'custom') {
          if (customWrap) customWrap.classList.remove('d-none');
        } else {
          if (customWrap) customWrap.classList.add('d-none');
          saveSeSchedule(scheduleSelect.value);
        }
      });
    }
    if (customDays) {
      customDays.addEventListener('change', function () {
        var days = parseInt(customDays.value);
        if (days && days > 0) saveSeSchedule(days);
      });
    }
  }

  function loadSeSchedule() {
    fetch('/api/integrations/se/schedule')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var count = document.getElementById('settingsSeCount');
        if (count) count.textContent = data.count || 0;

        var select = document.getElementById('settingsSeSchedule');
        var customWrap = document.getElementById('settingsSeCustomDaysWrap');
        var customDays = document.getElementById('settingsSeCustomDays');
        var info = document.getElementById('settingsSeScheduleInfo');

        if (select) {
          var schedule = data.auto_clear || 'never';
          if (typeof schedule === 'number') {
            select.value = 'custom';
            if (customWrap) customWrap.classList.remove('d-none');
            if (customDays) customDays.value = schedule;
          } else {
            select.value = schedule;
            if (customWrap) customWrap.classList.add('d-none');
          }
        }

        if (info && data.last_cleared) {
          var d = new Date(data.last_cleared + 'Z');
          info.textContent = 'Last cleared: ' + d.toLocaleDateString() + ' ' + d.toLocaleTimeString();
        } else if (info) {
          info.textContent = '';
        }

        var contentBadge = document.getElementById('seNameCount');
        if (contentBadge) contentBadge.textContent = data.count || 0;
      })
      .catch(function () {});
  }

  function saveSeSchedule(schedule) {
    fetch('/api/integrations/se/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ schedule: schedule }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          showSeMsg('Schedule updated.', 'success');
        } else {
          showSeMsg(data.error || 'Failed to save schedule.', 'danger');
        }
      })
      .catch(function (e) { showSeMsg('Error: ' + e.message, 'danger'); });
  }

  function showSeMsg(text, type) {
    var el = document.getElementById('settingsSeMsg');
    if (!el) return;
    el.className = 'alert alert-' + type + ' mt-1 mb-3 py-1 px-2 small';
    el.textContent = text;
    setTimeout(function () { el.className = 'alert d-none mt-1 mb-3 py-1 px-2 small'; }, 4000);
  }

  // ---- YouTube settings ----
  function setupYoutubeSettings() {
    // Redirect URI display + copy
    var redirectUri = document.getElementById('settingsYtRedirectUri');
    if (redirectUri) redirectUri.value = window.location.origin + '/oauth/youtube/callback';

    var copyBtn = document.getElementById('settingsYtCopyRedirect');
    if (copyBtn && redirectUri) {
      copyBtn.addEventListener('click', function () {
        navigator.clipboard.writeText(redirectUri.value).then(function () {
          copyBtn.innerHTML = '<i class="fa-solid fa-check"></i>';
          setTimeout(function () { copyBtn.innerHTML = '<i class="fa-solid fa-copy"></i>'; }, 1500);
        });
      });
    }

    // Revoke button
    var revokeBtn = document.getElementById('settingsYtRevokeBtn');
    if (revokeBtn) {
      revokeBtn.addEventListener('click', function () {
        if (!confirm('Revoke YouTube authorization?')) return;
        fetch('/api/integrations/youtube/revoke', { method: 'POST' })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.success) {
              showYtMsg('Authorization revoked.', 'success');
              loadYoutubeStatus();
            }
          })
          .catch(function (e) { showYtMsg('Error: ' + e.message, 'danger'); });
      });
    }

    loadYoutubeStatus();
  }

  function loadYoutubeStatus() {
    fetch('/api/integrations/youtube/status')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var badge = document.getElementById('settingsYtStatusBadge');
        var revokeBtn = document.getElementById('settingsYtRevokeBtn');
        if (data.authorized) {
          if (badge) {
            badge.textContent = 'Authorized';
            badge.className = 'badge bg-success ms-1';
          }
          if (revokeBtn) revokeBtn.classList.remove('d-none');
        } else {
          if (badge) {
            badge.textContent = 'Not Authorized';
            badge.className = 'badge bg-secondary ms-1';
          }
          if (revokeBtn) revokeBtn.classList.add('d-none');
        }
      })
      .catch(function () {});
  }

  function showYtMsg(text, type) {
    var el = document.getElementById('settingsYtMsg');
    if (!el) return;
    el.className = 'alert alert-' + type + ' mt-2 mb-0 py-1 px-2 small';
    el.textContent = text;
    setTimeout(function () { el.className = 'alert d-none mt-2 mb-0 py-1 px-2 small'; }, 4000);
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

    // Integration webhook + store settings
    setupSeSettings();
    setupBmcSettings();
    setupKofiSettings();
    setupYoutubeSettings();

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
