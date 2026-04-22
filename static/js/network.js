(function () {
  'use strict';

  if (document.body.dataset.page !== 'network') return;

  const state = {
    lat: 28.6139,
    lng: 77.2090,
    lastFutures: [],
    lastCredits: []
  };

  async function api(url, options = {}) {
    const defaults = {
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include'
    };
    const res = await fetch(url, { ...defaults, ...options });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Request failed');
    return data;
  }

  function toast(title, message, type = 'info') {
    if (window.showToast) {
      window.showToast(title, message, type);
      return;
    }
    console.log(`[${type}] ${title}: ${message}`);
  }

  function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
  }

  function formToObject(form) {
    return Object.fromEntries(new FormData(form).entries());
  }

  function initReveals() {
    const els = document.querySelectorAll('.network-reveal');
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.16 });
    els.forEach(el => io.observe(el));

    window.addEventListener('scroll', () => {
      const stage = document.querySelector('.network-stage-copy');
      if (!stage) return;
      const y = Math.min(window.scrollY, 420);
      stage.style.transform = `translateY(${y * 0.08}px) scale(${1 + y / 5000})`;
    }, { passive: true });
  }

  function initCanvas() {
    const canvas = document.getElementById('networkCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let width = 0;
    let height = 0;
    const nodes = Array.from({ length: 42 }, (_, i) => ({
      x: Math.random(),
      y: Math.random(),
      z: Math.random() * 0.8 + 0.2,
      vx: (Math.random() - 0.5) * 0.0008,
      vy: (Math.random() - 0.5) * 0.0008,
      hue: i % 4
    }));

    function resize() {
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = width * window.devicePixelRatio;
      canvas.height = height * window.devicePixelRatio;
      ctx.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
    }

    function color(hue, alpha) {
      const palette = [
        `rgba(0,255,136,${alpha})`,
        `rgba(0,212,255,${alpha})`,
        `rgba(255,217,61,${alpha})`,
        `rgba(255,107,107,${alpha})`
      ];
      return palette[hue] || palette[0];
    }

    function frame() {
      ctx.clearRect(0, 0, width, height);
      nodes.forEach((n) => {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > 1) n.vx *= -1;
        if (n.y < 0 || n.y > 1) n.vy *= -1;
      });

      for (let i = 0; i < nodes.length; i += 1) {
        for (let j = i + 1; j < nodes.length; j += 1) {
          const a = nodes[i];
          const b = nodes[j];
          const ax = a.x * width;
          const ay = a.y * height;
          const bx = b.x * width;
          const by = b.y * height;
          const d = Math.hypot(ax - bx, ay - by);
          if (d < 155) {
            ctx.strokeStyle = color(a.hue, (1 - d / 155) * 0.18);
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(ax, ay);
            ctx.lineTo(bx, by);
            ctx.stroke();
          }
        }
      }

      nodes.forEach((n) => {
        const x = n.x * width;
        const y = n.y * height;
        const r = 2 + n.z * 4;
        ctx.fillStyle = color(n.hue, 0.85);
        ctx.beginPath();
        ctx.arc(x, y, r, 0, Math.PI * 2);
        ctx.fill();
      });
      requestAnimationFrame(frame);
    }

    resize();
    window.addEventListener('resize', resize);
    frame();
  }

  async function hydrateLocation() {
    if (!navigator.geolocation) return;
    await new Promise((resolve) => {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          state.lat = pos.coords.latitude;
          state.lng = pos.coords.longitude;
          resolve();
        },
        () => resolve(),
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
      );
    });
  }

  function renderFutures(futures) {
    const ledger = document.getElementById('futuresLedger');
    if (!ledger) return;
    const rows = futures || state.lastFutures;
    if (!rows.length) {
      ledger.innerHTML = '<div class="ledger-empty">No futures minted yet.</div>';
      return;
    }
    ledger.innerHTML = rows.slice(0, 8).map((future) => {
      const stream = future.stream || {};
      const bestMatch = (future.matches || [])[0] || {};
      const partner = bestMatch.ngo || bestMatch.poultry_farm || bestMatch.biogas_plant || {};
      return `
        <div class="ledger-item">
          <div>
            <strong>${stream.token || future.id}</strong>
            <span>${stream.quantity_kg}kg ${stream.stream_type} · ${stream.route}</span>
            <small>${partner.name ? `${partner.name} · ${bestMatch.distance_km} km` : 'No partner match yet'}</small>
          </div>
          <button class="btn btn-ghost bid-btn" data-future-id="${future.id}">Bid</button>
        </div>
      `;
    }).join('');
  }

  function renderCredits(credits) {
    const ledger = document.getElementById('creditsLedger');
    if (!ledger) return;
    const rows = credits || state.lastCredits;
    if (!rows.length) {
      ledger.innerHTML = '<div class="ledger-empty">No credits minted yet.</div>';
      return;
    }
    ledger.innerHTML = rows.slice(0, 8).map((credit) => `
      <div class="ledger-item">
        <div>
          <strong>${credit.kg_co2e} kg CO2e</strong>
          <span>${credit.route_type} · ${credit.distance_km} km · INR ${credit.credit_value_inr}</span>
          <small>${credit.status}${credit.buyer_name ? ` · ${credit.buyer_name}` : ''}</small>
        </div>
        ${credit.status !== 'sold' ? `<button class="btn btn-ghost buy-credit-btn" data-credit-id="${credit.id}">Buy</button>` : ''}
      </div>
    `).join('');
  }

  async function loadOverview() {
    const data = await api(`/api/network/overview?lat=${state.lat}&lng=${state.lng}`);
    const counts = data.network.counts;
    setText('netRestaurants', counts.restaurants.toLocaleString());
    setText('netNgos', counts.ngos.toLocaleString());
    setText('netPoultry', counts.poultry_farms.toLocaleString());
    setText('netBiogas', counts.biogas_plants.toLocaleString());
    state.lastFutures = data.network.recent_futures || [];
    state.lastCredits = data.network.recent_credits || [];
    renderFutures();
    renderCredits();

    const top = data.network.nearby_restaurants?.[0]?.restaurant;
    if (top) {
      const names = ['fiaasRestaurant', 'pwxRestaurant'];
      names.forEach((id) => {
        const el = document.getElementById(id);
        if (el && !el.dataset.touched) el.value = top.name;
      });
    }
  }

  async function submitFiaas(e) {
    e.preventDefault();
    const result = document.getElementById('fiaasResult');
    result.innerHTML = '<div class="ledger-empty">Pricing freshness risk...</div>';
    try {
      const payload = formToObject(e.currentTarget);
      const data = await api('/api/freshness_insurance', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      const c = data.contract;
      result.innerHTML = `
        <div class="result-card success">
          <strong>${c.id}</strong>
          <span>${c.predicted_fresh_hours} guaranteed hours · ${(c.confidence * 100).toFixed(1)}% confidence</span>
          <small>Premium INR ${c.premium_inr} · buffer fund INR ${c.buffer_fund_inr}</small>
        </div>
      `;
      toast('FIaaS Issued', `Premium locked at ${(c.premium_rate * 100).toFixed(2)}%`, 'success');
      loadOverview();
    } catch (err) {
      result.innerHTML = `<div class="result-card error">${err.message}</div>`;
    }
  }

  async function submitPwx(e) {
    e.preventDefault();
    const result = document.getElementById('pwxResult');
    result.innerHTML = '<div class="ledger-empty">Forecasting waste streams...</div>';
    try {
      const payload = formToObject(e.currentTarget);
      payload.lat = state.lat;
      payload.lng = state.lng;
      const data = await api('/api/pwx/futures', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      state.lastFutures = [...data.futures, ...state.lastFutures];
      renderFutures(state.lastFutures);
      result.innerHTML = `
        <div class="result-card success">
          <strong>${data.created} futures minted</strong>
          <span>${data.futures.map(f => f.stream.token).join(', ')}</span>
          <small>Prediction logs stored with status predicted.</small>
        </div>
      `;
      toast('PWX Futures Open', `${data.created} tokenized streams are ready for bids.`, 'success');
    } catch (err) {
      result.innerHTML = `<div class="result-card error">${err.message}</div>`;
    }
  }

  async function submitGcnc(e) {
    e.preventDefault();
    const result = document.getElementById('gcncResult');
    result.innerHTML = '<div class="ledger-empty">Calculating route-sensitive carbon value...</div>';
    try {
      const payload = formToObject(e.currentTarget);
      payload.status = 'verified';
      const data = await api('/api/gcnc/credits', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      const c = data.credit;
      state.lastCredits = [c, ...state.lastCredits];
      renderCredits(state.lastCredits);
      result.innerHTML = `
        <div class="result-card success">
          <strong>${c.kg_co2e} kg CO2e</strong>
          <span>Credit value INR ${c.credit_value_inr} · platform fee INR ${c.platform_fee_inr}</span>
          <small>${c.formula}</small>
        </div>
      `;
      toast('G-CNC Minted', `${c.kg_co2e} kg CO2e credit created.`, 'success');
    } catch (err) {
      result.innerHTML = `<div class="result-card error">${err.message}</div>`;
    }
  }

  async function placeBid(futureId) {
    const future = state.lastFutures.find(f => f.id === futureId);
    const qty = future?.stream?.quantity_kg || 10;
    const price = future?.stream?.route === 'ngo' ? 0 : Math.max(4, future?.stream?.base_price_per_kg || 4);
    try {
      const data = await api('/api/pwx/bid', {
        method: 'POST',
        body: JSON.stringify({
          future_id: futureId,
          bidder_name: future?.stream?.route === 'biogas' ? 'Delhi Biogas Plant' : 'City Poultry Feed Partner',
          bidder_type: future?.stream?.route === 'biogas' ? 'biogas_plant' : 'poultry_farm',
          quantity_kg: qty,
          price_per_kg: price
        })
      });
      state.lastFutures = [data.future, ...state.lastFutures.filter(f => f.id !== futureId)];
      renderFutures(state.lastFutures);
      toast(data.bid.accepted ? 'Bid Matched' : 'Bid Logged', `Gross value INR ${data.bid.gross_value_inr}`, data.bid.accepted ? 'success' : 'info');
    } catch (err) {
      toast('Bid Failed', err.message, 'error');
    }
  }

  async function buyCredit(creditId) {
    try {
      const data = await api('/api/buy_credit', {
        method: 'POST',
        body: JSON.stringify({
          credit_id: creditId,
          buyer_name: document.getElementById('gcncBuyer')?.value || 'Corporate buyer'
        })
      });
      state.lastCredits = [data.credit, ...state.lastCredits.filter(c => c.id !== creditId)];
      renderCredits(state.lastCredits);
      toast('Credit Purchased', `${data.credit.kg_co2e} kg CO2e retired locally.`, 'success');
    } catch (err) {
      toast('Purchase Failed', err.message, 'error');
    }
  }

  function bindEvents() {
    document.getElementById('fiaasForm')?.addEventListener('submit', submitFiaas);
    document.getElementById('pwxForm')?.addEventListener('submit', submitPwx);
    document.getElementById('gcncForm')?.addEventListener('submit', submitGcnc);
    document.addEventListener('click', (e) => {
      const bid = e.target.closest('.bid-btn');
      if (bid) placeBid(bid.dataset.futureId);
      const buy = e.target.closest('.buy-credit-btn');
      if (buy) buyCredit(buy.dataset.creditId);
    });
    document.querySelectorAll('#fiaasRestaurant,#pwxRestaurant').forEach((input) => {
      input.addEventListener('input', () => { input.dataset.touched = 'true'; });
    });
  }

  async function init() {
    initCanvas();
    initReveals();
    bindEvents();
    loadOverview().catch(err => toast('Network Load Failed', err.message, 'error'));
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
