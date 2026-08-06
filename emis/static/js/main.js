document.addEventListener('DOMContentLoaded', function () {
  var shell = document.querySelector('.emis-shell');
  var toggleBtn = document.querySelector('[data-emis-sidebar-toggle]');

  if (toggleBtn && shell) {
    toggleBtn.addEventListener('click', function () {
      if (window.innerWidth <= 991) {
        shell.classList.toggle('sidebar-mobile-open');
      } else {
        shell.classList.toggle('sidebar-collapsed');
        localStorage.setItem(
          'emisSidebarCollapsed',
          shell.classList.contains('sidebar-collapsed')
        );
      }
    });
  }

  // restore collapsed state on desktop
  if (shell && window.innerWidth > 991) {
    var collapsed = localStorage.getItem('emisSidebarCollapsed');
    if (collapsed === 'true') {
      shell.classList.add('sidebar-collapsed');
    }
  }

  // auto-dismiss alerts
  document.querySelectorAll('.emis-alert[data-autodismiss]').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.3s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 300);
    }, 4000);
  });
});