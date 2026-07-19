'use strict';
/* ===== TEMPLATE 4 — PINK ===== */
(function () {
  /* Nav scroll */
  const nav = document.querySelector('.nav');
  window.addEventListener('scroll', () => {
    if (nav) nav.classList.toggle('scrolled', window.scrollY > 60);
  }, { passive: true });

  /* Mobile nav */
  const hamburger = document.getElementById('hamburger');
  const mobileNav = document.getElementById('mobileNav');
  if (hamburger && mobileNav) {
    hamburger.addEventListener('click', () => mobileNav.classList.toggle('open'));
    mobileNav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => mobileNav.classList.remove('open')));
  }

  /* Smooth scroll */
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const t = document.querySelector(a.getAttribute('href'));
      if (t) { e.preventDefault(); t.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  });

  /* Scroll reveal */
  const revObs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { e.target.classList.add('revealed'); revObs.unobserve(e.target); } });
  }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
  document.querySelectorAll('.reveal').forEach(el => revObs.observe(el));

  /* Animated counters */
  function animateCount(el) {
    const raw = el.dataset.count || el.textContent.trim();
    const suffix = raw.replace(/[\d.]/g, '');
    const end = parseFloat(raw.replace(/[^0-9.]/g, ''));
    const dur = 2000; const t0 = performance.now();
    const tick = now => {
      const p = Math.min((now - t0) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 4);
      el.textContent = (Number.isInteger(end) ? Math.round(end * eased) : (end * eased).toFixed(1)) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }
  const cntObs = new IntersectionObserver(entries => {
    entries.forEach(e => { if (e.isIntersecting) { animateCount(e.target); cntObs.unobserve(e.target); } });
  }, { threshold: 0.5 });
  document.querySelectorAll('.stat-num, .counter, .about-visual-num').forEach(el => {
    el.dataset.count = el.textContent.trim(); cntObs.observe(el);
  });

  /* Hero stagger entrance */
  document.querySelectorAll('.hero-content > *').forEach((el, i) => {
    el.style.cssText = `opacity:0;transform:translateY(22px);transition:opacity 0.65s ease ${i * 0.12}s,transform 0.65s ease ${i * 0.12}s`;
    setTimeout(() => { el.style.opacity = '1'; el.style.transform = 'none'; }, 60);
  });

  /* Orb parallax */
  const orbs = document.querySelectorAll('.hero-glow');
  if (orbs.length) {
    document.addEventListener('mousemove', e => {
      const fx = (e.clientX / window.innerWidth - 0.5) * 20;
      const fy = (e.clientY / window.innerHeight - 0.5) * 20;
      orbs.forEach((o, i) => { o.style.transform = `translate(${fx * (i+1) * 0.5}px,${fy * (i+1) * 0.5}px)`; });
    }, { passive: true });
  }

  /* Card hover tilt */
  document.querySelectorAll('.tcard, .service-card, .feature-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      if (!card.classList.contains('feature-card'))
        card.style.transform = `perspective(800px) rotateX(${-y*4}deg) rotateY(${x*4}deg) translateY(-3px)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });

  console.log('[Template 4 — pink] Loaded ✓');
})();
