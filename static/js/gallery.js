/* Patreon Credits Generator — Gallery Tab */
(function () {
  'use strict';

  function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  }

  function formatDate(isoStr) {
    try {
      var d = new Date(isoStr);
      return d.toLocaleDateString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch (_) {
      return isoStr;
    }
  }

  function createVideoCard(video) {
    var col = document.createElement('div');
    col.className = 'col';

    col.innerHTML =
      '<div class="card gallery-card h-100" data-filename="' + video.filename + '">' +
        '<img src="' + video.thumbnail_url + '" class="card-img-top" alt="' + video.filename + '"' +
          ' onerror="this.src=\'/static/img/video-placeholder.svg\'">' +
        '<div class="card-body p-2">' +
          '<p class="card-text small mb-1 text-truncate" title="' + video.filename + '">' + video.filename + '</p>' +
          '<p class="card-text text-body-secondary" style="font-size:.75rem">' +
            formatDate(video.created) + ' &middot; ' + formatBytes(video.size) +
          '</p>' +
        '</div>' +
        '<div class="card-footer bg-transparent border-0 p-2 pt-0">' +
          '<div class="btn-group btn-group-sm w-100">' +
            '<button class="btn btn-outline-primary gallery-preview-btn" title="Preview">' +
              '<i class="fa-solid fa-circle-play"></i> Preview' +
            '</button>' +
            '<a href="' + video.download_url + '" class="btn btn-outline-success gallery-download-btn" title="Download">' +
              '<i class="fa-solid fa-download"></i>' +
            '</a>' +
            '<button class="btn btn-outline-danger gallery-delete-btn" title="Delete">' +
              '<i class="fa-solid fa-trash"></i>' +
            '</button>' +
          '</div>' +
        '</div>' +
      '</div>';

    return col;
  }

  function loadGallery() {
    var grid = document.getElementById('galleryGrid');
    var empty = document.getElementById('galleryEmpty');
    var countBadge = document.getElementById('galleryCount');
    if (!grid) return;

    grid.innerHTML = '<div class="col-12 text-center py-4"><div class="spinner-border text-secondary" role="status"></div></div>';

    fetch('/api/videos')
      .then(function (r) { return r.json(); })
      .then(function (data) {
        grid.innerHTML = '';
        var videos = data.videos || [];

        if (countBadge) countBadge.textContent = videos.length;

        if (videos.length === 0) {
          if (empty) empty.classList.remove('d-none');
          return;
        }
        if (empty) empty.classList.add('d-none');

        videos.forEach(function (v) {
          grid.appendChild(createVideoCard(v));
        });
      })
      .catch(function () {
        grid.innerHTML = '<div class="col-12"><div class="alert alert-danger">Failed to load videos.</div></div>';
      });
  }

  function deleteVideo(filename, cardEl) {
    if (!confirm('Delete ' + filename + '? This cannot be undone.')) return;

    fetch('/api/videos/' + encodeURIComponent(filename), { method: 'DELETE' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.success) {
          cardEl.remove();
          // Update count
          var countBadge = document.getElementById('galleryCount');
          if (countBadge) {
            var n = parseInt(countBadge.textContent) - 1;
            countBadge.textContent = n < 0 ? 0 : n;
            if (n <= 0) {
              var empty = document.getElementById('galleryEmpty');
              if (empty) empty.classList.remove('d-none');
            }
          }
        }
      })
      .catch(function () { alert('Failed to delete video.'); });
  }

  function showPreview(video) {
    var modalPlayer = document.getElementById('modalVideoPlayer');
    var modalTitle = document.getElementById('galleryModalLabel');
    var modalDownload = document.getElementById('modalDownloadBtn');
    if (!modalPlayer) return;

    modalPlayer.src = video.video_url;
    if (modalTitle) modalTitle.textContent = video.filename;
    if (modalDownload) modalDownload.href = video.download_url;

    var modal = bootstrap.Modal.getOrCreateInstance(document.getElementById('galleryModal'));
    modal.show();
  }

  document.addEventListener('DOMContentLoaded', function () {
    var grid = document.getElementById('galleryGrid');
    if (!grid) return;

    // Load when Gallery tab is shown
    var galleryTab = document.querySelector('[data-bs-target="#gallery-tab-pane"]');
    if (galleryTab) {
      galleryTab.addEventListener('shown.bs.tab', loadGallery);
    }

    // Refresh button
    var refreshGalleryBtn = document.getElementById('refreshGalleryBtn');
    if (refreshGalleryBtn) {
      refreshGalleryBtn.addEventListener('click', loadGallery);
    }

    // Delegate click events on the grid
    grid.addEventListener('click', function (e) {
      var btn = e.target.closest('button, a');
      if (!btn) return;
      var card = btn.closest('.gallery-card');
      if (!card) return;
      var filename = card.dataset.filename;

      if (btn.classList.contains('gallery-preview-btn')) {
        e.preventDefault();
        showPreview({
          filename: filename,
          video_url: '/output/' + filename,
          download_url: '/download/' + filename,
        });
      } else if (btn.classList.contains('gallery-delete-btn')) {
        e.preventDefault();
        deleteVideo(filename, card.closest('.col'));
      }
      // gallery-download-btn is an <a>, let it navigate naturally
    });

    // Pause video when modal closes
    var galleryModal = document.getElementById('galleryModal');
    if (galleryModal) {
      galleryModal.addEventListener('hidden.bs.modal', function () {
        var player = document.getElementById('modalVideoPlayer');
        if (player) { player.pause(); player.src = ''; }
      });
    }

    // Listen for new video generation to refresh gallery
    document.addEventListener('videoGenerated', loadGallery);
  });
})();
