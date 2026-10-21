/* SkyBook - Main JS */

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', function () {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) bsAlert.close();
    }, 5000);
  });

  // Active nav link highlight
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar-custom .nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
      link.style.color = '#fff';
      link.style.background = 'rgba(255,255,255,0.12)';
    }
  });

  // Smooth hover effect for admin quick links
  document.querySelectorAll('.admin-quick-link').forEach(card => {
    card.style.transition = 'all 0.25s ease';
  });
});
