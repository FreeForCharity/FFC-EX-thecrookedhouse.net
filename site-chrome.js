// The Crooked House — shared site chrome
// Mobile hamburger nav toggle. Loaded by every page.

(function () {
  var menuToggle = document.getElementById('mobile-menu-toggle');
  var mobileNav = document.getElementById('mobile-nav');
  if (!menuToggle || !mobileNav) return;

  menuToggle.addEventListener('click', function () {
    var isOpen = mobileNav.classList.toggle('active');
    menuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  });

  mobileNav.querySelectorAll('.Index-nav-item').forEach(function (item) {
    item.addEventListener('click', function () {
      mobileNav.classList.remove('active');
      menuToggle.setAttribute('aria-expanded', 'false');
    });
  });
})();
