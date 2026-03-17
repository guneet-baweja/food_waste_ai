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
    adminUsers:   '/api/admin/users',
    adminApprove: '/api/admin/approve',
    adminDelete:  '/api/admin/delete'
  };

  // App state
  let currentUser = null;
  const page = document.body.dataset.page;

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

    // Detect location
    const detectBtn = document.getElementById('detectLocation');
    detectBtn?.addEventListener('click', () => {
      if (!navigator.geolocation) {
        showToast('Not Supported', 'Geolocation is not supported by your browser', 'warning');
        return;
      }
      detectBtn.textContent = '⏳';
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          document.getElementById('latHidden').value = pos.coords.latitude;
          document.getElementById('lngHidden').value = pos.coords.longitude;
          document.getElementById('location').value = `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;
          detectBtn.textContent = '✅';
          showToast('Location Detected', 'Your location has been captured', 'success');
        },
        () => {
          detectBtn.textContent = '📍';
          showToast('Location Error', 'Could not access your location', 'error');
        }
      );
    });

    // Image upload preview
    const uploadZone  = document.getElementById('uploadZone');
    const fileInput   = document.getElementById('foodImage');
    const previewWrap = document.getElementById('imagePreview');
    const previewImg  = document.getElementById('previewImg');
    const removeBtn   = document.getElementById('removeImg');

    fileInput?.addEventListener('change', () => {
      const file = fileInput.files[0];
      if (file) showImagePreview(file);
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

      const formData = new FormData(form);

      try {
        const data = await apiFetch(API.uploadFood, {
          method: 'POST',
          body: formData
        });

        if (data.success) {
          // Show AI prediction
          showAIPrediction(data.ai_prediction);

          showToast('Donation Listed! 🍽️', `+100 points earned! ${data.ai_prediction.urgency.toUpperCase()} urgency detected.`, 'success', 6000);

          setTimeout(() => {
            window.location.href = '/dashboard';
          }, 3000);
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

  function showAIPrediction(pred) {
    const card     = document.getElementById('aiPrediction');
    const scoreEl  = document.getElementById('freshnessScore');
    const fillEl   = document.getElementById('freshnessFill');
    const badgeEl  = document.getElementById('urgencyBadge');
    const hoursEl  = document.getElementById('hoursLeft');

    if (!card) return;

    card.style.display = 'block';
    scoreEl.textContent = pred.freshness_score + ' / 100';
    fillEl.style.width = pred.freshness_score + '%';

    // Color fill by score
    if (pred.freshness_score >= 70) {
      fillEl.style.background = 'var(--grad-primary)';
    } else if (pred.freshness_score >= 40) {
      fillEl.style.background = 'linear-gradient(90deg, #ffd93d, #ffa500)';
    } else {
      fillEl.style.background = 'linear-gradient(90deg, #ff6b6b, #ff4444)';
    }

    badgeEl.textContent = pred.urgency.charAt(0).toUpperCase() + pred.urgency.slice(1);
    badgeEl.className = `urgency-badge ${pred.urgency}`;
    hoursEl.textContent = pred.hours_remaining > 0
      ? `⏱ ${pred.hours_remaining} hours remaining`
      : '⚠️ Already expired';
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

    async function loadDonations() {
      list.innerHTML = `<div class="loading-state"><div class="loading-spinner"></div>Loading donations...</div>`;

      try {
        const statusEl = document.querySelector('input[name="statusFilter"]:checked');
        const status   = statusEl ? statusEl.value : 'available';
        const foodType = document.getElementById('foodTypeFilter')?.value || '';

        let url = API.getDonations + '?limit=50';
        if (status) url += `&status=${status}`;
        if (foodType) url += `&food_type=${foodType}`;

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

    // Modal close
    document.getElementById('modalClose')?.addEventListener('click', () => {
      document.getElementById('donationModal').style.display = 'none';
    });

    document.getElementById('donationModal')?.addEventListener('click', (e) => {
      if (e.target === document.getElementById('donationModal')) {
        document.getElementById('donationModal').style.display = 'none';
      }
    });

    // Expose for inline onclick
    window.ngoApp = { acceptDonation, completeDonation, showDetail };

    // Initial load
    loadDonations();
  }

  /* ═══════════════════════════════════════════
     DASHBOARD PAGE
  ═══════════════════════════════════════════ */

  function initDashboard() {
    const layout = document.querySelector('.dashboard-layout');
    if (!layout) return;

    async function init() {
      const user = await checkSession();

      if (!user) {
        showToast('Login Required', 'Please login to access dashboard', 'warning');
        setTimeout(() => { window.location.href = '/login'; }, 1500);
        return;
      }

      currentUser = user;
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
        const [profileData, statsData] = await Promise.all([
          apiFetch(API.profile),
          apiFetch(API.stats)
        ]);

        if (profileData.success) {
          const user = profileData.user;
          const meals = Math.round(user.total_donations * 8);

          const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
          set('statMeals', meals || 0);
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
          setP('platMeals', s.total_meals_donated?.toLocaleString() || '—');
          setP('platCO2', s.total_co2_saved?.toFixed(1) || '—');
          setP('platUsers', s.total_users || '—');
          setP('platDonations', s.total_donations || '—');
        }
      } catch (err) {
        console.warn('[Overview] Error:', err);
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

    async function loadMyDonations() {
      const container = document.getElementById('myDonationsList');
      if (!container) return;

      container.innerHTML = '<div class="loading-state"><div class="loading-spinner"></div>Loading...</div>';

      try {
        const data = await apiFetch(`${API.getDonations}?donor_id=${currentUser.id}`);
        const donations = data.donations || [];

        if (!donations.length) {
          container.innerHTML = `
            <div style="text-align:center;padding:3rem;color:var(--text-muted)">
              <div style="font-size:3rem;margin-bottom:1rem">🍽️</div>
              <h3>No donations yet</h3>
              <p>Start donating to see your history here.</p>
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