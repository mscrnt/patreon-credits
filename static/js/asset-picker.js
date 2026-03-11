/* Patreon Credits Generator — Asset Picker (Library) */
(function () {
  'use strict';

  // Target mapping: asset-target value -> { input, display, clear, hidden }
  var targetMap = {
    bgImage: { inputId: 'bgImageInput', displayId: 'bgImageName', clearId: null, hiddenId: 'bgImageFilename' },
    audio:   { inputId: 'audioFileInput', displayId: 'audioFileName', clearId: 'audioClearBtn', hiddenId: 'audioFilename' },
    logo:    { inputId: 'logoFileInput', displayId: 'logoFileName', clearId: 'logoClearBtn', hiddenId: 'logoFilename' },
  };

  var targetLabels = { bgImage: 'Background Image', audio: 'Background Music', logo: 'Logo' };

  var currentTarget = '';
  var currentType = '';
  var selectedAsset = '';

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function loadAssets(type) {
    var grid = document.getElementById('assetGrid');
    var empty = document.getElementById('assetEmpty');
    if (!grid) return;

    grid.innerHTML = '<div class="col-12 text-center py-4"><div class="spinner-border spinner-border-sm text-secondary" role="status"></div></div>';
    if (empty) empty.classList.add('d-none');

    fetch('/api/assets?type=' + encodeURIComponent(type))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var assets = data.assets || [];
        grid.innerHTML = '';
        selectedAsset = '';

        if (assets.length === 0) {
          if (empty) empty.classList.remove('d-none');
          return;
        }
        if (empty) empty.classList.add('d-none');

        assets.forEach(function (asset) {
          var col = document.createElement('div');
          col.className = 'col';

          var card = document.createElement('div');
          card.className = 'asset-card p-2 text-center';
          card.dataset.filename = asset.filename;

          // Thumbnail or icon
          var thumb;
          if (type === 'images') {
            thumb = '<img src="' + asset.url + '" class="asset-thumbnail mb-1" loading="lazy" alt="' + asset.filename + '">';
          } else {
            thumb = '<div class="asset-thumbnail mb-1 d-flex align-items-center justify-content-center"><i class="fa-solid fa-music fa-2x text-body-secondary"></i></div>';
          }

          card.innerHTML = thumb +
            '<div class="asset-info text-truncate" title="' + asset.filename + '">' + asset.filename + '</div>' +
            '<div class="asset-info text-body-secondary">' + formatBytes(asset.size) + '</div>' +
            '<button type="button" class="btn btn-sm btn-outline-danger asset-delete" title="Delete"><i class="fa-solid fa-trash-can"></i></button>';

          // Select on click
          card.addEventListener('click', function (e) {
            if (e.target.closest('.asset-delete')) return;
            grid.querySelectorAll('.asset-card').forEach(function (c) { c.classList.remove('selected'); });
            card.classList.add('selected');
            selectedAsset = asset.filename;
          });

          // Delete button
          var delBtn = card.querySelector('.asset-delete');
          if (delBtn) {
            delBtn.addEventListener('click', function () {
              if (!confirm('Delete ' + asset.filename + '?')) return;
              fetch('/api/assets/' + encodeURIComponent(asset.filename), { method: 'DELETE' })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                  if (d.success) {
                    col.remove();
                    if (selectedAsset === asset.filename) selectedAsset = '';
                    // Check if grid is now empty
                    if (!grid.querySelector('.asset-card')) {
                      if (empty) empty.classList.remove('d-none');
                    }
                  }
                })
                .catch(function () {});
            });
          }

          col.appendChild(card);
          grid.appendChild(col);
        });
      })
      .catch(function () {
        grid.innerHTML = '<div class="col-12"><div class="alert alert-danger py-1 small">Failed to load assets.</div></div>';
      });
  }

  function applySelection() {
    if (!selectedAsset || !currentTarget) return;
    var t = targetMap[currentTarget];
    if (!t) return;

    // Update file input dataset
    var input = document.getElementById(t.inputId);
    if (input) input.dataset.uploadedFilename = selectedAsset;

    // Update display text
    var display = document.getElementById(t.displayId);
    if (display) display.textContent = selectedAsset;

    // Show clear button
    var clearBtn = t.clearId ? document.getElementById(t.clearId) : null;
    if (clearBtn) clearBtn.classList.remove('d-none');

    // Update hidden persistence input
    var hidden = document.getElementById(t.hiddenId);
    if (hidden) hidden.value = selectedAsset;

    // Save settings
    if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();

    // Close modal
    var modalEl = document.getElementById('assetPickerModal');
    var modal = bootstrap.Modal.getInstance(modalEl);
    if (modal) modal.hide();
  }

  // ---- Restore selections on page load ----
  function restoreAssetSelections() {
    Object.keys(targetMap).forEach(function (key) {
      var t = targetMap[key];
      var hidden = document.getElementById(t.hiddenId);
      if (!hidden || !hidden.value) return;

      var filename = hidden.value;

      // Validate the file still exists
      fetch('/uploads/' + encodeURIComponent(filename), { method: 'HEAD' })
        .then(function (r) {
          if (!r.ok) {
            // File gone — clear persistence
            hidden.value = '';
            if (window.PCG && window.PCG.saveSettings) window.PCG.saveSettings();
            return;
          }

          // Restore display
          var input = document.getElementById(t.inputId);
          if (input) input.dataset.uploadedFilename = filename;

          var display = document.getElementById(t.displayId);
          if (display) display.textContent = filename;

          var clearBtn = t.clearId ? document.getElementById(t.clearId) : null;
          if (clearBtn) clearBtn.classList.remove('d-none');
        })
        .catch(function () {});
    });
  }

  // ---- Init ----
  document.addEventListener('DOMContentLoaded', function () {
    var modalEl = document.getElementById('assetPickerModal');
    if (!modalEl) return;

    // On modal show — detect which target triggered it
    modalEl.addEventListener('show.bs.modal', function (e) {
      var trigger = e.relatedTarget;
      if (trigger) {
        currentTarget = trigger.dataset.assetTarget || '';
        currentType = trigger.dataset.assetType || 'images';
      }
      var label = document.getElementById('assetPickerTarget');
      if (label) label.textContent = targetLabels[currentTarget] || 'Asset';
      loadAssets(currentType);
    });

    // Apply button
    var applyBtn = document.getElementById('assetPickerApply');
    if (applyBtn) applyBtn.addEventListener('click', applySelection);
  });

  // Expose restore function
  window.PCG = window.PCG || {};
  window.PCG.restoreAssetSelections = restoreAssetSelections;
})();
