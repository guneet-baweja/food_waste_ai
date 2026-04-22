/**
 * FoodSave AI — Main JavaScript Module
 * Handles: Auth, API calls, Dashboard, Donate Page,
 * NGO Portal, Notifications, Admin Panel, Toast system
 * 20+ functions, fully modular
 */

(function () {
  'use strict';

  /* ═══════════════════════════════════════════
     CONSTANTS & STATE
  ═══════════════════════════════════════════ */

  const API = {
    session:      '/api/session',
    signup:       '/api/signup',
    login:        '/api/login',
    logout:       '/api/logout',
    uploadFood:   '/api/upload_food',
    getDonations: '/api/get_donations',
    accept:       '/api/accept_donation',
    complete:     '/api/complete_donation',
    leaderboard:  '/api/leaderboard',
    stats:        '/api/stats',
    notifications:'/api/notifications',
    profile:      '/api/user/profile',
    nearbyEntities: '/api/nearby_entities',
    adminUsers:   '/api/admin/users',
    adminApprove: '/api/admin/approve',
    adminDelete:  '/api/admin/delete',
    dashboardAnalytics: '/api/dashboard_analytics'
  };

  // App state
  let currentUser = null;
  const page = document.body.dataset.page;
  const chartRegistry = {};

  /* ═══════════════════════════════════════════
     1. TOAST NOTIFICATION SYSTEM
  ═══════════════════════════════════════════ */

  function showToast(title, message, type = 'info', duration = 4000) {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <div class="toast-icon">${icons[type] || 'ℹ️'}</div>
      <div class="toast-body">
        <div class="toast-title">${title}</div>
        ${message ? `<div class="toast-msg">${message}</div>` : ''}
      </div>
      <div class="toast-close">✕</div>
    `;

    container.appendChild(toast);

    toast.querySelector('.toast-close').addEventListener('click', () => removeToast(toast));

    const timer = setTimeout(() => removeToast(toast), duration);
    toast._timer = timer;
  }

  window.showToast = showToast;

  function removeToast(toast) {
    clearTimeout(toast._timer);
    toast.classList.add('removing');
    setTimeout(() => toast.remove(), 300);
  }

  /* ═══════════════════════════════════════════
     2. API FETCH HELPER
  ═══════════════════════════════════════════ */

  async function apiFetch(url, options = {}) {
    try {
      const defaults = {
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      };

      // Don't set Content-Type for FormData
      if (options.body instanceof FormData) {
        delete defaults.headers['Content-Type'];
      }

      const res = await fetch(url, { ...defaults, ...options });
      const data = await res.json();

      if (!res.ok && data.error) {
        throw new Error(data.error);
      }

      return data;
    } catch (err) {
      throw err;
    }
  }

  /* ═══════════════════════════════════════════
     3. SESSION CHECK
  ═══════════════════════════════════════════ */

  async function checkSession() {
    try {
      const data = await apiFetch(API.session);
      if (data.logged_in && data.user) {
        currentUser = data.user;
        window._currentUser = data.user;
        // Also save to localStorage as backup
        localStorage.setItem('foodsave_user', JSON.stringify(data.user));
        updateNavAuth(data.user);
        return data.user;
      } else {
        currentUser = null;
        localStorage.removeItem('foodsave_user');
        updateNavAuth(null);
        return null;
      }
    } catch (err) {
      // Fallback to localStorage
      const cached = localStorage.getItem('foodsave_user');
      if (cached) {
        try {
          currentUser = JSON.parse(cached);
          updateNavAuth(currentUser);
          return currentUser;
        } catch {}
      }
      return null;
    }
  }

  /* ═══════════════════════════════════════════
     4. UPDATE NAV AUTH AREA
  ═══════════════════════════════════════════ */

  function updateNavAuth(user) {
    const area = document.getElementById('navAuthArea');
    if (!area) return;

    if (user) {
      area.innerHTML = `
        <a href="/dashboard" class="btn btn-ghost" style="font-size:0.85rem">
          <span>${user.name.split(' ')[0]}</span>
          <span style="background:var(--grad-primary);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-left:4px">${user.points} pts</span>
        </a>
      `;
    } else {
      area.innerHTML = `
        <a href="/login" class="btn btn-ghost">Login</a>
        <a href="/signup" class="btn btn-primary">Get Started</a>
      `;
    }
  }

  /* ═══════════════════════════════════════════
     5. RELATIVE TIME HELPER
  ═══════════════════════════════════════════ */

  function relativeTime(isoString) {
    const date = new Date(isoString);
    const now  = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60)     return `${diff}s ago`;
    if (diff < 3600)   return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400)  return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }

  /* ═══════════════════════════════════════════
     6. FORMAT URGENCY BADGE HTML
  ═══════════════════════════════════════════ */

  function urgencyBadgeHTML(urgency) {
    const labels = {
      critical: '🆘 Critical',
      high:     '⚠️ High',
      medium:   '📦 Medium',
      low:      '✅ Low',
      safe:     '🌿 Safe',
      expired:  '💀 Expired'
    };
    return `<span class="urgency-badge ${urgency}">${labels[urgency] || urgency}</span>`;
  }

  /* ═══════════════════════════════════════════
     7. RENDER DONATION CARD (NGO/list view)
  ═══════════════════════════════════════════ */

  function renderDonationCard(d, showActions = true) {
    const imageHTML = d.image
      ? `<div class="dc-food-img"><img src="${d.image}" alt="${d.food_name}" /></div>`
      : `<div class="dc-food-img">${getFoodEmoji(d.food_type)}</div>`;

    const canAccept = showActions &&
                      d.status === 'available' &&
                      currentUser &&
                      ['volunteer', 'ngo', 'admin'].includes(currentUser.role);

    const canComplete = showActions &&
                        d.status === 'accepted' &&
                        currentUser &&
                        (d.accepted_by === currentUser.id || currentUser.role === 'admin');

    const actionsHTML = `
      <div class="dc-freshness">
        ${d.freshness_score}<small>/ 100</small>
      </div>
      ${urgencyBadgeHTML(d.urgency)}
      <span class="dc-status-badge ${d.status}">${d.status.charAt(0).toUpperCase() + d.status.slice(1)}</span>
      ${canAccept ? `<button class="btn btn-primary" style="width:100%;margin-top:0.5rem;font-size:0.82rem;padding:0.5rem" onclick="window.ngoApp.acceptDonation('${d.id}')">Accept Pickup</button>` : ''}
      ${canComplete ? `<button class="btn btn-outline" style="width:100%;margin-top:0.5rem;font-size:0.82rem;padding:0.5rem;color:var(--accent-blue)" onclick="window.ngoApp.completeDonation('${d.id}')">Mark Complete</button>` : ''}
      <button class="btn btn-ghost" style="width:100%;margin-top:0.25rem;font-size:0.78rem;padding:0.4rem" onclick="window.ngoApp.showDetail('${d.id}')">Details</button>
    `;

    return `
      <div class="donation-card ${d.urgency}" data-id="${d.id}">
        ${imageHTML}
        <div class="dc-info">
          <div class="dc-name">${d.food_name}</div>
          <div class="dc-meta">
            <span>📦 ${d.quantity} ${d.quantity_unit}</span>
            <span>📍 ${d.location}</span>
            <span>⏱ ${d.hours_remaining > 0 ? d.hours_remaining + 'h left' : 'Expired'}</span>
            <span>👤 ${d.donor_name}</span>
          </div>
          <div class="dc-desc">${d.description || 'No description provided.'}</div>
          <div class="dc-tags">
            <span class="dc-tag">${d.food_type}</span>
            <span class="dc-tag">🌿 ${d.co2_saved}kg CO₂</span>
            <span class="dc-tag">${relativeTime(d.created_at)}</span>
          </div>
        </div>
        <div class="dc-actions">${actionsHTML}</div>
      </div>
    `;
  }

  function getFoodEmoji(type) {
    const emojis = {
      cooked: '🍛', raw: '🥦', bakery: '🍞',
      dairy: '🧀', packaged: '📦', other: '🥡'
    };
    return emojis[type] || '🍽️';
  }

  /* ═══════════════════════════════════════════
     LOGIN PAGE
  ═══════════════════════════════════════════ */

  function initLoginPage() {
    const form     = document.getElementById('loginForm');
    const errorEl  = document.getElementById('loginError');
    const passToggle = document.getElementById('passwordToggle');
    const passInput  = document.getElementById('loginPassword');

    if (!form) return;

    // Demo account buttons
    document.querySelectorAll('.demo-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.getElementById('loginEmail').value = btn.dataset.email;
        document.getElementById('loginPassword').value = btn.dataset.pass;
      });
    });

    // Password toggle
    passToggle?.addEventListener('click', () => {
      passInput.type = passInput.type === 'password' ? 'text' : 'password';
      passToggle.textContent = passInput.type === 'password' ? '👁️' : '🙈';
    });

    // Form submit
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorEl.style.display = 'none';

      const btn = document.getElementById('loginSubmit');
      setLoading(btn, true);

      try {
        const data = await apiFetch(API.login, {
          method: 'POST',
          body: JSON.stringify({
            email: form.email.value.trim(),
            password: form.password.value
          })
        });

        if (data.success) {
          currentUser = data.user;
          localStorage.setItem('foodsave_user', JSON.stringify(data.user));
          showToast('Welcome back!', `Hello, ${data.user.name}! 🎉`, 'success');
          setTimeout(() => { window.location.href = '/dashboard'; }, 1000);
        }
      } catch (err) {
        errorEl.textContent = err.message || 'Login failed. Please check your credentials.';
        errorEl.style.display = 'block';
        setLoading(btn, false);
      }
    });
  }

  /* ═══════════════════════════════════════════
     SIGNUP PAGE
  ═══════════════════════════════════════════ */

  function initSignupPage() {
    const form        = document.getElementById('signupForm');
    const errorEl     = document.getElementById('signupError');
    const roleSelector= document.getElementById('roleSelector');
    const roleHidden  = document.getElementById('roleHidden');
    const approvalNotice = document.getElementById('approvalNotice');
    const passToggle  = document.getElementById('passwordToggle');
    const passInput   = document.getElementById('signupPassword');

    if (!form) return;

    // Role selector
    roleSelector?.querySelectorAll('.role-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        roleSelector.querySelectorAll('.role-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        roleHidden.value = btn.dataset.role;

        const needsApproval = ['ngo', 'restaurant'].includes(btn.dataset.role);
        if (approvalNotice) {
          approvalNotice.style.display = needsApproval ? 'block' : 'none';
        }
      });
    });

    // Password toggle
    passToggle?.addEventListener('click', () => {
      passInput.type = passInput.type === 'password' ? 'text' : 'password';
      passToggle.textContent = passInput.type === 'password' ? '👁️' : '🙈';
    });

    // Form submit
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      errorEl.style.display = 'none';

      const btn = document.getElementById('signupSubmit');
      setLoading(btn, true);

      try {
        const data = await apiFetch(API.signup, {
          method: 'POST',
          body: JSON.stringify({
            name:     form.name.value.trim(),
            email:    form.email.value.trim(),
            password: form.password.value,
            role:     roleHidden.value,
            location: form.location.value.trim()
          })
        });

        if (data.success) {
          currentUser = data.user;
          localStorage.setItem('foodsave_user', JSON.stringify(data.user));
          showToast('Account Created!', `Welcome, ${data.user.name}! +50 bonus points! 🎉`, 'success');
          setTimeout(() => { window.location.href = '/dashboard'; }, 1200);
        }
      } catch (err) {
        errorEl.textContent = err.message || 'Signup failed. Please try again.';
        errorEl.style.display = 'block';
        setLoading(btn, false);
      }
    });
  }

  /* ═══════════════════════════════════════════
     DONATE PAGE
  ═══════════════════════════════════════════ */

  function initDonatePage() {
    const form       = document.getElementById('donateForm');
    const loginPrompt= document.getElementById('loginPrompt');
    if (!form) return;

    // Show login prompt if not logged in
    async function checkDonateAuth() {
      const user = await checkSession();
      if (!user) {
        form.style.display = 'none';
        if (loginPrompt) loginPrompt.style.display = 'block';
      } else {
        form.style.display = 'flex';
        if (loginPrompt) loginPrompt.style.display = 'none';
      }
    }

    checkDonateAuth();

    // Set min expiry time to now+1 hour
    const expiryInput = document.getElementById('expiryTime');
    if (expiryInput) {
      const minTime = new Date(Date.now() + 3600000);
      expiryInput.min = minTime.toISOString().slice(0, 16);
      expiryInput.value = new Date(Date.now() + 21600000).toISOString().slice(0, 16);
    }

    // Food type selector
    document.querySelectorAll('.type-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById('foodTypeHidden').value = btn.dataset.type;
      });
    });

    function hasCapturedLocation() {
      const latRaw = document.getElementById('latHidden')?.value.trim();
      const lngRaw = document.getElementById('lngHidden')?.value.trim();
      if (!latRaw || !lngRaw) return false;

      const lat = Number(latRaw);
      const lng = Number(lngRaw);
      return Number.isFinite(lat) && Number.isFinite(lng)
        && lat >= -90 && lat <= 90
        && lng >= -180 && lng <= 180;
    }

    function isLocalHost() {
      return ['localhost', '127.0.0.1', '[::1]', '::1'].includes(window.location.hostname);
    }

    function locationOriginMessage() {
      if (window.isSecureContext || isLocalHost()) {
        return '';
      }

      const port = window.location.port ? `:${window.location.port}` : '';
      return `Chrome blocks GPS on this address. Open http://localhost${port}/donate and allow location access.`;
    }

    function geolocationErrorMessage(err) {
      const originMessage = locationOriginMessage();
      if (originMessage) return originMessage;

      if (err?.code === 1) return 'Location permission was blocked. Allow location access in the browser and try again.';
      if (err?.code === 2) return 'Your device could not find a GPS position. Check Wi-Fi/GPS and try again.';
      if (err?.code === 3) return 'Location request timed out. Try again near a window or with GPS enabled.';
      return 'Could not access your location.';
    }

    async function capturePickupLocation({ silent = false } = {}) {
      if (!navigator.geolocation) {
        if (!silent) showToast('Not Supported', 'Geolocation is not supported by your browser', 'warning');
        return false;
      }

      const originMessage = locationOriginMessage();
      if (originMessage) {
        if (!silent) showToast('Location Blocked', originMessage, 'error', 8000);
        return false;
      }

      if (detectBtn) {
        detectBtn.textContent = '⏳';
        detectBtn.disabled = true;
      }

      return new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;
            const accuracy = pos.coords.accuracy ? Math.round(pos.coords.accuracy) : null;
            const locationInput = document.getElementById('location');

            document.getElementById('latHidden').value = lat;
            document.getElementById('lngHidden').value = lng;

            if (locationInput && (!locationInput.value.trim() || locationInput.dataset.gpsFilled === 'true')) {
              locationInput.value = accuracy
                ? `GPS: ${lat.toFixed(6)}, ${lng.toFixed(6)} (accuracy ${accuracy}m)`
                : `GPS: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
              locationInput.dataset.gpsFilled = 'true';
            }

            if (detectBtn) {
              detectBtn.textContent = '✅';
              detectBtn.disabled = false;
            }
            if (!silent) showToast('Location Detected', 'GPS coordinates saved for NGO pickup matching.', 'success');
            resolve(true);
          },
          (err) => {
            if (detectBtn) {
              detectBtn.textContent = '📍';
              detectBtn.disabled = false;
            }
            if (!silent) showToast('Location Error', geolocationErrorMessage(err), 'error', 8000);
            resolve(false);
          },
          { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
        );
      });
    }

    // Detect location
    const detectBtn = document.getElementById('detectLocation');
    detectBtn?.addEventListener('click', () => capturePickupLocation());

    // Image upload preview
    const uploadZone  = document.getElementById('uploadZone');
    const fileInput   = document.getElementById('foodImage');
    const previewWrap = document.getElementById('imagePreview');
    const previewImg  = document.getElementById('previewImg');
    const removeBtn   = document.getElementById('removeImg');

    fileInput?.addEventListener('change', () => {
      const file = fileInput.files[0];
      if (file) {
        showImagePreview(file);
        capturePickupLocation();
      }
    });

    // Drag & drop
    uploadZone?.addEventListener('dragover', (e) => {
      e.preventDefault();
      uploadZone.classList.add('dragging');
    });

    uploadZone?.addEventListener('dragleave', () => {
      uploadZone.classList.remove('dragging');
    });

    uploadZone?.addEventListener('drop', (e) => {
      e.preventDefault();
      uploadZone.classList.remove('dragging');
      const file = e.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        showImagePreview(file);
        capturePickupLocation();
      }
    });

    function showImagePreview(file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        previewImg.src = e.target.result;
        previewWrap.style.display = 'block';
        uploadZone.style.display = 'none';
      };
      reader.readAsDataURL(file);
    }

    removeBtn?.addEventListener('click', () => {
      previewImg.src = '';
      previewWrap.style.display = 'none';
      uploadZone.style.display = 'block';
      fileInput.value = '';
    });

    // Form submit
    form.addEventListener('submit', async (e) => {
      e.preventDefault();

      const btn = document.getElementById('submitDonation');
      const btnText = btn.querySelector('.btn-text');
      const btnLoader = btn.querySelector('.btn-loader');

      btnText.style.display = 'none';
      btnLoader.style.display = 'block';
      btn.disabled = true;

      try {
        if (!hasCapturedLocation()) {
          const captured = await capturePickupLocation({ silent: true });
          if (!captured) {
            throw new Error(geolocationErrorMessage());
          }
        }

        const formData = new FormData(form);
        const data = await apiFetch(API.uploadFood, {
          method: 'POST',
          body: formData
        });

        if (data.success) {
          // Show AI prediction
          showAIPrediction(data.ai_prediction);
          showMatchResults(data.matches);

          showToast('Donation Listed! 🍽️', `+100 points earned! ${data.ai_prediction.urgency.toUpperCase()} urgency detected.`, 'success', 6000);
          btnText.style.display = 'block';
          btnLoader.style.display = 'none';
          btn.disabled = false;
        }
      } catch (err) {
        showToast('Upload Failed', err.message || 'Could not list donation. Please try again.', 'error');
        btnText.style.display = 'block';
        btnLoader.style.display = 'none';
        btn.disabled = false;
      }
    });

    // Load urgent donations in sidebar
    loadUrgentDonations();
    loadImpactMini();
  }

  function showMatchResults(matches) {
    const card = document.getElementById('matchResults');
    const list = document.getElementById('matchResultsList');
    const route = document.getElementById('matchRoute');
    if (!card || !list || !matches) return;

    const ngos = matches.ngos || [];
    const farms = matches.poultry_farms || [];
    const routeLabels = {
      ngo: 'NGO relief route',
      poultry_farm: 'Poultry feed route',
      poultry_or_biogas: 'Animal feed or biogas',
      biogas: 'Biogas route',
      manual_review: 'Manual review'
    };
    if (route) route.textContent = routeLabels[matches.recommended_route] || 'Smart route';

    const rows = [
      ...ngos.slice(0, 4).map(m => ({ kind: 'NGO', icon: '🏥', entity: m.ngo, ...m })),
      ...farms.slice(0, 3).map(m => ({ kind: 'Farm', icon: '🐔', entity: m.poultry_farm, ...m }))
    ];

    if (!rows.length) {
      list.innerHTML = '<div class="nearby-empty">No verified partner found near this pickup yet. The donation is still listed for manual acceptance.</div>';
    } else {
      list.innerHTML = rows.map(row => `
        <div class="match-result-item">
          <div class="match-rank">${row.icon}</div>
          <div class="match-copy">
            <strong>${row.entity?.name || 'Partner'}</strong>
            <span>${row.kind} · ${row.distance_km} km · score ${row.score}</span>
            <small>${row.reason}</small>
          </div>
          <div class="match-accuracy ${row.location_accuracy === 'exact' ? 'exact' : 'estimated'}">
            ${row.location_accuracy === 'exact' ? 'GPS' : 'Estimated'}
          </div>
        </div>
      `).join('');
    }

    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  function showAIPrediction(pred) {
    const card     = document.getElementById('aiPrediction');
    const bodyEl   = document.getElementById('aiPredictionBody');

    if (!card || !bodyEl) return;

    card.style.display = 'block';

    const active = pred || {};
    const expiry = pred.expiry_prediction || null;
    const model = pred.model_prediction || null;

    function meter(score, label, meta, urgency, extra = '') {
      const safeScore = Number.isFinite(score) ? Math.max(0, Math.min(100, score)) : 0;
      let fillBackground = 'var(--grad-primary)';
      if (safeScore < 70 && safeScore >= 40) fillBackground = 'linear-gradient(90deg, #ffd93d, #ffa500)';
      if (safeScore < 40) fillBackground = 'linear-gradient(90deg, #ff6b6b, #ff4444)';
      return `
        <div class="prediction-mode-card">
          <div class="prediction-mode-head">
            <strong>${label}</strong>
            ${urgency ? `<span class="urgency-badge ${urgency}">${urgency.replace('_', ' ')}</span>` : ''}
          </div>
          <div class="freshness-meter">
            <div class="freshness-label">Freshness Score</div>
            <div class="freshness-bar">
              <div class="freshness-fill" style="width:${safeScore}%;background:${fillBackground}"></div>
            </div>
            <div class="freshness-num">${safeScore} / 100</div>
          </div>
          <div class="hours-left">${meta || ''}</div>
          ${extra}
        </div>
      `;
    }

    const activeMeta = active.hours_remaining > 0
      ? `⏱ ${active.hours_remaining} hours remaining`
      : active.hours_remaining === 0
        ? '⚠️ Already expired'
        : (active.predicted_class ? `Classified as ${active.predicted_class}` : '');

    const blocks = [
      meter(
        active.freshness_score,
        `Active Result · ${active.selected_mode || active.prediction_source || 'prediction'}`,
        activeMeta,
        active.urgency,
        [
          active.model_confidence ? `<div class="form-hint">Trained model confidence: ${active.model_confidence}%</div>` : '',
          active.recommended_route ? `<div class="form-hint">Recommended route: ${active.recommended_route}</div>` : ''
        ].filter(Boolean).join('')
      )
    ];

    if (expiry) {
      blocks.push(
        meter(
          expiry.freshness_score,
          'Expiry-based result',
          expiry.hours_remaining > 0 ? `⏱ ${expiry.hours_remaining} hours remaining` : '⚠️ Already expired',
          expiry.urgency
        )
      );
    }

    if (model?.available) {
      blocks.push(
        meter(
          model.freshness_score,
          `Trained model result · ${model.model_name || 'model'}`,
          `Confidence: ${model.confidence}% · Class: ${model.predicted_class}`,
          model.urgency,
          [
            model.checkpoint_name ? `<div class="form-hint">Checkpoint: ${model.checkpoint_name}</div>` : '',
            model.probabilities ? `<div class="form-hint">Top class comes from your trained image model.</div>` : ''
          ].filter(Boolean).join('')
        )
      );
    } else if (active.selected_mode !== 'expiry') {
      blocks.push(`
        <div class="prediction-mode-card prediction-mode-muted">
          <div class="prediction-mode-head">
            <strong>Trained model status</strong>
          </div>
          <div class="hours-left">${model?.reason || 'The trained image model is not available in this runtime yet.'}</div>
        </div>
      `);
    }

    bodyEl.innerHTML = blocks.join('');
  }

  async function loadUrgentDonations() {
    const container = document.getElementById('urgentDonations');
    if (!container) return;

    try {
      const data = await apiFetch(`${API.getDonations}?status=available&urgency=critical`);
      const critical = data.donations || [];

      // Also fetch high urgency
      const data2 = await apiFetch(`${API.getDonations}?status=available&urgency=high`);
      const all = [...critical, ...(data2.donations || [])].slice(0, 5);

      if (!all.length) {
        container.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem;text-align:center">No urgent donations at the moment ✅</p>';
        return;
      }

      container.innerHTML = all.map(d => `
        <div class="urgent-item">
          <div class="urgent-urg"></div>
          <div class="urgent-info">
            <div class="urgent-name">${d.food_name}</div>
            <div class="urgent-meta">${d.location} · ${d.hours_remaining}h left</div>
          </div>
          <a href="/ngo" class="urgent-btn">Accept</a>
        </div>
      `).join('');
    } catch (err) {
      container.innerHTML = '<p style="color:var(--text-muted);font-size:0.85rem">Unable to load</p>';
    }
  }

  async function loadImpactMini() {
    try {
      const profileData = await apiFetch(API.profile);
      if (!profileData.success) return;
      const user = profileData.user;

      const setEl = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
      };

      setEl('impactWeekDonations', user.total_donations || 0);
      setEl('impactWeekCO2', (user.co2_saved || 0).toFixed(1) + ' kg');
      setEl('impactWeekPoints', user.points || 0);
    } catch {}
  }

  /* ═══════════════════════════════════════════
     NGO PORTAL PAGE
  ═══════════════════════════════════════════ */

  function initNGOPage() {
    const list = document.getElementById('donationsList');
    if (!list) return;

    let allDonations = [];
    let ngoSearchLocation = null;

    async function loadDonations() {
      list.innerHTML = `<div class="loading-state"><div class="loading-spinner"></div>Loading donations...</div>`;

      try {
        const statusEl = document.querySelector('input[name="statusFilter"]:checked');
        const status   = statusEl ? statusEl.value : 'available';
        const foodType = document.getElementById('foodTypeFilter')?.value || '';

        let url = API.getDonations + '?limit=50';
        if (status) url += `&status=${status}`;
        if (foodType) url += `&food_type=${foodType}`;
        if (ngoSearchLocation) {
          url += `&lat=${ngoSearchLocation.lat}&lng=${ngoSearchLocation.lng}&radius_km=${ngoSearchLocation.radius}`;
        }

        const data = await apiFetch(url);
        let donations = data.donations || [];

        // Filter by checked urgencies
        const checkedUrgencies = Array.from(
          document.querySelectorAll('.urgency-cb:checked')
        ).map(cb => cb.value);

        if (checkedUrgencies.length > 0) {
          donations = donations.filter(d => checkedUrgencies.includes(d.urgency));
        }

        // Sort
        const sort = document.getElementById('sortSelect')?.value;
        if (sort === 'time') {
          donations.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
        } else if (sort === 'quantity') {
          donations.sort((a, b) => b.quantity - a.quantity);
        }

        allDonations = donations;

        // Update count
        const countEl = document.getElementById('donationCount');
        if (countEl) countEl.textContent = donations.length;

        // Update summary
        updateNGOSummary(data.donations || []);

        if (!donations.length) {
          list.innerHTML = '<div class="loading-state">No donations found matching your filters.</div>';
          return;
        }

        list.innerHTML = donations.map(d => renderDonationCard(d)).join('');
        // Initialize map with donation pins
if (!window.MapModule._mapInitialized) {
  window.MapModule.initMap('donationMap', 20.5937, 78.9629, 5);
  window.MapModule.initToggle();
  window.MapModule._mapInitialized = true;
}
window.MapModule.addDonationMarkers(donations);

// Load NGOs and biogas on map too
fetch('/api/locations')
  .then(r => r.json())
  .then(data => {
    if (data.ngos)   window.MapModule.addNGOMarkers(data.ngos);
    if (data.biogas) window.MapModule.addBiogasMarkers(data.biogas);
    if (data.poultry_farms) window.MapModule.addPoultryMarkers(data.poultry_farms);
  }).catch(() => {});

      } catch (err) {
        list.innerHTML = `<div class="loading-state" style="color:var(--accent-red)">Error: ${err.message}</div>`;
      }
    }

    function updateNGOSummary(donations) {
      const available = donations.filter(d => d.status === 'available').length;
      const critical  = donations.filter(d => d.urgency === 'critical' && d.status === 'available').length;
      const accepted  = donations.filter(d => d.status === 'accepted').length;
      const completed = donations.filter(d => d.completed).length;

      const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
      set('sumAvailable', available);
      set('sumCritical', critical);
      set('sumAccepted', accepted);
      set('sumCompleted', completed);
    }

    // Accept donation
    async function acceptDonation(id) {
      if (!currentUser) {
        showToast('Login Required', 'Please login to accept donations', 'warning');
        setTimeout(() => { window.location.href = '/login'; }, 1500);
        return;
      }

      try {
        const data = await apiFetch(API.accept, {
          method: 'POST',
          body: JSON.stringify({ donation_id: id })
        });

        showToast('Pickup Accepted! 🚗', data.message, 'success');
        loadDonations();
      } catch (err) {
        showToast('Error', err.message, 'error');
      }
    }

    // Complete donation
    async function completeDonation(id) {
      try {
        const data = await apiFetch(API.complete, {
          method: 'POST',
          body: JSON.stringify({ donation_id: id })
        });

        showToast('Delivery Completed! 🎉', `+150 points! ${data.co2_saved}kg CO₂ saved!`, 'success');
        loadDonations();
      } catch (err) {
        showToast('Error', err.message, 'error');
      }
    }

    // Show donation detail modal
    function showDetail(id) {
      const donation = allDonations.find(d => d.id === id);
      if (!donation) return;

      const modal   = document.getElementById('donationModal');
      const body    = document.getElementById('modalBody');
      if (!modal || !body) return;

      body.innerHTML = `
        <div style="margin-top:1rem">
          <h2 style="font-family:var(--font-display);font-size:1.6rem;font-weight:800;margin-bottom:1rem">${donation.food_name}</h2>
          ${donation.image ? `<img src="${donation.image}" style="width:100%;height:200px;object-fit:cover;border-radius:var(--radius-md);margin-bottom:1.25rem" />` : ''}
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1.5rem">
            <div style="background:var(--bg-secondary);border-radius:var(--radius-sm);padding:1rem;border:1px solid var(--border-color)">
              <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.3rem">Freshness Score</div>
              <div style="font-size:2rem;font-weight:800;font-family:var(--font-display);color:var(--accent-green)">${donation.freshness_score}<span style="font-size:1rem;color:var(--text-muted)">/100</span></div>
            </div>
            <div style="background:var(--bg-secondary);border-radius:var(--radius-sm);padding:1rem;border:1px solid var(--border-color)">
              <div style="font-size:0.72rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.3rem">Urgency</div>
              ${urgencyBadgeHTML(donation.urgency)}
            </div>
          </div>
          <table style="width:100%;font-size:0.88rem;border-collapse:collapse">
            ${[
              ['Donor', donation.donor_name],
              ['Quantity', `${donation.quantity} ${donation.quantity_unit}`],
              ['Type', donation.food_type],
              ['Location', donation.location],
              ['Expires', new Date(donation.expiry_time).toLocaleString()],
              ['CO₂ Saved', `${donation.co2_saved} kg`],
              ['Status', donation.status],
              ['Listed', relativeTime(donation.created_at)]
            ].map(([k, v]) => `
              <tr>
                <td style="padding:0.6rem 0;border-bottom:1px solid var(--border-color);color:var(--text-muted);font-weight:600;width:120px">${k}</td>
                <td style="padding:0.6rem 0;border-bottom:1px solid var(--border-color);color:var(--text-primary)">${v}</td>
              </tr>
            `).join('')}
          </table>
          ${donation.description ? `<p style="color:var(--text-secondary);margin-top:1rem;font-size:0.9rem;line-height:1.6">${donation.description}</p>` : ''}
          <div style="margin-top:1.5rem;display:flex;gap:0.75rem">
            ${donation.status === 'available' && currentUser && ['volunteer','ngo','admin'].includes(currentUser.role) ? `
              <button class="btn btn-primary" style="flex:1" onclick="window.ngoApp.acceptDonation('${donation.id}');document.getElementById('donationModal').style.display='none'">
                🚗 Accept Pickup
              </button>
            ` : ''}
            <button class="btn btn-ghost" onclick="document.getElementById('donationModal').style.display='none'">Close</button>
          </div>
        </div>
      `;

      modal.style.display = 'flex';
    }

    // Filter & sort controls
    document.getElementById('applyFilters')?.addEventListener('click', loadDonations);
    document.getElementById('resetFilters')?.addEventListener('click', () => {
      document.querySelectorAll('.urgency-cb').forEach(cb => { cb.checked = true; });
      document.getElementById('foodTypeFilter').value = '';
      document.querySelector('input[name="statusFilter"][value="available"]').checked = true;
      loadDonations();
    });

    document.getElementById('sortSelect')?.addEventListener('change', loadDonations);

    async function detectNGOLocation() {
      if (!navigator.geolocation) {
        showToast('Not Supported', 'Geolocation is not supported by your browser', 'warning');
        return null;
      }
      return new Promise((resolve) => {
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
          () => resolve(null),
          { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 }
        );
      });
    }

    async function findNearbyRestaurants() {
      const container = document.getElementById('nearbyRestaurants');
      const radius = document.getElementById('restaurantRadius')?.value || '10';
      const btn = document.getElementById('findRestaurantsBtn');
      if (!container) return;

      container.innerHTML = '<div class="nearby-empty">Finding restaurants and sorting by distance...</div>';
      if (btn) btn.disabled = true;

      const loc = await detectNGOLocation();
      if (!loc) {
        container.innerHTML = '<div class="nearby-empty">Location permission is needed to search nearby restaurants.</div>';
        showToast('Location Needed', 'Allow GPS access so nearby restaurants can be ranked accurately.', 'warning');
        if (btn) btn.disabled = false;
        return;
      }

      ngoSearchLocation = { ...loc, radius };

      try {
        const data = await apiFetch(`${API.nearbyEntities}?lat=${loc.lat}&lng=${loc.lng}&radius_km=${radius}&limit=10`);
        const restaurants = data.restaurants || [];
        if (!restaurants.length) {
          container.innerHTML = '<div class="nearby-empty">No restaurants found in this radius. Try 20 km or 50 km.</div>';
        } else {
          container.innerHTML = restaurants.map(item => {
            const r = item.restaurant || {};
            return `
              <div class="nearby-restaurant-item">
                <strong>${r.name || 'Restaurant'}</strong>
                <span>${item.distance_km} km · ${r.city || r.area || 'India'} · ${r.rating || 0} rating</span>
                <small>${r.address || r.cuisines || 'Restaurant partner'}</small>
                <em>${item.location_accuracy === 'exact' ? 'Exact GPS from dataset' : 'Estimated coordinate'}</em>
              </div>
            `;
          }).join('');
        }
        showToast('Nearby Search Ready', `${restaurants.length} restaurants found. Donation list is now filtered near you.`, 'success');
        loadDonations();
      } catch (err) {
        container.innerHTML = `<div class="nearby-empty">Could not load restaurants: ${err.message}</div>`;
        showToast('Nearby Search Failed', err.message, 'error');
      } finally {
        if (btn) btn.disabled = false;
      }
    }

    document.getElementById('findRestaurantsBtn')?.addEventListener('click', findNearbyRestaurants);

    // Modal close
    document.getElementById('modalClose')?.addEventListener('click', () => {
      document.getElementById('donationModal').style.display = 'none';
    });

    document.getElementById('donationModal')?.addEventListener('click', (e) => {
      if (e.target === document.getElementById('donationModal')) {
        document.getElementById('donationModal').style.display = 'none';
      }
    });

      // Expose for inline onclick + real-time refresh
    window.ngoApp = { 
      acceptDonation, 
      completeDonation, 
      showDetail,
      loadDonations   // ← Make loadDonations accessible
    };

    // Initial load
    loadDonations();
  }

  /* ═══════════════════════════════════════════
     DASHBOARD PAGE
  ═══════════════════════════════════════════ */

  function initDashboard() {
    const layout = document.querySelector('.dashboard-layout');
    if (!layout) return;
    let dashboardDonations = [];

    async function init() {
      const user = await checkSession();

      if (!user) {
        showToast('Login Required', 'Please login to access dashboard', 'warning');
        setTimeout(() => { window.location.href = '/login'; }, 1500);
        return;
      }

      currentUser = user;
      window._currentUser = user;
      updateSidebarUser(user);
      loadNotifications();

      // Show admin link
      if (user.role === 'admin') {
        const adminLink = document.getElementById('adminSidebarLink');
        if (adminLink) adminLink.style.display = 'flex';
      }

      // Active tab from hash
      const hash = window.location.hash.replace('#', '') || 'overview';
      loadTab(hash);

      // Sidebar nav
      document.querySelectorAll('.sidebar-link').forEach(link => {
        link.addEventListener('click', (e) => {
          e.preventDefault();
          const tab = link.dataset.tab;
          loadTab(tab);
          history.pushState(null, null, '#' + tab);
        });
      });
    }

    function updateSidebarUser(user) {
      const setEl = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

      const initial = (user.name || '?').charAt(0).toUpperCase();
      const avatarEl = document.getElementById('sidebarAvatar');
      if (avatarEl) avatarEl.textContent = initial;

      setEl('sidebarName', user.name);
      setEl('sidebarRole', user.role);
      setEl('sidebarPoints', (user.points || 0).toLocaleString());

      // Points progress bar (next level every 500 pts)
      const progress = (user.points % 500) / 500 * 100;
      const fill = document.getElementById('pointsFill');
      if (fill) setTimeout(() => { fill.style.width = progress + '%'; }, 300);

      setEl('dashWelcomeName', user.name.split(' ')[0]);
    }

    async function loadTab(tabName) {
      // Update sidebar active
      document.querySelectorAll('.sidebar-link').forEach(l => l.classList.remove('active'));
      const activeLink = document.querySelector(`.sidebar-link[data-tab="${tabName}"]`);
      if (activeLink) activeLink.classList.add('active');

      // Show tab
      document.querySelectorAll('.dash-tab').forEach(t => t.classList.remove('active'));
      const activeTab = document.getElementById(`tab-${tabName}`);
      if (activeTab) activeTab.classList.add('active');

      // Load data for tab
      switch (tabName) {
        case 'overview':     await loadOverview();     break;
        case 'my-donations': await loadMyDonations();  break;
        case 'leaderboard':  await loadLeaderboard();  break;
        case 'badges':       await loadBadges();        break;
        case 'admin-panel':  await loadAdminPanel();   break;
      }
    }

    async function loadOverview() {
      try {
        const [profileData, statsData, analyticsData] = await Promise.all([
          apiFetch(API.profile),
          apiFetch(API.stats),
          apiFetch(API.dashboardAnalytics)
        ]);

        if (profileData.success) {
          const user = profileData.user;

          const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
          set('statCO2', (user.co2_saved || 0).toFixed(1));
          set('statPoints', (user.points || 0).toLocaleString());

          // Recent activity from notifications
          const notifData = await apiFetch(API.notifications);
          renderRecentActivity(notifData.notifications || []);

          // Rank calculation
          const lbData = await apiFetch(API.leaderboard);
          const myRank = (lbData.leaderboard || []).findIndex(u => u.id === currentUser.id) + 1;
          set('statRank', myRank ? `#${myRank}` : '—');
        }

        if (statsData.success) {
          const s = statsData.stats;
          const setP = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
          setP('statMeals', s.total_donations || 0);
          setP('platMeals', s.total_meals_donated?.toLocaleString() || '—');
          setP('platCO2', s.total_co2_saved?.toFixed(1) || '—');
          setP('platUsers', s.total_users || '—');
          setP('platDonations', s.total_donations || '—');
        }

        if (analyticsData.success) {
          renderDashboardAnalytics(analyticsData.analytics);
        }
      } catch (err) {
        console.warn('[Overview] Error:', err);
        renderDashboardError(err);
      }
    }

    function renderRecentActivity(notifications) {
      const container = document.getElementById('recentActivity');
      if (!container) return;

      if (!notifications.length) {
        container.innerHTML = '<div class="activity-loading">No recent activity yet. Start donating! 🍽️</div>';
        return;
      }

      container.innerHTML = notifications.slice(0, 6).map(n => `
        <div class="activity-item">
          <div class="activity-icon">${getNotifIcon(n.type)}</div>
          <div class="activity-text">${n.message}</div>
          <div class="activity-time">${relativeTime(n.timestamp)}</div>
        </div>
      `).join('');
    }

    function getNotifIcon(type) {
      const icons = {
        welcome: '🎉', points: '⭐', donation: '📦',
        pickup: '🚗', pickup_accepted: '✅', completed: '🏆',
        new_donation: '🔔', alert: '⚠️'
      };
      return icons[type] || '📬';
    }

    async function dashboardAcceptDonation(id) {
      try {
        const data = await apiFetch(API.accept, {
          method: 'POST',
          body: JSON.stringify({ donation_id: id })
        });
        if (data.success) {
          showToast('Pickup Accepted', data.message, 'success');
          await loadMyDonations();
          await loadOverview();
        }
      } catch (err) {
        showToast('Accept Failed', err.message || 'Could not accept this pickup', 'error');
      }
    }

    async function dashboardCompleteDonation(id) {
      try {
        const data = await apiFetch(API.complete, {
          method: 'POST',
          body: JSON.stringify({ donation_id: id })
        });
        if (data.success) {
          showToast('Pickup Completed', data.message, 'success');
          await loadMyDonations();
          await loadOverview();
        }
      } catch (err) {
        showToast('Complete Failed', err.message || 'Could not complete this pickup', 'error');
      }
    }

    function showDashboardDonationDetail(id) {
      const d = dashboardDonations.find(item => item.id === id);
      if (!d) return;

      let modal = document.getElementById('dashboardDonationModal');
      if (!modal) {
        modal = document.createElement('div');
        modal.id = 'dashboardDonationModal';
        modal.className = 'modal-overlay';
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
          if (e.target === modal) modal.style.display = 'none';
        });
      }

      modal.innerHTML = `
        <div class="modal-content" style="max-width:640px">
          <button class="modal-close" onclick="document.getElementById('dashboardDonationModal').style.display='none'">×</button>
          <h2 style="font-family:var(--font-display);margin-bottom:1rem">${d.food_name}</h2>
          ${d.image ? `<img src="${d.image}" style="width:100%;height:220px;object-fit:cover;border-radius:var(--radius-md);margin-bottom:1rem" alt="${d.food_name}">` : ''}
          <div class="detail-grid">
            ${[
              ['Status', d.status],
              ['Urgency', d.urgency],
              ['Freshness', `${d.freshness_score}/100`],
              ['Quantity', `${d.quantity} ${d.quantity_unit}`],
              ['Pickup', d.location],
              ['Coordinates', d.coordinates ? `${Number(d.coordinates.lat).toFixed(5)}, ${Number(d.coordinates.lng).toFixed(5)}` : 'Not captured'],
              ['CO₂ Saved', `${d.co2_saved || 0} kg`],
              ['Listed', relativeTime(d.created_at)]
            ].map(([k, v]) => `<div><span>${k}</span><strong>${v || '—'}</strong></div>`).join('')}
          </div>
          <p style="color:var(--text-secondary);line-height:1.6;margin-top:1rem">${d.description || 'No description provided.'}</p>
        </div>
      `;
      modal.style.display = 'flex';
    }

    function renderDashboardError(err) {
      ['modelPerfPanel', 'routingAnalytics', 'platStatsPanel'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.innerHTML = `<div class="loading-state" style="color:var(--accent-red)">Dashboard data failed: ${err.message || 'Unknown error'}</div>`;
      });
    }

    function renderDashboardAnalytics(a) {
      const set = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
      };

      const confidenceText = a.ai.avg_confidence === null ? 'Rule-based' : `${a.ai.avg_confidence}%`;
      set('statConfDash', confidenceText);
      set('predCount', `${a.ai.prediction_count || a.ai.recent_predictions.length} total`);

      renderPredictionTable(a.ai.recent_predictions || []);
      renderModelPerformance(a);
      renderRoutingAnalytics(a.routing);
      renderPlatformPanel(a);
      renderDashboardMap(a.map_donations || []);
    }

    function renderPredictionTable(predictions) {
      const body = document.getElementById('predTableBody');
      if (!body) return;

      if (!predictions.length) {
        body.innerHTML = '<tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--text-muted)">No AI predictions logged yet.</td></tr>';
        return;
      }

      body.innerHTML = predictions.map(p => {
        const conf = p.confidence === null || p.confidence === undefined ? 'rules' : `${Math.round(Number(p.confidence) * 100)}%`;
        const food = p.food_name || 'Food item';
        const klass = p.predicted_class || p.urgency || 'unknown';
        const route = p.recommended_route || (klass === 'expired' ? 'Biogas' : 'NGO');
        return `
          <tr style="border-bottom:1px solid var(--border-color)">
            <td style="padding:0.65rem 0.75rem;color:var(--text-muted)">${relativeTime(p.timestamp)}</td>
            <td style="padding:0.65rem 0.75rem;font-weight:700">${food}</td>
            <td style="padding:0.65rem 0.75rem">${urgencyBadgeHTML(klass)}</td>
            <td style="padding:0.65rem 0.75rem;color:var(--accent-blue)">${conf}</td>
            <td style="padding:0.65rem 0.75rem;color:var(--accent-green);font-weight:700">${route}</td>
          </tr>
        `;
      }).join('');
    }

    function renderModelPerformance(a) {
      const panel = document.getElementById('modelPerfPanel');
      if (!panel) return;

      panel.innerHTML = `
        <div class="analytics-kpi-grid">
          <div class="analytics-kpi"><span>${a.ai.avg_freshness}</span><small>Avg freshness score</small></div>
          <div class="analytics-kpi"><span>${a.ai.prediction_count}</span><small>AI predictions logged</small></div>
          <div class="analytics-kpi"><span>${a.donations.total}</span><small>Donation samples</small></div>
        </div>
        <div class="chart-wrap"><canvas id="urgencyChart"></canvas></div>
      `;

      renderChart('urgencyChart', 'doughnut', Object.keys(a.donations.by_urgency), Object.values(a.donations.by_urgency), [
        '#ff5c7a', '#ffcc4d', '#20d3ff', '#00ff88', '#8c8f99', '#ff8a3d'
      ]);
    }

    function renderRoutingAnalytics(routing) {
      const panel = document.getElementById('routingAnalytics');
      if (!panel) return;

      panel.innerHTML = `
        <div class="route-metrics">
          <div><strong>${routing.active_pickups}</strong><span>active pickups</span></div>
          <div><strong>${routing.optimized_distance_km} km</strong><span>optimized route load</span></div>
          <div><strong>${routing.distance_saved_km} km</strong><span>distance saved</span></div>
          <div><strong>${routing.estimated_time_saved_min} min</strong><span>ETA saved</span></div>
        </div>
        <div class="route-progress">
          <div style="width:${Math.min(routing.nearest_match_rate, 100)}%"></div>
        </div>
        <div class="route-note">${routing.nearest_match_rate}% nearest-match routing rate</div>
        <div class="chart-wrap small"><canvas id="routeChart"></canvas></div>
      `;

      renderChart('routeChart', 'bar', Object.keys(routing.route_distribution), Object.values(routing.route_distribution), [
        '#00ff88', '#ffd93d', '#ff5c7a'
      ]);
    }

    function renderPlatformPanel(a) {
      const panel = document.getElementById('platStatsPanel');
      if (!panel) return;

      const status = a.donations.by_status || {};
      const cities = Object.entries(a.donations.by_city || {});
      panel.innerHTML = `
        <div class="analytics-kpi-grid">
          <div class="analytics-kpi"><span>${a.donations.available}</span><small>available</small></div>
          <div class="analytics-kpi"><span>${a.donations.accepted}</span><small>in transit</small></div>
          <div class="analytics-kpi"><span>${a.donations.completed}</span><small>completed</small></div>
        </div>
        <div class="status-bars">
          ${Object.entries(status).map(([name, count]) => `
            <div class="status-row">
              <span>${name}</span>
              <div><i style="width:${Math.max(8, count / Math.max(a.donations.total, 1) * 100)}%"></i></div>
              <b>${count}</b>
            </div>
          `).join('')}
        </div>
        <div class="city-list">
          ${cities.map(([city, count]) => `<span>${city}<b>${count}</b></span>`).join('') || '<span>No city data yet</span>'}
        </div>
      `;
    }

    function renderChart(canvasId, type, labels, values, colors) {
      const canvas = document.getElementById(canvasId);
      if (!canvas || typeof Chart === 'undefined') return;

      if (chartRegistry[canvasId]) chartRegistry[canvasId].destroy();
      chartRegistry[canvasId] = new Chart(canvas, {
        type,
        data: {
          labels,
          datasets: [{
            data: values,
            backgroundColor: colors,
            borderColor: 'rgba(255,255,255,0.12)',
            borderWidth: 1,
            borderRadius: type === 'bar' ? 6 : 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { labels: { color: '#a7adbb', boxWidth: 10, font: { size: 11 } } }
          },
          scales: type === 'bar' ? {
            x: { ticks: { color: '#a7adbb' }, grid: { color: 'rgba(255,255,255,0.06)' } },
            y: { ticks: { color: '#a7adbb', precision: 0 }, grid: { color: 'rgba(255,255,255,0.06)' } }
          } : {}
        }
      });
    }

    function renderDashboardMap(donations) {
      const el = document.getElementById('dashboardMap');
      if (!el) return;
      if (typeof L === 'undefined') {
        el.innerHTML = '<div class="loading-state">Map library unavailable.</div>';
        return;
      }

      if (window._dashboardLeafletMap) {
        window._dashboardLeafletMap.remove();
      }

      const map = L.map('dashboardMap', { zoomControl: true }).setView([20.5937, 78.9629], 5);
      window._dashboardLeafletMap = map;
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: 'OpenStreetMap',
        maxZoom: 18
      }).addTo(map);

      const markers = [];
      const iconFor = (d) => {
        const color = d.urgency === 'expired' ? '#ff5c7a' : d.urgency === 'medium' ? '#ffd93d' : '#00ff88';
        return L.divIcon({
          className: '',
          html: `<div class="map-pin-dot" style="background:${color}"></div>`,
          iconSize: [20, 20],
          iconAnchor: [10, 10]
        });
      };

      donations.forEach(d => {
        const lat = d.coordinates?.lat;
        const lng = d.coordinates?.lng;
        if (lat === undefined || lng === undefined) return;

        const marker = L.marker([lat, lng], { icon: iconFor(d) }).addTo(map);
        marker._donationStatus = d.status || 'available';
        marker.bindPopup(`
          <strong>${d.food_name || 'Food donation'}</strong><br>
          ${d.location || 'Pickup location'}<br>
          ${d.quantity || 0} ${d.quantity_unit || ''} · ${d.urgency || 'safe'}
        `);
        markers.push(marker);
      });

      if (markers.length) {
        map.fitBounds(L.featureGroup(markers).getBounds().pad(0.18));
      }

      window.dashboardMap = {
        filterMarkers(status) {
          document.querySelectorAll('[data-mapfilter]').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mapfilter === status);
          });
          markers.forEach(marker => {
            const visible = status === 'all' || marker._donationStatus === status;
            if (visible && !map.hasLayer(marker)) marker.addTo(map);
            if (!visible && map.hasLayer(marker)) marker.remove();
          });
        }
      };

      setTimeout(() => map.invalidateSize(), 100);
    }

    async function loadMyDonations() {
      const container = document.getElementById('myDonationsList');
      if (!container) return;

      container.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div>Loading...</div>';

      try {
        const url = currentUser.role === 'admin'
          ? `${API.getDonations}?limit=100`
          : `${API.getDonations}?donor_id=${currentUser.id}`;
        const data = await apiFetch(url);
        const donations = data.donations || [];
        dashboardDonations = donations;

        if (!donations.length) {
          container.innerHTML = `
            <div style="text-align:center;padding:3rem;color:var(--text-muted)">
              <div style="font-size:3rem;margin-bottom:1rem">🍽️</div>
              <h3>No donations yet</h3>
              <p>Start donating to see donation history here.</p>
              <a href="/donate" class="btn btn-primary" style="margin-top:1rem;display:inline-flex">Donate Now</a>
            </div>
          `;
          return;
        }

        container.innerHTML = donations.map(d => renderDonationCard(d, true)).join('');

        // Filter buttons
        document.querySelectorAll('.filter-btn[data-status]').forEach(btn => {
          btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn[data-status]').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const status = btn.dataset.status;
            const cards  = container.querySelectorAll('.donation-card');
            cards.forEach(card => {
              const id = card.dataset.id;
              const d  = donations.find(x => x.id === id);
              if (!d) return;
              card.style.display = (status === 'all' || d.status === status) ? 'grid' : 'none';
            });
          });
        });

      } catch (err) {
        container.innerHTML = `<div class="loading-state" style="color:var(--accent-red)">Error loading donations</div>`;
      }
    }

    async function loadLeaderboard() {
      const container = document.getElementById('leaderboardList');
      if (!container) return;

      container.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div>Loading...</div>';

      try {
        const data = await apiFetch(API.leaderboard);
        const board = data.leaderboard || [];

        if (!board.length) {
          container.innerHTML = '<div class="loading-state">No users yet.</div>';
          return;
        }

        const rankDisplay = (rank) => {
          if (rank === 1) return `<span class="lb-rank gold">🥇</span>`;
          if (rank === 2) return `<span class="lb-rank silver">🥈</span>`;
          if (rank === 3) return `<span class="lb-rank bronze">🥉</span>`;
          return `<span class="lb-rank">#${rank}</span>`;
        };

        container.innerHTML = board.map(u => `
          <div class="lb-item ${u.id === currentUser.id ? 'current-user' : ''}">
            ${rankDisplay(u.rank)}
            <div class="lb-avatar">${u.name.charAt(0).toUpperCase()}</div>
            <div class="lb-info">
              <div class="lb-name">${u.name} ${u.id === currentUser.id ? '<span style="color:var(--accent-green);font-size:0.72rem">(You)</span>' : ''}</div>
              <div class="lb-role">${u.role} · ${u.total_donations} donations</div>
              <div class="lb-badges">${(u.badges || []).join(' ')}</div>
            </div>
            <div class="lb-points">${(u.points || 0).toLocaleString()}</div>
          </div>
        `).join('');

        // Role filters
        document.querySelectorAll('.lb-filter .filter-btn').forEach(btn => {
          btn.addEventListener('click', async () => {
            document.querySelectorAll('.lb-filter .filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const role = btn.dataset.role;
            const url  = role === 'all' ? API.leaderboard : `${API.leaderboard}?role=${role}`;
            container.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div>Loading...</div>';
            const d2 = await apiFetch(url);
            container.innerHTML = (d2.leaderboard || []).map(u => `
              <div class="lb-item ${u.id === currentUser.id ? 'current-user' : ''}">
                ${rankDisplay(u.rank)}
                <div class="lb-avatar">${u.name.charAt(0).toUpperCase()}</div>
                <div class="lb-info">
                  <div class="lb-name">${u.name}</div>
                  <div class="lb-role">${u.role} · ${u.total_donations} donations</div>
                </div>
                <div class="lb-points">${(u.points || 0).toLocaleString()}</div>
              </div>
            `).join('') || '<div class="loading-state">No users in this category</div>';
          });
        });

      } catch (err) {
        container.innerHTML = `<div class="loading-state" style="color:var(--accent-red)">Error loading leaderboard</div>`;
      }
    }

    async function loadBadges() {
      const container = document.getElementById('badgesGrid');
      if (!container) return;

      try {
        const data = await apiFetch(API.profile);
        const user = data.user || currentUser;
        const badges = user.badges || [];

        if (!badges.length) {
          container.innerHTML = `
            <div style="grid-column:1/-1;text-align:center;padding:2rem;color:var(--text-muted)">
              <div style="font-size:3rem;margin-bottom:0.5rem">🎖️</div>
              <p>No badges yet. Keep donating to earn them!</p>
            </div>
          `;
          return;
        }

        container.innerHTML = badges.map(badge => {
          const parts = badge.split(' ');
          const emoji = parts[0];
          const name  = parts.slice(1).join(' ');
          return `
            <div class="badge-card earned" style="animation:fadeIn 0.5s ease">
              <div class="badge-emoji">${emoji}</div>
              <div class="badge-name">${name}</div>
              <div class="badge-req" style="color:var(--accent-green)">✅ Earned</div>
            </div>
          `;
        }).join('');

        // Update all-badges grid to show unlocked
        document.querySelectorAll('.all-badges-grid .badge-card').forEach(card => {
          const name = card.querySelector('.badge-name')?.textContent || '';
          if (badges.some(b => b.includes(name))) {
            card.classList.remove('locked');
            card.classList.add('earned');
          }
        });

      } catch {}
    }

    async function loadAdminPanel() {
      const container = document.getElementById('adminContent');
      if (!container || currentUser?.role !== 'admin') return;

      await loadAdminUsers();

      document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          document.querySelectorAll('.admin-tab-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          switch (btn.dataset.atab) {
            case 'users':     await loadAdminUsers();     break;
            case 'donations': await loadAdminDonations(); break;
            case 'reports':   await loadAdminReports();   break;
          }
        });
      });
    }

    async function loadAdminUsers() {
      const container = document.getElementById('adminContent');
      container.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div>Loading users...</div>';

      try {
        const data = await apiFetch(API.adminUsers);
        const users = data.users || [];

        container.innerHTML = `
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Name</th><th>Email</th><th>Role</th><th>Points</th>
                  <th>Donations</th><th>Status</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${users.map(u => `
                  <tr>
                    <td><strong>${u.name}</strong></td>
                    <td style="color:var(--text-muted)">${u.email}</td>
                    <td><span style="text-transform:capitalize">${u.role}</span></td>
                    <td style="color:var(--accent-green);font-weight:700">${u.points}</td>
                    <td>${u.total_donations}</td>
                    <td>
                      <span style="padding:0.2rem 0.5rem;border-radius:999px;font-size:0.72rem;font-weight:700;background:${u.approved ? 'rgba(0,255,136,0.12)' : 'rgba(255,107,107,0.12)'};color:${u.approved ? 'var(--accent-green)' : 'var(--accent-red)'}">
                        ${u.approved ? 'Active' : 'Pending'}
                      </span>
                    </td>
                    <td>
                      <div class="admin-action-btns">
                        ${!u.approved ? `<button class="admin-btn approve" onclick="window.dashboardApp.approveUser('${u.id}', true)">Approve</button>` : ''}
                        ${u.role !== 'admin' ? `<button class="admin-btn delete" onclick="window.dashboardApp.deleteUser('${u.id}')">Delete</button>` : ''}
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `;
      } catch (err) {
        container.innerHTML = `<div class="loading-state" style="color:var(--accent-red)">Error: ${err.message}</div>`;
      }
    }

    async function loadAdminDonations() {
      const container = document.getElementById('adminContent');
      container.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div>Loading...</div>';

      try {
        const data = await apiFetch(API.getDonations + '?limit=50');
        const donations = data.donations || [];

        container.innerHTML = `
          <div class="admin-table-wrap">
            <table class="admin-table">
              <thead>
                <tr><th>Food</th><th>Donor</th><th>Qty</th><th>Urgency</th><th>Status</th><th>CO₂</th><th>Actions</th></tr>
              </thead>
              <tbody>
                ${donations.map(d => `
                  <tr>
                    <td><strong>${d.food_name}</strong></td>
                    <td>${d.donor_name}</td>
                    <td>${d.quantity} ${d.quantity_unit}</td>
                    <td>${urgencyBadgeHTML(d.urgency)}</td>
                    <td><span class="dc-status-badge ${d.status}">${d.status}</span></td>
                    <td>${d.co2_saved}kg</td>
                    <td><button class="admin-btn delete" onclick="window.dashboardApp.deleteDonation('${d.id}')">Delete</button></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `;
      } catch (err) {
        container.innerHTML = `<div class="loading-state" style="color:var(--accent-red)">Error loading donations</div>`;
      }
    }

    async function loadAdminReports() {
      const container = document.getElementById('adminContent');
      try {
        const data = await apiFetch(API.stats);
        const s = data.stats;
        container.innerHTML = `
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem">
            ${[
              ['Total Users', s.total_users, '👥'],
              ['Donors', s.donors, '🏠'],
              ['Restaurants', s.restaurants, '🍽️'],
              ['NGOs', s.ngos, '🏥'],
              ['Volunteers', s.volunteers, '🚗'],
              ['Total Donations', s.total_donations, '📦'],
              ['Completed', s.completed_donations, '✅'],
              ['Meals Donated', s.total_meals_donated, '🍽️'],
              ['CO₂ Saved (kg)', s.total_co2_saved?.toFixed(1), '🌿'],
              ['Food Saved (kg)', s.total_food_kg?.toFixed(1), '⚖️'],
              ['Cities', s.cities_reached, '🏙️'],
              ['Trees Equiv.', s.trees_equivalent, '🌳']
            ].map(([label, val, icon]) => `
              <div class="dash-stat-card">
                <div class="dsc-icon">${icon}</div>
                <div class="dsc-value">${val ?? '—'}</div>
                <div class="dsc-label">${label}</div>
              </div>
            `).join('')}
          </div>
        `;
      } catch {}
    }

    // Admin actions
    async function approveUser(userId, approved) {
      try {
        await apiFetch(API.adminApprove, {
          method: 'POST',
          body: JSON.stringify({ user_id: userId, approved })
        });
        showToast('User Updated', `User has been ${approved ? 'approved' : 'rejected'}`, 'success');
        loadAdminUsers();
      } catch (err) {
        showToast('Error', err.message, 'error');
      }
    }

    async function deleteUser(userId) {
      if (!confirm('Delete this user? This cannot be undone.')) return;
      try {
        await apiFetch(API.adminDelete, {
          method: 'POST',
          body: JSON.stringify({ type: 'user', id: userId })
        });
        showToast('User Deleted', 'User has been removed', 'success');
        loadAdminUsers();
      } catch (err) {
        showToast('Error', err.message, 'error');
      }
    }

    async function deleteDonation(id) {
      if (!confirm('Delete this donation?')) return;
      try {
        await apiFetch(API.adminDelete, {
          method: 'POST',
          body: JSON.stringify({ type: 'donation', id })
        });
        showToast('Deleted', 'Donation removed', 'success');
        loadAdminDonations();
      } catch (err) {
        showToast('Error', err.message, 'error');
      }
    }

    // Notifications
    async function loadNotifications() {
      const badge   = document.getElementById('notifBadge');
      const list    = document.getElementById('notifList');
      const btn     = document.getElementById('notifBtn');
      const panel   = document.getElementById('notifPanel');
      const markAll = document.getElementById('markAllRead');

      if (!btn || !panel) return;

      btn.addEventListener('click', () => {
        panel.classList.toggle('open');
        if (panel.classList.contains('open')) {
          fetchNotifications(badge, list);
        }
      });

      markAll?.addEventListener('click', async () => {
        await apiFetch(API.notifications, { method: 'POST' });
        if (badge) badge.textContent = '0';
        await fetchNotifications(badge, list);
      });

      // Close on outside click
      document.addEventListener('click', (e) => {
        if (!panel.contains(e.target) && e.target !== btn) {
          panel.classList.remove('open');
        }
      });

      // Initial fetch for badge count
      await fetchNotifications(badge, list, false);
    }

    async function fetchNotifications(badge, list, render = true) {
      try {
        const data = await apiFetch(API.notifications);
        const notifs = data.notifications || [];

        if (badge) badge.textContent = data.unread_count || 0;

        if (!render || !list) return;

        if (!notifs.length) {
          list.innerHTML = '<div class="notif-empty">No notifications yet 🔔</div>';
          return;
        }

        list.innerHTML = notifs.map(n => `
          <div class="notif-item ${n.read ? '' : 'unread'}">
            <div class="notif-msg">${n.message}</div>
            <div class="notif-time">${relativeTime(n.timestamp)}</div>
          </div>
        `).join('');
      } catch {}
    }

    // Logout
    document.getElementById('logoutBtn')?.addEventListener('click', async () => {
      await apiFetch(API.logout, { method: 'POST' });
      localStorage.removeItem('foodsave_user');
      showToast('Logged Out', 'See you soon! 👋', 'info');
      setTimeout(() => { window.location.href = '/'; }, 1000);
    });

    window.ngoApp = {
      acceptDonation: dashboardAcceptDonation,
      completeDonation: dashboardCompleteDonation,
      showDetail: showDashboardDonationDetail
    };

    // Expose for dashboard use
    window.dashboardApp = {
      init,
      loadTab,
      approveUser,
      deleteUser,
      deleteDonation
    };

    init();
  }

  /* ═══════════════════════════════════════════
     LOADING BUTTON STATE HELPER
  ═══════════════════════════════════════════ */

  function setLoading(btn, loading) {
    const text   = btn.querySelector('.btn-text');
    const loader = btn.querySelector('.btn-loader');
    if (text)   text.style.display   = loading ? 'none' : 'block';
    if (loader) loader.style.display = loading ? 'block' : 'none';
    btn.disabled = loading;
  }

  /* ═══════════════════════════════════════════
     PAGE ROUTER
  ═══════════════════════════════════════════ */

  async function router() {
    // Always check session and update nav
    await checkSession();

    switch (page) {
      case 'home':
        // Home page — animations handled by animations.js
        break;
      case 'login':
        initLoginPage();
        break;
      case 'signup':
        initSignupPage();
        break;
      case 'donate':
        initDonatePage();
        break;
      case 'ngo':
        initNGOPage();
        break;
      case 'dashboard':
        initDashboard();
        break;
    }
  }

  /* ═══════════════════════════════════════════
     INIT
  ═══════════════════════════════════════════ */

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', router);
  } else {
    router();
  }

  // Expose toast globally
  window.showToast = showToast;

})();

