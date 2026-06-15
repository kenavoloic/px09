/* theme.js — gestion du thème dark/light avec persistance */
(function() {
  const htmlEl = document.documentElement;
  const themeBtn = document.getElementById('theme-toggle');
  const iconSun = document.getElementById('icon-sun');
  const iconMoon = document.getElementById('icon-moon');

  function applyTheme(t) {
    htmlEl.setAttribute('data-theme', t);
    if (iconSun) iconSun.style.display = t === 'dark' ? 'block' : 'none';
    if (iconMoon) iconMoon.style.display = t === 'light' ? 'block' : 'none';
  }

  const saved = localStorage.getItem('hlm-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved || (prefersDark ? 'dark' : 'light'));

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const current = htmlEl.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem('hlm-theme', next);
    });
  }

  // Nav scroll
  const nav = document.querySelector('.site-nav');
  if (nav) {
    window.addEventListener('scroll', () => {
      nav.classList.toggle('scrolled', window.scrollY > 40);
    });
  }

  // Reveal observer
  const reveals = document.querySelectorAll('.reveal');
  if (reveals.length) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('visible');
          observer.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    reveals.forEach(el => observer.observe(el));
    // Trigger header reveals immediately
    setTimeout(() => {
      document.querySelectorAll('.hero .reveal, .page-header .reveal').forEach(el => el.classList.add('visible'));
    }, 100);
  }
})();
