/* Patreon Credits Generator — Integrations (Name Sources) */
(function () {
  'use strict';

  // ---- StreamElements ----
  function fetchStreamElements() {
    var jwt = (document.getElementById('settingsSeJwt') || {}).value;
    var channelId = (document.getElementById('settingsSeChannelId') || {}).value;
    var msg = document.getElementById('seMsg');
    var badge = document.getElementById('seNameCount');
    if (!jwt || !channelId) { showMsg(msg, 'Set JWT & Channel ID in Settings → Integrations.', 'danger'); return; }

    var btn = document.getElementById('seFetchBtn');
    if (btn) { btn.disabled = true; }

    fetch('/api/integrations/streamelements/fetch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ jwt: jwt, channel_id: channelId }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) {
          showMsg(msg, data.error, 'danger');
        } else {
          var names = data.names || [];
          if (badge) badge.textContent = names.length;
          var settingsBadge = document.getElementById('settingsSeCount');
          if (settingsBadge) settingsBadge.textContent = names.length;
          showMsg(msg, names.length + ' tippers', 'success');
          appendNames(names);
        }
      })
      .catch(function (e) { showMsg(msg, 'Error: ' + e.message, 'danger'); })
      .finally(function () {
        if (btn) { btn.disabled = false; }
      });
  }

  // ---- StreamElements (stored names) ----
  function loadSeNames() {
    var badge = document.getElementById('seNameCount');
    fetch('/api/integrations/se/names')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var names = data.names || [];
        if (badge) badge.textContent = names.length;
      })
      .catch(function () {});
  }

  // ---- Buy Me a Coffee (webhook) ----
  function loadBmcNames() {
    var badge = document.getElementById('bmcNameCount');
    fetch('/api/integrations/bmc/names')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var names = data.names || [];
        if (badge) badge.textContent = names.length;
      })
      .catch(function () {});
  }

  // ---- Ko-fi (webhook) ----
  function loadKofiNames() {
    var badge = document.getElementById('kofiNameCount');
    fetch('/api/integrations/kofi/names')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var names = data.names || [];
        if (badge) badge.textContent = names.length;
      })
      .catch(function () {});
  }

  // ---- YouTube Members ----
  function fetchYouTubeMembers() {
    var msg = document.getElementById('ytMsg');
    var badge = document.getElementById('ytNameCount');
    var btn = document.getElementById('ytFetchBtn');
    if (btn) btn.disabled = true;

    fetch('/api/integrations/youtube/fetch', { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.error) {
          showMsg(msg, data.error, 'danger');
        } else {
          var names = data.names || [];
          if (badge) badge.textContent = names.length;
          showMsg(msg, names.length + ' members', 'success');
          appendNames(names);
        }
      })
      .catch(function (e) { showMsg(msg, 'Error: ' + e.message, 'danger'); })
      .finally(function () { if (btn) btn.disabled = false; });
  }

  // ---- Helpers ----
  function appendNames(names) {
    if (!names || !names.length) return;
    var ta = document.getElementById('customNames');
    if (!ta) return;
    var existing = ta.value.trim();
    var newText = names.join('\n');
    ta.value = existing ? existing + '\n' + newText : newText;
    if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();
  }

  function showMsg(el, text, type) {
    if (!el) return;
    el.className = 'alert alert-' + type + ' mt-0 mb-0 py-1 px-2 small';
    el.textContent = text;
    if (type !== 'info') {
      setTimeout(function () { el.className = 'alert d-none mt-0 mb-0 py-1 px-2 small'; }, 5000);
    }
  }

  // ---- Init ----
  document.addEventListener('DOMContentLoaded', function () {
    var seBtn = document.getElementById('seFetchBtn');
    if (seBtn) seBtn.addEventListener('click', fetchStreamElements);

    var ytFetchBtn = document.getElementById('ytFetchBtn');
    if (ytFetchBtn) ytFetchBtn.addEventListener('click', fetchYouTubeMembers);

    // Settings-link buttons (gear icon → open Settings → Integrations → sub-tab)
    document.querySelectorAll('.ns-settings-link').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var intTab = btn.getAttribute('data-int-tab');
        // 1. Switch to Settings main tab
        var settingsTab = document.querySelector('[data-bs-target="#settings-tab-pane"]');
        if (settingsTab) new bootstrap.Tab(settingsTab).show();
        // 2. Switch to Integrations sub-tab within Settings
        var intPane = document.querySelector('[data-bs-target="#settings-integrations-pane"]');
        if (intPane) new bootstrap.Tab(intPane).show();
        // 3. Switch to the specific integration pill
        if (intTab) {
          var pill = document.querySelector('[data-bs-target="' + intTab + '"]');
          if (pill) new bootstrap.Tab(pill).show();
        }
      });
    });

    loadSeNames();
    loadBmcNames();
    loadKofiNames();
  });
})();
