/* Theme toggle — loaded before DOM to prevent flash */
(function () {
  var THEME_KEY = 'patreon_credits_theme';
  var saved = localStorage.getItem(THEME_KEY) || 'dark';
  document.documentElement.setAttribute('data-bs-theme', saved);

  document.addEventListener('DOMContentLoaded', function () {
    var toggle = document.getElementById('themeToggle');
    var icon = document.getElementById('themeIcon');
    if (!toggle || !icon) return;

    function updateIcon() {
      var current = document.documentElement.getAttribute('data-bs-theme');
      icon.className = current === 'dark' ? 'fa-solid fa-sun' : 'fa-solid fa-moon';
    }
    updateIcon();

    toggle.addEventListener('click', function () {
      var current = document.documentElement.getAttribute('data-bs-theme');
      var next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-bs-theme', next);
      localStorage.setItem(THEME_KEY, next);
      updateIcon();
    });
  });
})();