/* ═══════════════════════════════════════════
   SCROLL-TO-TOP BUTTON (global)
═══════════════════════════════════════════ */
(function() {
  const btn = document.createElement('button');
  btn.id = 'scrollTopBtn';
  btn.innerHTML = '↑';
  btn.title = 'Back to top';
  document.body.appendChild(btn);

  window.addEventListener('scroll', () => {
    if (window.scrollY > 400) {
      btn.classList.add('visible');
    } else {
      btn.classList.remove('visible');
    }
  }, { passive: true });

  btn.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
})();

/* ═══════════════════════════════════════════
   WEBSOCKET REAL-TIME NOTIFICATIONS (Improved)
═══════════════════════════════════════════ */
(function initWebSocket() {
  if (typeof io === 'undefined') {
    console.warn('⚠️ Socket.IO not loaded');
    return;
  }

  const socket = io();

  socket.on('connect', () => {
    console.log('✅ Real-time connected');
    if (window._currentUser) {
      socket.emit('join_notifications', { user_id: window._currentUser.id });
    }
  });

  socket.on('notification', (data) => {
    if (window.showToast) {
      const typeMap = {
        pickup_accepted: 'success',
        new_donation: 'info',
        completed: 'success',
        alert: 'warning'
      };
      window.showToast('Live Update 🔔', data.message, typeMap[data.type] || 'info', 6000);
    }

    // Update notification badge
    const badge = document.getElementById('notifBadge');
    if (badge) {
      let count = parseInt(badge.textContent) || 0;
      badge.textContent = count + 1;
    }
  });

  socket.on('donation_update', (data) => {
    console.log('📦 Real-time donation update:', data);

    // Auto-refresh NGO donations list
    if (document.body.dataset.page === 'ngo' && window.ngoApp && window.ngoApp.loadDonations) {
      console.log('🔄 Auto-refreshing donations list...');
      setTimeout(() => {
        window.ngoApp.loadDonations();
      }, 800);
    }

    // Optional: Show live ticker (if you add #liveTicker element later)
    const ticker = document.getElementById('liveTicker');
    if (ticker && data.message) {
      ticker.style.opacity = '0';
      setTimeout(() => {
        ticker.textContent = '🔴 LIVE: ' + data.message;
        ticker.style.opacity = '1';
      }, 300);
    }
  });

  socket.on('disconnect', () => {
    console.log('🔌 Real-time disconnected');
  });

  window._socket = socket;
})();


