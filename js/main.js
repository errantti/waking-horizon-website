(() => {
  'use strict';
  const root = document.documentElement;
  root.classList.add('js');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  const yr = document.getElementById('year');
  if (yr) yr.textContent = new Date().getFullYear();

  /* nav turns solid after the hero */
  const nav = document.getElementById('nav');
  const onScroll = () => nav.classList.toggle('is-solid', window.scrollY > window.innerHeight * 0.6);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* scroll reveal */
  const els = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduce) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); } });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    els.forEach((el) => io.observe(el));
  } else {
    els.forEach((el) => el.classList.add('is-in'));
  }

  /* toast */
  const toast = document.getElementById('toast');
  let tt;
  const say = (msg) => {
    toast.textContent = msg; toast.classList.add('is-on');
    clearTimeout(tt); tt = setTimeout(() => toast.classList.remove('is-on'), 1800);
  };

  /* press kit */
  const VARIANTS = [
    { id: 'logo-full', name: 'Full logo', note: 'Mark + Waking Horizon + Studio', primary: true },
    { id: 'logo-horizontal', name: 'Horizontal, no “Studio”', note: 'For use outside a gaming context' },
    { id: 'logo-stacked', name: 'Stacked', note: 'Centered, with Studio' },
    { id: 'logo-stacked-nostudio', name: 'Stacked, no “Studio”', note: 'Centered, name only' },
    { id: 'mark', name: 'Mark only', note: 'Sunrise and cross-spike. Avatars, icons' },
    { id: 'wordmark', name: 'Wordmark', note: 'Text only' },
    { id: 'wordmark-studio', name: 'Wordmark + Studio', note: 'Text only, with Studio' },
  ];
  const COLORS = [['color', 'Color'], ['cream', 'Cream'], ['violet', 'Violet'], ['black', 'Black'], ['white', 'White']];
  const grid = document.getElementById('logo-grid');
  if (grid) {
    grid.dataset.bg = 'dark';
    VARIANTS.forEach((v) => {
      const card = document.createElement('article');
      card.className = 'logo-card';
      const links = (ext) => COLORS.map(([c, label]) =>
        `<a href="assets/logo/${ext}/${v.id}-${c}.${ext}" download>${label}</a>`).join('');
      card.innerHTML = `
        <div class="logo-card__view"><img loading="lazy" src="assets/logo/svg/${v.id}-color.svg" alt="${v.name} logo preview"></div>
        <div class="logo-card__meta">
          <h4>${v.name}</h4><p>${v.note}</p>
          <div class="dl"><span class="dl__label">SVG</span>${links('svg')}</div>
          <div class="dl" style="margin-top:6px"><span class="dl__label">PNG</span>${links('png')}</div>
        </div>`;
      grid.appendChild(card);
    });
    const swap = (bg) => {
      grid.dataset.bg = bg;
      document.querySelectorAll('.seg button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.bg === bg)));
      /* color version keeps its dark outline; on light, mono black/teal reads better */
      grid.querySelectorAll('.logo-card__view img').forEach((img) => {
        img.src = img.src.replace(/-(color|black)\.svg$/, bg === 'light' ? '-black.svg' : '-color.svg');
      });
    };
    document.querySelectorAll('.seg button').forEach((b) => b.addEventListener('click', () => swap(b.dataset.bg)));
  }

  /* copy swatches */
  document.querySelectorAll('.swatch').forEach((s) => s.addEventListener('click', () => {
    const hex = s.dataset.hex;
    (navigator.clipboard ? navigator.clipboard.writeText(hex) : Promise.reject()).then(() => say(hex + ' copied'), () => say(hex));
  }));

  /* embers */
  const cv = document.getElementById('embers');
  if (!cv || reduce) return;
  const ctx = cv.getContext('2d');
  let w = 0, h = 0, dpr = 1, parts = [], mx = 0, my = 0, tx = 0, ty = 0, running = true;

  const make = (initial) => ({
    x: Math.random() * w,
    y: initial ? Math.random() * h : h + 10,
    r: Math.random() * 1.7 + 0.4,
    vy: Math.random() * 0.35 + 0.08,
    sway: Math.random() * 40 + 10,
    ph: Math.random() * 6.28,
    sp: Math.random() * 0.6 + 0.2,
    warm: Math.random() < 0.7,
    z: Math.random() * 0.9 + 0.1,
  });
  const resize = () => {
    dpr = Math.min(devicePixelRatio || 1, 2);
    w = cv.clientWidth; h = cv.clientHeight;
    cv.width = w * dpr; cv.height = h * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const n = Math.round(Math.min(110, Math.max(36, (w * h) / 15000)));
    parts = Array.from({ length: n }, () => make(true));
  };
  addEventListener('resize', resize);
  resize();
  addEventListener('pointermove', (e) => { tx = (e.clientX / innerWidth - 0.5) * 2; ty = (e.clientY / innerHeight - 0.5) * 2; }, { passive: true });
  new IntersectionObserver((e) => { running = e[0].isIntersecting; if (running) requestAnimationFrame(frame); }).observe(cv);

  let t = 0;
  function frame() {
    if (!running) return;
    t += 0.016;
    mx += (tx - mx) * 0.04; my += (ty - my) * 0.04;
    ctx.clearRect(0, 0, w, h);
    ctx.globalCompositeOperation = 'lighter';
    for (const p of parts) {
      p.y -= p.vy * (0.5 + p.z);
      const x = p.x + Math.sin(t * p.sp + p.ph) * p.sway + mx * 24 * p.z;
      const y = p.y + my * 14 * p.z;
      if (p.y < -10) Object.assign(p, make(false));
      const fade = Math.min(1, (h - p.y) / (h * 0.25)) * Math.min(1, p.y / (h * 0.3) + 0.15);
      const tw = 0.55 + 0.45 * Math.sin(t * 2 * p.sp + p.ph);
      const a = Math.max(0, fade) * tw * (0.25 + 0.55 * p.z);
      const g = ctx.createRadialGradient(x, y, 0, x, y, p.r * 5);
      const c = p.warm ? '253,233,203' : '138,136,217';
      g.addColorStop(0, `rgba(${c},${a})`);
      g.addColorStop(1, `rgba(${c},0)`);
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.arc(x, y, p.r * 5, 0, 6.283); ctx.fill();
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
