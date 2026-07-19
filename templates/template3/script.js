'use strict';
/* ===== TEMPLATE 3 — GREEN: Eco / Health / Organic ===== */
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
    const dur = 2000; const start = performance.now();
    const update = now => { const p = Math.min((now - start) / dur, 1); const eased = 1 - Math.pow(1 - p, 3); const cur = end * eased; el.textContent = (Number.isInteger(end) ? Math.round(cur) : cur.toFixed(1)) + suffix; if (p < 1) requestAnimationFrame(update); };
    requestAnimationFrame(update);
  }
  const counterObs = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) { animateCounter(e.target); counterObs.unobserve(e.target); } }), { threshold: 0.5 });
  document.querySelectorAll('.stat-num').forEach(el => { el.dataset.count = el.textContent.trim(); counterObs.observe(el); });

  /* Floating pill animation jitter */
  document.querySelectorAll('.hero-pill').forEach((pill, i) => {
    pill.style.animationDuration = `${4 + i * 1.5}s`;
    pill.style.animationDelay = `${i * -1.5}s`;
  });

  /* Service card hover */
  document.querySelectorAll('.service-card').forEach(card => {
    card.addEventListener('mouseenter', () => card.querySelector('.service-icon') && (card.querySelector('.service-icon').style.color = '#fff'));
    card.addEventListener('mouseleave', () => card.querySelector('.service-icon') && (card.querySelector('.service-icon').style.color = ''));
  });

  /* Hero stagger */
  document.querySelectorAll('.hero-content > *').forEach((el, i) => {
    el.style.opacity = '0'; el.style.transform = 'translateY(20px)';
    el.style.transition = `opacity 0.6s ease ${i * 0.1 + 0.1}s, transform 0.6s ease ${i * 0.1 + 0.1}s`;
    setTimeout(() => { el.style.opacity = '1'; el.style.transform = 'none'; }, 50);
  });

  console.log('[Template 3 — Green Health] Loaded ✓');
})();
