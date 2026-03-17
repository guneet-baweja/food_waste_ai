(function () {
  'use strict';

  // ── LOADER ──
  function initLoader() {
    const loader = document.getElementById('loader');
    if (!loader) return;
    setTimeout(() => {
      loader.classList.add('hidden');
    }, 2000);
  }

  // ── THEME TOGGLE ──
  function initThemeToggle() {
    const toggle = document.getElementById('themeToggle');
    const icon = toggle?.querySelector('.theme-icon');
    if (!toggle) return;
    const saved = localStorage.getItem('theme') || 'dark';
    applyTheme(saved, icon);
    toggle.addEventListener('click', () => {
      const isDark = document.body.classList.contains('dark-mode');
      const next = isDark ? 'light' : 'dark';
      applyTheme(next, icon);
      localStorage.setItem('theme', next);
    });
  }

  function applyTheme(theme, icon) {
    if (theme === 'light') {
      document.body.classList.remove('dark-mode');
      if (icon) icon.textContent = '🌙';
    } else {
      document.body.classList.add('dark-mode');
      if (icon) icon.textContent = '☀️';
    }
  }

  // ── NAVBAR SCROLL ──
  function initNavbarScroll() {
    const navbar = document.getElementById('navbar');
    if (!navbar) return;
    window.addEventListener('scroll', () => {
      if (window.scrollY > 60) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    }, { passive: true });
  }

  // ── SCROLL REVEAL ──
  function initScrollReveal() {
    const revealEls = document.querySelectorAll('.reveal');
    if (!revealEls.length) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    revealEls.forEach((el) => observer.observe(el));
  }

  // ── COUNTER ANIMATION ──
  function animateCounter(el, start, end, duration) {
    const startTime = performance.now();
    function update(timestamp) {
      const progress = Math.min((timestamp - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(start + (end - start) * eased);
      el.textContent = current.toLocaleString();
      if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
  }

  // ── HERO STAT COUNTERS ──
  function initHeroCounters() {
    const statEls = document.querySelectorAll('.hstat-num');
    if (!statEls.length) return;
    let started = false;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !started) {
        started = true;
        statEls.forEach((el) => {
          const target = parseInt(el.dataset.target, 10) || 0;
          animateCounter(el, 0, target, 2000);
        });
      }
    }, { threshold: 0.5 });
    const heroContent = document.getElementById('heroContent');
    if (heroContent) observer.observe(heroContent);
  }

  // ── IMPACT COUNTERS (from API) ──
  function initImpactCounters() {
    const section = document.getElementById('impactSection');
    if (!section) return;
    let triggered = false;
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && !triggered) {
        triggered = true;
        loadAndAnimateStats();
      }
    }, { threshold: 0.3 });
    observer.observe(section);
  }

  async function loadAndAnimateStats() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      if (!data.success) return;
      const stats = data.stats;
      const mapping = {
        impactMeals: stats.total_meals_donated,
        impactCO2: Math.round(stats.total_co2_saved),
        impactUsers: stats.total_users,
        impactCities: stats.cities_reached,
        platMeals: stats.total_meals_donated,
        platCO2: Math.round(stats.total_co2_saved),
        platUsers: stats.total_users,
        platDonations: stats.total_donations
      };
      Object.entries(mapping).forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el && val !== undefined) animateCounter(el, 0, val, 1800);
      });
    } catch (err) {
      console.warn('[Impact] Failed to load stats:', err);
    }
  }

  // ── TESTIMONIALS CAROUSEL ──
  function initCarousel() {
    const cards = document.querySelectorAll('.testimonial-card');
    const dots = document.querySelectorAll('.cdot');
    if (!cards.length) return;
    let current = 0;
    let autoplay;

    function showSlide(idx) {
      cards.forEach(c => c.classList.remove('active'));
      dots.forEach(d => d.classList.remove('active'));
      cards[idx].classList.add('active');
      if (dots[idx]) dots[idx].classList.add('active');
      current = idx;
    }

    function next() {
      showSlide((current + 1) % cards.length);
    }

    dots.forEach((dot, idx) => {
      dot.addEventListener('click', () => {
        showSlide(idx);
        clearInterval(autoplay);
        autoplay = setInterval(next, 4500);
      });
    });

    autoplay = setInterval(next, 4500);
  }

  // ── MAP TICKER ──
  function initMapTicker() {
    const tickerEl = document.getElementById('tickerText');
    if (!tickerEl) return;
    const messages = [
      '🍛 Vegetable Curry picked up in Brooklyn',
      '🚗 Volunteer en route to NGO Center',
      '🍞 3 Bread Loaves listed in Bronx',
      '⚠️ High urgency: Mixed Salads need pickup NOW',
      '✅ Rice & Dal delivered — 8kg food saved!',
      '🌿 12.5 kg CO₂ saved this hour',
      '📦 New donation from Green Kitchen NYC',
      '🏆 Alex earned Planet Saver badge!'
    ];
    let idx = 0;
    setInterval(() => {
      tickerEl.style.opacity = '0';
      setTimeout(() => {
        idx = (idx + 1) % messages.length;
        tickerEl.textContent = messages[idx];
        tickerEl.style.opacity = '1';
      }, 400);
    }, 3500);
  }

  // ── PARALLAX HERO ──
  function initParallax() {
    const heroContent = document.getElementById('heroContent');
    if (!heroContent) return;
    window.addEventListener('scroll', () => {
      const sy = window.scrollY;
      if (sy < window.innerHeight) {
        heroContent.style.transform = `translateY(${sy * 0.25}px)`;
        heroContent.style.opacity = `${1 - sy / 600}`;
      }
    }, { passive: true });
  }

  // ── AI METER ANIMATION ──
  function initAIMeters() {
    const meters = document.querySelectorAll('.ai-meter-fill');
    if (!meters.length) return;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const fill = entry.target;
          const pct = fill.style.getPropertyValue('--pct') || '0%';
          fill.style.width = '0%';
          setTimeout(() => {
            fill.style.transition = 'width 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
            fill.style.width = pct;
          }, 200);
          observer.unobserve(fill);
        }
      });
    }, { threshold: 0.5 });
    meters.forEach(m => observer.observe(m));
  }

  // ── MOBILE MENU ──
  function initMobileMenu() {
    const hamburger = document.getElementById('navHamburger');
    const menu = document.getElementById('mobileMenu');
    const closeBtn = document.getElementById('mobileClose');
    if (!hamburger || !menu) return;
    hamburger.addEventListener('click', () => menu.classList.add('open'));
    closeBtn?.addEventListener('click', () => menu.classList.remove('open'));
    menu.addEventListener('click', (e) => {
      if (e.target === menu) menu.classList.remove('open');
    });
  }

  // ── BUTTON RIPPLE ──
  function initButtonEffects() {
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn');
      if (!btn) return;
      const ripple = document.createElement('span');
      const rect = btn.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.cssText = `
        position:absolute;border-radius:50%;
        background:rgba(255,255,255,0.25);
        width:${size}px;height:${size}px;
        left:${e.clientX - rect.left - size / 2}px;
        top:${e.clientY - rect.top - size / 2}px;
        transform:scale(0);
        animation:rippleAnim 0.6s ease-out forwards;
        pointer-events:none;
      `;
      if (!document.getElementById('rippleStyle')) {
        const style = document.createElement('style');
        style.id = 'rippleStyle';
        style.textContent = `@keyframes rippleAnim{to{transform:scale(2);opacity:0;}}`;
        document.head.appendChild(style);
      }
      btn.style.position = 'relative';
      btn.style.overflow = 'hidden';
      btn.appendChild(ripple);
      setTimeout(() => ripple.remove(), 600);
    });
  }

  // ── INIT ALL ──
  function init() {
    initLoader();
    initThemeToggle();
    initNavbarScroll();
    initScrollReveal();
    initHeroCounters();
    initImpactCounters();
    initCarousel();
    initMapTicker();
    initParallax();
    initAIMeters();
    initMobileMenu();
    initButtonEffects();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  window.animationsModule = { animateCounter };

})();
