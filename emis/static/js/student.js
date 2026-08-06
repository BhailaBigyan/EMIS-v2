document.addEventListener('DOMContentLoaded', function () {
  var toggleBtn = document.querySelector('[data-stu-nav-toggle]');
  var navbar = document.querySelector('.stu-navbar');

  if (toggleBtn && navbar) {
    toggleBtn.addEventListener('click', function () {
      navbar.classList.toggle('mobile-open');
      var icon = toggleBtn.querySelector('i');
      if (icon) {
        icon.classList.toggle('bi-list');
        icon.classList.toggle('bi-x-lg');
      }
    });
  }

  // auto-dismiss alerts (shared behavior with admin shell)
  document.querySelectorAll('.emis-alert[data-autodismiss]').forEach(function (el) {
    setTimeout(function () {
      el.style.transition = 'opacity 0.3s ease';
      el.style.opacity = '0';
      setTimeout(function () { el.remove(); }, 300);
    }, 4000);
  });
});