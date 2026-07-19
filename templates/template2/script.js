'use strict';
/* ===== TEMPLATE 2 — RED: Bold Agency ===== */
(function () {
  const nav = document.querySelector('.nav');
  window.addEventListener('scroll', () => { nav && (window.scrollY > 60 ? nav.classList.add('scrolled') : nav.classList.remove('scrolled')); }, { passive: true });

  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobileNav');
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', () => mobileNav.classList.toggle('open'));
    mobileNav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => mobileNav.classList.remove('open')));
  }

  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => { const t = document.querySelector(a.getAttribute('href')); if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth' }); } });
  });

  const revealObs = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); revealObs.unobserve(e.target); } }), { threshold: 0.1, rootMargin: '0px 0px -60px 0px' });
  document.querySelectorAll('.reveal').forEach(el => revealObs.observe(el));

  function animateCounter(el) {
    const raw = el.dataset.count || el.textContent.trim();
    const suffix = raw.replace(/[\d.]/g, '');
    const end = parseFloat(raw.replace(/[^0-9.]/g, ''));
    const dur = 1800; const start = performance.now();
    const update = now => { const p = Math.min((now - start) / dur, 1); const eased = 1 - Math.pow(1 - p, 4); const cur = end * eased; el.textContent = (Number.isInteger(end) ? Math.round(cur) : cur.toFixed(1)) + suffix; if (p < 1) requestAnimationFrame(update); };
    requestAnimationFrame(update);
  }
  const counterObs = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) { animateCounter(e.target); counterObs.unobserve(e.target); } }), { threshold: 0.5 });
  document.querySelectorAll('.stat-num, .about-num-val').forEach(el => { el.dataset.count = el.textContent.trim(); counterObs.observe(el); });

  /* Service item hover */
  document.querySelectorAll('.service-item').forEach(item => {
    item.addEventListener('mouseenter', () => item.style.borderLeftWidth = '3px');
    item.addEventListener('mouseleave', () => item.style.borderLeftWidth = '');
  });

  /* Hero stagger */
  document.querySelectorAll('.hero-content > *').forEach((el, i) => {
    el.style.opacity = '0'; el.style.transform = 'translateY(24px)';
    el.style.transition = `opacity 0.7s ease ${i * 0.12 + 0.2}s, transform 0.7s ease ${i * 0.12 + 0.2}s`;
    setTimeout(() => { el.style.opacity = '1'; el.style.transform = 'none'; }, 50);
  });

  console.log('[Template 2 — Red Agency] Loaded ✓');
})();
