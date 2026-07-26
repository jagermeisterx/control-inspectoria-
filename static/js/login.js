(function () {
  'use strict';
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.password-toggle');
    if (!btn) return;
    e.preventDefault();
    var targetId = btn.getAttribute('data-target');
    var input = document.getElementById(targetId);
    if (!input) return;
    var icon = btn.querySelector('i');
    if (input.type === 'password') {
      input.type = 'text';
      if (icon) icon.className = 'bi bi-eye-slash';
    } else {
      input.type = 'password';
      if (icon) icon.className = 'bi bi-eye';
    }
  });
})();
