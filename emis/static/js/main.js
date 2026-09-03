document.addEventListener('DOMContentLoaded', function () {
  var shell = document.querySelector('.emis-shell');
  var toggleBtn = document.querySelector('[data-emis-sidebar-toggle]');
  var searchInput = document.getElementById('emis-global-search');

  // Sidebar toggle
  if (toggleBtn && shell) {
    toggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
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

  // Close mobile sidebar on backdrop click
  document.addEventListener('click', function (e) {
    if (shell && shell.classList.contains('sidebar-mobile-open')) {
      var sidebar = document.querySelector('.emis-sidebar');
      if (sidebar && !sidebar.contains(e.target) && (!toggleBtn || !toggleBtn.contains(e.target))) {
        shell.classList.remove('sidebar-mobile-open');
      }
    }
  });

  // Restore collapsed state on desktop
  if (shell && window.innerWidth > 991) {
    var collapsed = localStorage.getItem('emisSidebarCollapsed');
    if (collapsed === 'true') {
      shell.classList.add('sidebar-collapsed');
    }
  }

  // Global search keyboard shortcut (Ctrl+K / Cmd+K)
  document.addEventListener('keydown', function (e) {
    if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
      if (searchInput) {
        e.preventDefault();
        searchInput.focus();
        searchInput.select();
      }
    } else if (e.key === 'Escape') {
      if (searchInput && document.activeElement === searchInput) {
        searchInput.blur();
      }
      if (shell && shell.classList.contains('sidebar-mobile-open')) {
        shell.classList.remove('sidebar-mobile-open');
      }
    }
  });

  // Auto-dismiss alerts
  document.querySelectorAll('.emis-alert[data-autodismiss]').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      setTimeout(function () { el.remove(); }, 300);
    }, 4000);
  });
});



