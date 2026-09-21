(() => {
  const toggle = document.querySelector('.mobile-menu-toggle');
  const menu = document.getElementById('header-menu');
  if (!toggle || !menu) return;
  const mobile = window.matchMedia('(max-width: 780px)');
  const themeToggle = menu.querySelector('.theme-toggle');
  function updateThemeLabel() {
    if (themeToggle) themeToggle.setAttribute('aria-label',
      document.documentElement.dataset.theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode');
  }
  new MutationObserver(updateThemeLabel).observe(document.documentElement, {
    attributes: true, attributeFilter: ['data-theme'],
  });
  updateThemeLabel();
  function setOpen(open, restoreFocus = false) {
    menu.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Close navigation menu' : 'Open navigation menu');
    if (restoreFocus) toggle.focus();
  }
  toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && mobile.matches && menu.classList.contains('is-open')) {
      setOpen(false, true);
    }
  });
  document.addEventListener('click', event => {
    if (mobile.matches && !menu.contains(event.target) && !toggle.contains(event.target)) {
      setOpen(false);
    }
  });
  menu.addEventListener('click', event => {
    if (mobile.matches && event.target.closest('a')) setOpen(false);
  });
  mobile.addEventListener('change', () => {
    const focusWillBeHidden = mobile.matches && menu.contains(document.activeElement);
    const focusWasOnToggle = !mobile.matches && document.activeElement === toggle;
    setOpen(false, focusWillBeHidden);
    if (focusWasOnToggle) menu.querySelector('a')?.focus();
  });
})();
