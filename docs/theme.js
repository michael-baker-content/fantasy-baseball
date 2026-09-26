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
    const icon = document.getElementById('theme-icon');
    function syncButton() {
      const dark = root.dataset.theme === 'dark';
      if (icon) icon.innerHTML = dark
        ? '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>'
        : '<path d="M21.75 15A9.72 9.72 0 0 1 18 15.75 9.75 9.75 0 0 1 8.25 6c0-1.33.27-2.6.75-3.75A9.75 9.75 0 1 0 21.75 15Z"/>';
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
