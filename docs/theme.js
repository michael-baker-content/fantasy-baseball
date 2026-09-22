/* Loaded in the head so both pages apply the saved theme before rendering. */
(() => {
  const root = document.documentElement;
  try {
    root.dataset.theme = localStorage.getItem('theme') === 'dark' ? 'dark' : 'light';
  } catch {
    root.dataset.theme = 'light';
  }
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('theme-toggle');
    if (!button) return;
    function syncButton() {
      const dark = root.dataset.theme === 'dark';
      button.setAttribute('aria-label', dark ? 'Switch to Light Mode' : 'Switch to Dark Mode');
      // This is an action button with a changing label, not a fixed-label toggle.
      button.removeAttribute('aria-pressed');
    }
    button.addEventListener('click', () => {
      root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('theme', root.dataset.theme); } catch {}
      syncButton();
    });
    syncButton();
  }, {once: true});
})();
