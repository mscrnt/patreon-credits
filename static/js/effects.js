/* Patreon Credits Generator — Effects Sub-tab */
(function () {
  'use strict';

  // ---- Range slider value displays ----
  function bindRange(inputId, displayId, suffix) {
    var input = document.getElementById(inputId);
    var display = document.getElementById(displayId);
    if (!input || !display) return;
    function update() { display.textContent = input.value + suffix; }
    input.addEventListener('input', update);
    update();
  }

  // ---- Background type toggle ----
  function bindBgTypeToggle() {
    var radios = document.querySelectorAll('input[name="bgType"]');
    var solidOpts = document.getElementById('bgSolidOptions');
    var imageOpts = document.getElementById('bgImageOptions');
    var gradientOpts = document.getElementById('bgGradientOptions');
    if (!radios.length) return;

    function update() {
      var val = document.querySelector('input[name="bgType"]:checked').value;
      if (solidOpts) solidOpts.classList.toggle('d-none', val !== 'solid');
      if (imageOpts) imageOpts.classList.toggle('d-none', val !== 'image');
      if (gradientOpts) gradientOpts.classList.toggle('d-none', val !== 'gradient');
      // Save via global saveSettings
      if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();
    }
    radios.forEach(function (r) { r.addEventListener('change', update); });
    update();
  }

  // ---- File upload helpers ----
  // Map file input IDs to their hidden persistence input IDs
  var persistMap = {
    bgImageInput: 'bgImageFilename',
    audioFileInput: 'audioFilename',
    logoFileInput: 'logoFilename',
  };

  function bindFileUpload(inputId, displayId, clearBtnId, uploadEndpoint) {
    var input = document.getElementById(inputId);
    var display = document.getElementById(displayId);
    var clearBtn = document.getElementById(clearBtnId);
    var hiddenId = persistMap[inputId];
    if (!input) return;

    input.addEventListener('change', function (e) {
      var file = e.target.files[0];
      if (!file) return;
      if (display) display.textContent = file.name;
      if (clearBtn) clearBtn.classList.remove('d-none');

      // Upload to server
      var formData = new FormData();
      formData.append('file', file);
      fetch(uploadEndpoint, { method: 'POST', body: formData })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.filename) {
            input.dataset.uploadedFilename = data.filename;
            // Persist filename for restore across page loads
            var hidden = hiddenId ? document.getElementById(hiddenId) : null;
            if (hidden) hidden.value = data.filename;
            if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();
          }
        })
        .catch(function () {});
    });

    if (clearBtn) {
      clearBtn.addEventListener('click', function () {
        input.value = '';
        input.dataset.uploadedFilename = '';
        if (display) display.textContent = 'No file selected';
        clearBtn.classList.add('d-none');
        // Clear persisted filename
        var hidden = hiddenId ? document.getElementById(hiddenId) : null;
        if (hidden) hidden.value = '';
        if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();
      });
    }
  }

  // ---- QR preview ----
  function bindQrPreview() {
    var urlInput = document.getElementById('qrUrl');
    var preview = document.getElementById('qrPreview');
    if (!urlInput || !preview) return;

    var timer = null;
    urlInput.addEventListener('input', function () {
      clearTimeout(timer);
      var url = urlInput.value.trim();
      if (!url) {
        preview.classList.add('d-none');
        return;
      }
      timer = setTimeout(function () {
        preview.src = '/api/qr?url=' + encodeURIComponent(url) + '&size=120';
        preview.classList.remove('d-none');
      }, 500);
    });
  }

  // ---- Collect effects data for form submission ----
  window.PCG = window.PCG || {};
  window.PCG.collectEffects = function () {
    var bgType = 'solid';
    var checked = document.querySelector('input[name="bgType"]:checked');
    if (checked) bgType = checked.value;

    return {
      fps: parseInt((document.getElementById('fps') || {}).value) || 30,
      fade_in: parseFloat((document.getElementById('fadeIn') || {}).value) || 0,
      fade_out: parseFloat((document.getElementById('fadeOut') || {}).value) || 0,
      speed_multiplier: parseFloat((document.getElementById('speedMultiplier') || {}).value) || 1,
      bg_type: bgType,
      bg_gradient: bgType === 'gradient' ? {
        color1: (document.getElementById('bgGradientColor1') || {}).value || '#000033',
        color2: (document.getElementById('bgGradientColor2') || {}).value || '#000000',
        direction: (document.getElementById('bgGradientDirection') || {}).value || 'vertical',
      } : null,
      bg_image: bgType === 'image' ? ((document.getElementById('bgImageInput') || {}).dataset || {}).uploadedFilename || null : null,
      audio_file: ((document.getElementById('audioFileInput') || {}).dataset || {}).uploadedFilename || null,
      audio_volume: parseInt((document.getElementById('audioVolume') || {}).value) || 100,
      logo_file: ((document.getElementById('logoFileInput') || {}).dataset || {}).uploadedFilename || null,
      logo_position: (document.getElementById('logoPosition') || {}).value || 'top-right',
      logo_size: parseInt((document.getElementById('logoSize') || {}).value) || 80,
      qr_url: (document.getElementById('qrUrl') || {}).value || '',
      qr_position: (document.getElementById('qrPosition') || {}).value || 'bottom-right',
      qr_size: parseInt((document.getElementById('qrSize') || {}).value) || 120,
    };
  };

  // ---- Init ----
  document.addEventListener('DOMContentLoaded', function () {
    bindRange('fadeIn', 'fadeInVal', 's');
    bindRange('fadeOut', 'fadeOutVal', 's');
    bindRange('speedMultiplier', 'speedVal', 'x');
    bindRange('audioVolume', 'audioVolumeVal', '%');
    bindBgTypeToggle();

    bindFileUpload('bgImageInput', 'bgImageName', null, '/upload/image');
    bindFileUpload('audioFileInput', 'audioFileName', 'audioClearBtn', '/upload/audio');
    bindFileUpload('logoFileInput', 'logoFileName', 'logoClearBtn', '/upload/image');

    bindQrPreview();

    // Save on any form field change
    var formInputs = document.querySelectorAll(
      '#creditsForm input, #creditsForm select, #creditsForm textarea'
    );
    formInputs.forEach(function (el) {
      el.addEventListener('change', function () {
        if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();
      });
      if (el.type === 'range' || el.type === 'color') {
        el.addEventListener('input', function () {
          if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();
        });
      }
    });
  });
})();
