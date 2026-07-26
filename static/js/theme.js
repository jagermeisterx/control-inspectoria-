(function () {
  'use strict';
  var STORAGE_KEY = 'inspectoria-theme';

  function getStored() {
    try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }
  function setStored(v) {
    try { localStorage.setItem(STORAGE_KEY, v); } catch (e) {}
  }

  function systemPref() {
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark' : 'light';
  }

  function applyTheme(theme) {
    var t = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', t);
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      var icon = btn.querySelector('i');
      var label = btn.querySelector('span');
      if (icon) icon.className = t === 'dark' ? 'bi bi-sun' : 'bi bi-moon-stars';
      if (label) label.textContent = t === 'dark' ? 'Modo claro' : 'Modo oscuro';
      btn.setAttribute('aria-label', t === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro');
    }
  }

  function init() {
    var stored = getStored();
    var theme = stored || systemPref();
    applyTheme(theme);
  }

  function toggle() {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    setStored(next);
    applyTheme(next);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('#theme-toggle');
    if (btn) {
      e.preventDefault();
      toggle();
    }
  });
})();
