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
    inter: "'Inter', sans-serif",
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
    { id: 'columns', type: 'value' },
    { id: 'nameAlign', type: 'value' },
    { id: 'truncateLength', type: 'value' },
    { id: 'wordWrap', type: 'checked' },
    { id: 'nameSpacing', type: 'checked' },
    { id: 'bgColor', type: 'value' },
    { id: 'useCache', type: 'checked' },
  ];

  function saveSettings() {
    var settings = {};
    persistFields.forEach(function (f) {
      var el = document.getElementById(f.id);
      if (el) settings[f.id] = f.type === 'checked' ? el.checked : el.value;
    });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }

  function loadSettings() {
    var raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    try {
      var settings = JSON.parse(raw);
      persistFields.forEach(function (f) {
        if (settings[f.id] === undefined) return;
        var el = document.getElementById(f.id);
        if (!el) return;
        if (f.type === 'checked') el.checked = settings[f.id];
        else el.value = settings[f.id];
      });
    } catch (_) {
      /* ignore corrupt data */
    }
  }

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
    var el = document.getElementById('patronCount');
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
      var useCache = document.getElementById('useCache').checked;

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

      fetch('/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
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
          use_cache: useCache,
          message_style: messageStyle,
          patron_style: patronStyle,
        }),
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
          document.getElementById('patronCount').textContent = data.patron_count;
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
              document.getElementById('patronCount').textContent = data.count;
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
  });
})();
