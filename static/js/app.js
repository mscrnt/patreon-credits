/* Patreon Credits Generator — Main App JS */
(function () {
  'use strict';

  // Font family mapping (backend key -> CSS font-family)
  var fontFamilyMap = {
    noto_sans: "'Noto Sans', sans-serif",
    noto_serif_cjk: "'Noto Serif SC', serif",
    lxgw_wenkai: "'LXGW WenKai', cursive",
    zen_maru_gothic: "'Zen Maru Gothic', sans-serif",
    mplus_rounded: "'M PLUS Rounded 1c', sans-serif",
    shippori_mincho: "'Shippori Mincho', serif",
    bpmf_huninn: "'Bpmf Huninn', sans-serif",
    inter: "'Inter', sans-serif",
    saira: "'Saira', sans-serif",
    roboto: "'Roboto', sans-serif",
    open_sans: "'Open Sans', sans-serif",
    poppins: "'Poppins', sans-serif",
    montserrat: "'Montserrat', sans-serif",
    raleway: "'Raleway', sans-serif",
    quicksand: "'Quicksand', sans-serif",
    source_sans: "'Source Sans 3', sans-serif",
    lato: "'Lato', sans-serif",
    nunito: "'Nunito', sans-serif",
    rubik: "'Rubik', sans-serif",
    dm_sans: "'DM Sans', sans-serif",
    josefin_sans: "'Josefin Sans', sans-serif",
    ubuntu: "'Ubuntu', sans-serif",
    oswald: "'Oswald', sans-serif",
    bebas_neue: "'Bebas Neue', sans-serif",
    cinzel: "'Cinzel', serif",
    playfair_display: "'Playfair Display', serif",
    merriweather: "'Merriweather', serif",
    crimson_text: "'Crimson Text', serif",
    lora: "'Lora', serif",
    libre_baskerville: "'Libre Baskerville', serif",
    arvo: "'Arvo', serif",
    neuton: "'Neuton', serif",
    alfa_slab_one: "'Alfa Slab One', serif",
    bangers: "'Bangers', system-ui",
    bowlby_one_sc: "'Bowlby One SC', system-ui",
    bungee: "'Bungee', system-ui",
    carter_one: "'Carter One', system-ui",
    chango: "'Chango', system-ui",
    creepster: "'Creepster', system-ui",
    erica_one: "'Erica One', system-ui",
    lobster_two: "'Lobster Two', cursive",
    luckiest_guy: "'Luckiest Guy', system-ui",
    amatic_sc: "'Amatic SC', cursive",
    caveat: "'Caveat', cursive",
    indie_flower: "'Indie Flower', cursive",
    permanent_marker: "'Permanent Marker', cursive",
    pacifico: "'Pacifico', cursive",
    playwrite: "'Playwrite DE Grund', cursive",
  };

  // Expose for other modules
  window.PCG = window.PCG || {};
  window.PCG.fontFamilyMap = fontFamilyMap;

  // ---- localStorage persistence ----
  var STORAGE_KEY = 'patreon_credits_settings';

  var persistFields = [
    { id: 'message', type: 'value' },
    { id: 'customNames', type: 'value' },
    { id: 'messageSize', type: 'value' },
    { id: 'messageColor', type: 'value' },
    { id: 'messageFont', type: 'value' },
    { id: 'messageBold', type: 'checked' },
    { id: 'messageAlign', type: 'value' },
    { id: 'patronSize', type: 'value' },
    { id: 'patronColor', type: 'value' },
    { id: 'patronFont', type: 'value' },
    { id: 'patronBold', type: 'checked' },
    { id: 'duration', type: 'value' },
    { id: 'resolution', type: 'value' },
    { id: 'fps', type: 'value' },
    { id: 'columns', type: 'value' },
    { id: 'nameAlign', type: 'value' },
    { id: 'truncateLength', type: 'value' },
    { id: 'wordWrap', type: 'checked' },
    { id: 'nameSpacing', type: 'checked' },
    { id: 'bgColor', type: 'value' },
    // Effects fields (Phase 2)
    { id: 'fadeIn', type: 'value' },
    { id: 'fadeOut', type: 'value' },
    { id: 'speedMultiplier', type: 'value' },
    { id: 'bgType', type: 'value' },
    { id: 'bgGradientColor1', type: 'value' },
    { id: 'bgGradientColor2', type: 'value' },
    { id: 'bgGradientDirection', type: 'value' },
    { id: 'logoPosition', type: 'value' },
    { id: 'logoSize', type: 'value' },
    { id: 'qrUrl', type: 'value' },
    { id: 'qrPosition', type: 'value' },
    { id: 'qrSize', type: 'value' },
    { id: 'audioVolume', type: 'value' },
    // Integration credentials (Settings tab)
    { id: 'settingsBmcToken', type: 'value' },
    { id: 'settingsSeJwt', type: 'value' },
    { id: 'settingsSeChannelId', type: 'value' },
    { id: 'settingsKofiVerifyToken', type: 'value' },
    { id: 'settingsYtClientId', type: 'value' },
    { id: 'settingsYtClientSecret', type: 'value' },
    // Name source checkboxes
    { id: 'nsPatreonCheck', type: 'checked' },
    { id: 'nsBmcCheck', type: 'checked' },
    { id: 'nsSeCheck', type: 'checked' },
    { id: 'nsKofiCheck', type: 'checked' },
    { id: 'nsYtCheck', type: 'checked' },
    // Asset library (persisted upload filenames)
    { id: 'bgImageFilename', type: 'value' },
    { id: 'audioFilename', type: 'value' },
    { id: 'logoFilename', type: 'value' },
    // Logging settings
    { id: 'logLevel', type: 'value' },
    { id: 'logMaxSize', type: 'value' },
    { id: 'logBackupCount', type: 'value' },
  ];

  function _collectSettings() {
    var settings = {};
    persistFields.forEach(function (f) {
      var el = document.getElementById(f.id);
      if (el) settings[f.id] = f.type === 'checked' ? el.checked : el.value;
    });
    return settings;
  }

  function _applySettings(settings) {
    if (!settings) return;
    persistFields.forEach(function (f) {
      if (settings[f.id] === undefined) return;
      var el = document.getElementById(f.id);
      if (!el) return;
      if (f.type === 'checked') el.checked = settings[f.id];
      else el.value = settings[f.id];
    });
  }

  var _saveTimer = null;
  function saveSettings() {
    var settings = _collectSettings();
    // Always save to localStorage as fast cache
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    // Debounce server saves to avoid flooding
    clearTimeout(_saveTimer);
    _saveTimer = setTimeout(function () {
      fetch('/api/generate-settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      }).catch(function () { /* server save failed, localStorage has it */ });
    }, 500);
  }

  function loadSettings() {
    // First apply localStorage for instant restore
    var raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      try { _applySettings(JSON.parse(raw)); } catch (_) {}
    }
    // Then try server for authoritative values
    fetch('/api/generate-settings', { headers: { Accept: 'application/json' } })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data && Object.keys(data).length > 0) {
          _applySettings(data);
          // Sync localStorage with server values
          localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
          // Re-sync font previews with server values
          updateFontPreview('messageFontPreview', 'messageFont', 'messageBold', 'messageColor');
          updateFontPreview('patronFontPreview', 'patronFont', 'patronBold', 'patronColor');
        }
      })
      .catch(function () { /* server unavailable, localStorage is fine */ });
  }

  // Expose for other modules (presets need to load/save)
  window.PCG.saveSettings = saveSettings;
  window.PCG.loadSettings = loadSettings;
  window.PCG.applySettings = _applySettings;
  window.PCG.collectSettings = _collectSettings;

  // ---- Live font preview updaters ----
  function updateFontPreview(previewId, fontSelectId, boldCheckboxId, colorInputId) {
    var preview = document.getElementById(previewId);
    if (!preview) return;
    var fontVal = document.getElementById(fontSelectId).value;
    var bold = document.getElementById(boldCheckboxId).checked;
    preview.style.fontFamily = fontFamilyMap[fontVal] || 'sans-serif';
    preview.style.fontWeight = bold ? 'bold' : 'normal';
    if (colorInputId) {
      preview.style.color = document.getElementById(colorInputId).value;
    }
  }

  // ---- FFmpeg helpers ----
  function checkFFmpeg() {
    var ffmpegStatus = document.getElementById('ffmpegStatus');
    var installBtn = document.getElementById('installFfmpegBtn');
    if (!ffmpegStatus) return;
    fetch('/check-ffmpeg')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.installed) {
          ffmpegStatus.textContent = 'Installed';
          ffmpegStatus.className = 'badge bg-success';
        } else {
          ffmpegStatus.textContent = 'Not Found';
          ffmpegStatus.className = 'badge bg-danger';
          if (installBtn) installBtn.classList.remove('d-none');
        }
      })
      .catch(function () {
        ffmpegStatus.textContent = 'Error';
        ffmpegStatus.className = 'badge bg-danger';
      });
  }

  function installFfmpeg() {
    var btn = document.getElementById('installFfmpegBtn');
    var ffmpegStatus = document.getElementById('ffmpegStatus');
    if (!btn) return;
    btn.disabled = true;
    btn.textContent = 'Installing...';
    ffmpegStatus.textContent = 'Downloading...';
    ffmpegStatus.className = 'badge bg-warning text-dark';

    fetch('/install-ffmpeg', { method: 'POST' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          ffmpegStatus.textContent = 'Installed';
          ffmpegStatus.className = 'badge bg-success';
          btn.classList.add('d-none');
        } else {
          ffmpegStatus.textContent = 'Failed';
          ffmpegStatus.className = 'badge bg-danger';
          btn.textContent = 'Retry';
          btn.disabled = false;
        }
      })
      .catch(function () {
        ffmpegStatus.textContent = 'Failed';
        ffmpegStatus.className = 'badge bg-danger';
        btn.textContent = 'Retry';
        btn.disabled = false;
      });
  }

  function updatePatronCount() {
    var el = document.getElementById('patreonNameCount');
    if (!el) return;
    fetch('/patron-count')
      .then(function (r) { return r.json(); })
      .then(function (data) { el.textContent = data.count || '0'; })
      .catch(function () { el.textContent = 'Error'; });
  }

  // ---- UI helpers ----
  function showError(message) {
    var el = document.getElementById('errorMessage');
    if (!el) return;
    el.textContent = message;
    el.classList.remove('d-none');
    setTimeout(function () { el.classList.add('d-none'); }, 5000);
  }

  function showStatus(message) {
    var sec = document.getElementById('statusSection');
    var txt = document.getElementById('statusText');
    if (!sec || !txt) return;
    txt.textContent = message;
    sec.classList.remove('d-none');
  }

  function hideStatus() {
    var sec = document.getElementById('statusSection');
    if (sec) sec.classList.add('d-none');
  }

  // ---- Init on DOMContentLoaded ----
  document.addEventListener('DOMContentLoaded', function () {
    var form = document.getElementById('creditsForm');
    var generateBtn = document.getElementById('generateBtn');
    var refreshBtn = document.getElementById('refreshBtn');
    var videoPlayer = document.getElementById('videoPlayer');
    var downloadBtn = document.getElementById('downloadBtn');
    var openFolderBtn = document.getElementById('openFolderBtn');
    var previewModalEl = document.getElementById('videoPreviewModal');
    var previewModal = previewModalEl ? bootstrap.Modal.getOrCreateInstance(previewModalEl) : null;

    // Not on generate tab — bail
    if (!form) return;

    // Restore settings
    loadSettings();

    // Bind persistence listeners
    persistFields.forEach(function (f) {
      var el = document.getElementById(f.id);
      if (!el) return;
      el.addEventListener('change', saveSettings);
      if (el.type === 'color' || el.tagName === 'TEXTAREA') {
        el.addEventListener('input', saveSettings);
      }
    });

    // Font preview bindings
    ['messageFont', 'messageBold', 'messageColor'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener(id === 'messageColor' ? 'input' : 'change', function () {
        updateFontPreview('messageFontPreview', 'messageFont', 'messageBold', 'messageColor');
      });
    });
    ['patronFont', 'patronBold', 'patronColor'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener(id === 'patronColor' ? 'input' : 'change', function () {
        updateFontPreview('patronFontPreview', 'patronFont', 'patronBold', 'patronColor');
      });
    });

    // Sync previews with restored values
    updateFontPreview('messageFontPreview', 'messageFont', 'messageBold', 'messageColor');
    updateFontPreview('patronFontPreview', 'patronFont', 'patronBold', 'patronColor');

    // Restore uploaded asset selections from persisted filenames
    if (window.PCG && window.PCG.restoreAssetSelections) {
      window.PCG.restoreAssetSelections();
    }

    // FFmpeg & patron count
    checkFFmpeg();
    updatePatronCount();

    // Install FFmpeg button
    var installBtn = document.getElementById('installFfmpegBtn');
    if (installBtn) installBtn.addEventListener('click', installFfmpeg);

    // ---- Form submit ----
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var message = document.getElementById('message').value.trim();
      var customNames = document.getElementById('customNames').value.trim();
      var duration = parseInt(document.getElementById('duration').value);
      var resolution = document.getElementById('resolution').value;
      var columns = parseInt(document.getElementById('columns').value);
      var nameAlign = document.getElementById('nameAlign').value;
      var truncateLength = parseInt(document.getElementById('truncateLength').value) || 0;
      var wordWrap = document.getElementById('wordWrap').checked;
      var nameSpacing = document.getElementById('nameSpacing').checked;
      var bgColor = document.getElementById('bgColor').value;
      var messageStyle = {
        size: parseInt(document.getElementById('messageSize').value),
        color: document.getElementById('messageColor').value,
        font: document.getElementById('messageFont').value,
        bold: document.getElementById('messageBold').checked,
        align: document.getElementById('messageAlign').value,
      };
      var patronStyle = {
        size: parseInt(document.getElementById('patronSize').value),
        color: document.getElementById('patronColor').value,
        font: document.getElementById('patronFont').value,
        bold: document.getElementById('patronBold').checked,
      };

      if (!message) { showError('Please enter a message'); return; }

      generateBtn.disabled = true;
      showStatus('Generating credits video...');

      // Collect effects data if available
      var effects = (window.PCG && window.PCG.collectEffects) ? window.PCG.collectEffects() : {};

      var payload = {
        message: message,
        custom_names: customNames,
        duration: duration,
        resolution: resolution,
        columns: columns,
        name_align: nameAlign,
        truncate_length: truncateLength,
        word_wrap: wordWrap,
        name_spacing: nameSpacing,
        bg_color: bgColor,
        message_style: messageStyle,
        patron_style: patronStyle,
      };
      // Merge effects into payload
      for (var k in effects) { payload[k] = effects[k]; }

      fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
        .then(function (resp) {
          return resp.json().then(function (data) {
            if (!resp.ok) throw new Error(data.error || 'Failed to generate video');
            return data;
          });
        })
        .then(function (data) {
          hideStatus();
          videoPlayer.src = data.video_url;
          downloadBtn.dataset.filename = data.filename;
          var pcBadge = document.getElementById('patreonNameCount');
          if (pcBadge) pcBadge.textContent = data.patron_count;
          if (previewModal) previewModal.show();
          // Notify gallery
          document.dispatchEvent(new CustomEvent('videoGenerated'));
        })
        .catch(function (err) {
          showError(err.message);
          hideStatus();
        })
        .finally(function () {
          generateBtn.disabled = false;
        });
    });

    // ---- File upload (.txt/.csv) ----
    var namesFileInput = document.getElementById('namesFileInput');
    if (namesFileInput) {
      namesFileInput.addEventListener('change', function (e) {
        var file = e.target.files[0];
        if (!file) return;
        var reader = new FileReader();
        reader.onload = function () {
          var text = reader.result;
          if (file.name.endsWith('.csv')) {
            var names = text.split(/[\r\n]+/)
              .flatMap(function (line) { return line.split(','); })
              .map(function (n) { return n.trim().replace(/^["']|["']$/g, ''); })
              .filter(Boolean);
            text = names.join('\n');
          }
          var ta = document.getElementById('customNames');
          ta.value = ta.value ? ta.value.trimEnd() + '\n' + text.trim() : text.trim();
          saveSettings();
        };
        reader.readAsText(file);
        e.target.value = '';
      });
    }

    // ---- Desktop mode (pywebview) ----
    var isDesktop = false;
    function applyDesktopMode() {
      if (window.pywebview) {
        isDesktop = true;
        if (downloadBtn) downloadBtn.classList.add('d-none');
        if (openFolderBtn) openFolderBtn.classList.remove('d-none');
      }
    }
    applyDesktopMode();
    window.addEventListener('pywebviewready', applyDesktopMode);
    setTimeout(applyDesktopMode, 500);

    // Pause video when preview modal closes
    if (previewModalEl) {
      previewModalEl.addEventListener('hidden.bs.modal', function () {
        if (videoPlayer) { videoPlayer.pause(); }
      });
    }

    // ---- Download handler ----
    if (downloadBtn) {
      downloadBtn.addEventListener('click', function (e) {
        e.preventDefault();
        var filename = downloadBtn.dataset.filename;
        if (!filename) return;
        fetch('/download/' + filename)
          .then(function (resp) {
            if (!resp.ok) throw new Error('Download failed');
            return resp.blob();
          })
          .then(function (blob) {
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'patreon_credits_' + filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
          })
          .catch(function (err) { showError(err.message); });
      });
    }

    // ---- Open folder handler ----
    if (openFolderBtn) {
      openFolderBtn.addEventListener('click', function (e) {
        e.preventDefault();
        fetch('/open-output-folder', { method: 'POST' })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (!data.success) showError(data.error || 'Failed to open folder');
          })
          .catch(function (err) { showError(err.message); });
      });
    }

    // ---- Refresh patrons ----
    if (refreshBtn) {
      refreshBtn.addEventListener('click', function () {
        refreshBtn.disabled = true;
        showStatus('Refreshing patron list...');
        fetch('/refresh-patrons', { method: 'POST' })
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (data.error) {
              showError('Error: ' + data.error);
            } else {
              showStatus('Patron list refreshed: ' + data.count + ' patrons.');
              var pcBadge = document.getElementById('patreonNameCount');
              if (pcBadge) pcBadge.textContent = data.count;
              setTimeout(hideStatus, 2000);
            }
          })
          .catch(function () {
            showError('Failed to refresh patron list');
            hideStatus();
          })
          .finally(function () {
            refreshBtn.disabled = false;
          });
      });
    }

    // ---- Collapsible card headers — toggle .collapsed class for chevron rotation ----
    document.querySelectorAll('.card-header[data-bs-toggle="collapse"]').forEach(function (header) {
      var target = document.querySelector(header.dataset.bsTarget);
      if (!target) return;
      target.addEventListener('show.bs.collapse', function () {
        header.classList.remove('collapsed');
        header.setAttribute('aria-expanded', 'true');
      });
      target.addEventListener('hide.bs.collapse', function () {
        header.classList.add('collapsed');
        header.setAttribute('aria-expanded', 'false');
      });
    });

    // ---- Font Picker Modal ----
    (function () {
      var fontPickerModal = document.getElementById('fontPickerModal');
      if (!fontPickerModal) return;

      var grid = document.getElementById('fontGrid');
      var search = document.getElementById('fontSearch');
      var preview = document.getElementById('fontModalPreview');
      var applyBtn = document.getElementById('fontPickerApply');
      var targetLabel = document.getElementById('fontPickerTarget');
      var currentTarget = 'message'; // 'message' or 'patron'
      var selectedFont = '';

      // Build font list from the hidden select options
      var fontList = [];
      var messageSelect = document.getElementById('messageFont');
      if (messageSelect) {
        Array.prototype.slice.call(messageSelect.options).forEach(function (opt) {
          fontList.push({ value: opt.value, label: opt.textContent, family: fontFamilyMap[opt.value] || 'sans-serif' });
        });
      }

      function renderGrid(filter) {
        grid.innerHTML = '';
        var lowerFilter = (filter || '').toLowerCase();
        fontList.forEach(function (f) {
          if (lowerFilter && f.label.toLowerCase().indexOf(lowerFilter) === -1) return;
          var col = document.createElement('div');
          col.className = 'col';
          var card = document.createElement('div');
          card.className = 'font-card p-2 text-center' + (f.value === selectedFont ? ' selected' : '');
          card.dataset.font = f.value;
          card.innerHTML = '<div class="font-sample" style="font-family:' + f.family + ';">AaBbCcDd 123</div>' +
            '<small class="font-name text-body-secondary">' + f.label + '</small>';
          card.addEventListener('click', function () {
            grid.querySelectorAll('.font-card').forEach(function (c) { c.classList.remove('selected'); });
            card.classList.add('selected');
            selectedFont = f.value;
            preview.style.fontFamily = f.family;
          });
          col.appendChild(card);
          grid.appendChild(col);
        });
      }

      // On modal show — read which font target triggered it
      fontPickerModal.addEventListener('show.bs.modal', function (event) {
        var trigger = event.relatedTarget;
        if (trigger && trigger.dataset.targetFont) {
          currentTarget = trigger.dataset.targetFont;
        }
        targetLabel.textContent = currentTarget === 'message' ? 'Message' : 'Names';
        var selectEl = document.getElementById(currentTarget + 'Font');
        selectedFont = selectEl ? selectEl.value : 'noto_sans';
        search.value = '';
        renderGrid('');
        preview.style.fontFamily = fontFamilyMap[selectedFont] || 'sans-serif';
      });

      // Search filter
      if (search) {
        search.addEventListener('input', function () {
          renderGrid(search.value);
        });
      }

      // Apply selection
      if (applyBtn) {
        applyBtn.addEventListener('click', function () {
          if (!selectedFont) return;
          var selectEl = document.getElementById(currentTarget + 'Font');
          var badgeEl = document.getElementById(currentTarget + 'FontLabel');
          if (selectEl) {
            selectEl.value = selectedFont;
            selectEl.dispatchEvent(new Event('change'));
          }
          if (badgeEl) {
            // Find display label
            var match = fontList.find(function (f) { return f.value === selectedFont; });
            badgeEl.textContent = match ? match.label : selectedFont;
          }
          // Update font preview
          var previewId = currentTarget + 'FontPreview';
          var boldId = currentTarget + 'Bold';
          var colorId = currentTarget === 'message' ? 'messageColor' : 'patronColor';
          updateFontPreview(previewId, currentTarget + 'Font', boldId, colorId);
          saveSettings();
          bootstrap.Modal.getInstance(fontPickerModal).hide();
        });
      }
    })();

    // ---- Sync font badge labels on load ----
    function syncFontBadge(target) {
      var selectEl = document.getElementById(target + 'Font');
      var badgeEl = document.getElementById(target + 'FontLabel');
      if (selectEl && badgeEl) {
        var opt = selectEl.options[selectEl.selectedIndex];
        if (opt) badgeEl.textContent = opt.textContent;
      }
    }
    syncFontBadge('message');
    syncFontBadge('patron');
  });
})();