/* ═══════════════════════════════════════════
   LEAFLET MAP MODULE
═══════════════════════════════════════════ */
window.MapModule = (function () {
  let map = null;
  let markers = [];

  const ICONS = {
    available: { color: '#00ff88', emoji: '🍽️' },
    accepted:  { color: '#00d4ff', emoji: '🚗' },
    completed: { color: '#b48eff', emoji: '✅' },
    ngo:       { color: '#ffd93d', emoji: '🏥' },
    poultry:   { color: '#ff9f1c', emoji: '🐔' },
    biogas:    { color: '#ff6b6b', emoji: '♻️' }
  };

  function makeIcon(type) {
    const cfg = ICONS[type] || ICONS.available;
    return L.divIcon({
      className: '',
      html: `<div style="
        background:${cfg.color};
        width:36px;height:36px;
        border-radius:50% 50% 50% 0;
        transform:rotate(-45deg);
        border:2px solid white;
        box-shadow:0 2px 8px rgba(0,0,0,0.3);
        display:flex;align-items:center;justify-content:center;
      "><span style="transform:rotate(45deg);font-size:14px">${cfg.emoji}</span></div>`,
      iconSize: [36, 36],
      iconAnchor: [18, 36],
      popupAnchor: [0, -36]
    });
  }

  function initMap(containerId, centerLat, centerLng, zoom) {
    if (map) { map.remove(); map = null; }
    const container = document.getElementById(containerId);
    if (!container) return;

    // Default: India center
    map = L.map(containerId, { zoomControl: true }).setView(
      [centerLat || 20.5937, centerLng || 78.9629],
      zoom || 5
    );

    // Dark tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map);

    return map;
  }

  function clearMarkers() {
    markers.forEach(m => m.remove());
    markers = [];
  }

  function addDonationMarkers(donations) {
    if (!map) return;
    clearMarkers();
    donations.forEach(d => {
      if (!d.coordinates || !d.coordinates.lat) return;
      const marker = L.marker(
        [d.coordinates.lat, d.coordinates.lng],
        { icon: makeIcon(d.status) }
      ).addTo(map);

      marker.bindPopup(`
        <div style="font-family:sans-serif;min-width:200px">
          <strong style="font-size:1rem">${d.food_name}</strong><br/>
          <span style="color:#666;font-size:0.82rem">by ${d.donor_name}</span><br/>
          <hr style="margin:6px 0;border:none;border-top:1px solid #eee"/>
          <span>📦 ${d.quantity} ${d.quantity_unit}</span><br/>
          <span>⏱ ${d.hours_remaining}h remaining</span><br/>
          <span>🌿 ${d.co2_saved}kg CO₂ saved</span><br/>
          <span style="
            display:inline-block;margin-top:6px;padding:2px 8px;
            border-radius:999px;font-size:0.72rem;font-weight:700;
            background:${d.urgency === 'critical' ? '#ff6b6b33' : '#00ff8833'};
            color:${d.urgency === 'critical' ? '#ff6b6b' : '#00ff88'}
          ">${d.urgency.toUpperCase()}</span>
        </div>
      `);
      markers.push(marker);
    });

    // Auto-fit bounds
    if (markers.length > 0) {
      const group = L.featureGroup(markers);
      map.fitBounds(group.getBounds().pad(0.2));
    }
  }

  function addNGOMarkers(ngos) {
    if (!map) return;
    ngos.forEach(n => {
      if (!n.lat || !n.lng) return;
      const marker = L.marker([n.lat, n.lng], { icon: makeIcon('ngo') }).addTo(map);
      marker.bindPopup(`
        <div style="font-family:sans-serif">
          <strong>${n.name}</strong><br/>
          <span style="color:#666;font-size:0.82rem">${n.address}</span><br/>
          <span>📞 ${n.phone || 'N/A'}</span><br/>
          <span>Capacity: ${n.capacity_kg}kg/day</span>
        </div>
      `);
      markers.push(marker);
    });
  }

  function addBiogasMarkers(plants) {
    if (!map) return;
    plants.forEach(p => {
      if (!p.lat || !p.lng) return;
      const marker = L.marker([p.lat, p.lng], { icon: makeIcon('biogas') }).addTo(map);
      marker.bindPopup(`
        <div style="font-family:sans-serif">
          <strong>♻️ ${p.name}</strong><br/>
          <span>${p.address}</span><br/>
          <span>Capacity: ${p.capacity_kg}kg/day</span>
        </div>
      `);
      markers.push(marker);
    });
  }

  function addPoultryMarkers(farms) {
    if (!map) return;
    farms.forEach(p => {
      if (!p.lat || !p.lng) return;
      const marker = L.marker([p.lat, p.lng], { icon: makeIcon('poultry') }).addTo(map);
      marker.bindPopup(`
        <div style="font-family:sans-serif">
          <strong>🐔 ${p.name}</strong><br/>
          <span>${p.address}</span><br/>
          <span>Capacity: ${p.capacity_kg || 'N/A'}kg/day</span>
        </div>
      `);
      markers.push(marker);
    });
  }

  // Toggle map visibility
  function initToggle() {
    const btn = document.getElementById('toggleMapBtn');
    const container = document.getElementById('donationMap');
    if (!btn || !container) return;
    btn.addEventListener('click', () => {
      const hidden = container.style.display === 'none';
      container.style.display = hidden ? 'block' : 'none';
      btn.textContent = hidden ? 'Hide Map' : 'Show Map';
      if (hidden && map) map.invalidateSize();
    });
  }

  return { initMap, addDonationMarkers, addNGOMarkers, addBiogasMarkers, addPoultryMarkers, initToggle };
})();
/* ═══════════════════════════════════════════
   WASTE HEATMAP
═══════════════════════════════════════════ */
async function initWasteHeatmap() {
  const container = document.getElementById('wasteHeatmap');
  if (!container || typeof L === 'undefined') return;

  const map = L.map('wasteHeatmap').setView([20.5937, 78.9629], 5);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

  try {
    const data = await fetch('/api/get_donations?limit=100').then(r => r.json());
    const points = (data.donations || [])
      .filter(d => d.coordinates?.lat)
      .map(d => [
        d.coordinates.lat,
        d.coordinates.lng,
        // Intensity based on urgency
        { critical:1.0, high:0.7, medium:0.4, low:0.2 }[d.urgency] || 0.3
      ]);

    if (points.length && L.heatLayer) {
      L.heatLayer(points, {
        radius: 35,
        blur: 20,
        maxZoom: 10,
        gradient: { 0.2:'#00ff88', 0.5:'#ffd93d', 0.8:'#ff6b6b', 1.0:'#ff0000' }
      }).addTo(map);
    }
  } catch (e) {
    console.warn('Heatmap error:', e);
  }
}
