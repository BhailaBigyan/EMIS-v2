document.addEventListener('DOMContentLoaded', function () {
  var toggleBtn = document.querySelector('[data-stu-nav-toggle]');
  var navbar = document.querySelector('.stu-navbar');

  if (toggleBtn && navbar) {
    toggleBtn.addEventListener('click', function (e) {
      e.stopPropagation();
      var isOpen = navbar.classList.toggle('mobile-open');
      toggleBtn.classList.toggle('open', isOpen);
    });

    // Close when clicking outside on mobile
    document.addEventListener('click', function (e) {
      if (navbar.classList.contains('mobile-open')) {
        if (!navbar.contains(e.target) && !toggleBtn.contains(e.target)) {
          navbar.classList.remove('mobile-open');
          toggleBtn.classList.remove('open');
        }
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && navbar.classList.contains('mobile-open')) {
        navbar.classList.remove('mobile-open');
        toggleBtn.classList.remove('open');
      }
    });
  }

  // Auto-dismiss alerts (shared behavior with admin shell)
  document.querySelectorAll('.emis-alert[data-autodismiss]').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
      el.style.opacity = '0';
      el.style.transform = 'translateY(-6px)';
      setTimeout(function () { el.remove(); }, 300);
    }, 4000);
  });
});