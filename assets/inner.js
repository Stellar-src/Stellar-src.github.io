try {
  const theme = localStorage.getItem('stellar-src-theme-v1') === 'dark' ? 'dark' : 'light';
  document.getElementById('og-journal').dataset.theme = theme;
  document.documentElement.dataset.theme = theme;
} catch {}
