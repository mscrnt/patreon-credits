/* Patreon Credits Generator — Presets */
(function () {
  'use strict';

  function loadPresetList() {
    var select = document.getElementById('presetSelect');
    var deleteBtn = document.getElementById('presetDeleteBtn');
    if (!select) return;

    fetch('/api/presets')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var presets = data.presets || [];
        // Clear all options except the placeholder
        while (select.options.length > 1) select.remove(1);

        presets.forEach(function (p) {
          var opt = document.createElement('option');
          opt.value = p.name;
          opt.textContent = p.name;
          select.appendChild(opt);
        });

        // Reset to placeholder
        select.selectedIndex = 0;
        if (deleteBtn) deleteBtn.classList.add('d-none');
      })
      .catch(function () {});
  }

  function savePreset() {
    var nameInput = document.getElementById('presetName');
    var msg = document.getElementById('presetSaveMsg');
    var name = (nameInput ? nameInput.value.trim() : '');
    if (!name) {
      showMsg(msg, 'Enter a name.', 'danger');
      return;
    }

    var config = {};
    if (window.PCG && window.PCG.collectSettings) {
      config = window.PCG.collectSettings();
    }
    if (window.PCG && window.PCG.collectEffects) {
      var effects = window.PCG.collectEffects();
      for (var k in effects) { config['_fx_' + k] = effects[k]; }
    }

    fetch('/api/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, config: config }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          showMsg(msg, 'Saved!', 'success');
          nameInput.value = '';
          loadPresetList();
        } else {
          showMsg(msg, data.error || 'Failed.', 'danger');
        }
      })
      .catch(function (e) { showMsg(msg, 'Error: ' + e.message, 'danger'); });
  }

  function loadPreset(name) {
    if (!name) return;
    fetch('/api/presets/' + encodeURIComponent(name))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.config) return;
        if (window.PCG && window.PCG.applySettings) {
          window.PCG.applySettings(data.config);
        }
        if (window.PCG && window.PCG.saveSettings) {
          window.PCG.saveSettings();
        }
      })
      .catch(function () {});
  }

  function deletePreset(name) {
    if (!name || !confirm('Delete preset "' + name + '"?')) return;
    fetch('/api/presets/' + encodeURIComponent(name), { method: 'DELETE' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) loadPresetList();
      })
      .catch(function () {});
  }

  // ---- Quick export preset buttons ----
  function bindExportPresets() {
    document.querySelectorAll('.export-preset').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var resolution = btn.dataset.resolution;
        var resolutionEl = document.getElementById('resolution');
        if (resolutionEl && resolution) {
          resolutionEl.value = resolution;
          if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();
        }
      });
    });
  }

  // ---- Helpers ----
  function showMsg(el, text, type) {
    if (!el) return;
    el.className = 'alert alert-' + type + ' d-inline-block py-1 px-2 mb-0 small';
    el.textContent = text;
    setTimeout(function () { el.className = 'alert d-none py-1 px-2 mb-0 small'; }, 3000);
  }

  // ---- Init ----
  document.addEventListener('DOMContentLoaded', function () {
    var select = document.getElementById('presetSelect');
    if (!select) return;

    var deleteBtn = document.getElementById('presetDeleteBtn');

    // Load preset on select change
    select.addEventListener('change', function () {
      var name = select.value;
      if (name) {
        loadPreset(name);
        if (deleteBtn) deleteBtn.classList.remove('d-none');
      }
    });

    // Delete button
    if (deleteBtn) {
      deleteBtn.addEventListener('click', function () {
        var name = select.value;
        if (name) deletePreset(name);
      });
    }

    var saveBtn = document.getElementById('presetSaveBtn');
    if (saveBtn) saveBtn.addEventListener('click', savePreset);

    bindExportPresets();
    loadPresetList();
  });
})();
