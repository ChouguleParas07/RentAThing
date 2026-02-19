/**
 * Rent-a-Thing — simple frontend (vanilla JS, no build).
 * API base: set in API_BASE below or via window.__API_BASE__.
 */

// Use same origin when served from same host (e.g. FastAPI static); else localhost backend
const API_BASE = window.__API_BASE__ ?? (document.location.protocol !== 'file:' ? '' : 'http://localhost:8000');

const TOKEN_KEY = 'rentathing_access_token';
const USER_KEY = 'rentathing_user';

// --- API helpers ---
function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setAuth(token, user) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
}

function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
  } catch {
    return null;
  }
}

async function api(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(url, { ...options, headers });
  const data = res.ok ? await res.json().catch(() => ({})) : await res.json().catch(() => ({ detail: res.statusText }));
  if (!res.ok) throw new Error(Array.isArray(data.detail) ? 'Validation error' : (data.detail || res.statusText));
  return data;
}

// --- Router (hash) ---
let currentUser = getUser();

function navigate(path) {
  window.location.hash = path || '#';
  render();
}

function getRoute() {
  const hash = (window.location.hash || '#').slice(1) || 'home';
  const [path, id] = hash.split('/').filter(Boolean);
  return { path: path || 'home', id: id || null };
}

// --- Render ---
async function render() {
  const app = document.getElementById('app');
  if (!app) return;
  const route = getRoute();
  const user = getUser();
  currentUser = user;

  let nav = '';
  nav += `<a href="#home">Browse</a>`;
  if (user) {
    nav += ` <a href="#bookings">My bookings</a>`;
    if (user.role === 'OWNER' || user.role === 'ADMIN') {
      nav += ` <a href="#my-items">My Items</a>`;
      nav += ` <a href="#owner-bookings">Owner Bookings</a>`;
    }
    nav += ` <a href="#messages">Messages</a>`;
    nav += ` <span class="user">${escapeHtml(user.email)}</span>`;
    nav += ` <button type="button" data-logout>Log out</button>`;
  } else {
    nav += ` <a href="#login">Log in</a>`;
    nav += ` <a href="#register">Register</a>`;
  }

  // Show loading state first
  app.innerHTML = `<nav class="nav">${nav}</nav><main><p class="loading">Loading...</p></main>`;

  // Attach logout handler early
  app.querySelector('[data-logout]')?.addEventListener('click', () => {
    clearAuth();
    navigate('home');
  });

  let main = '';
  try {
    if (route.path === 'login') main = await renderLogin();
    else if (route.path === 'register') main = await renderRegister();
    else if (route.path === 'home') main = await renderHome();
    else if (route.path === 'item' && route.id) main = await renderItem(route.id);
    else if (route.path === 'items' && route.id === 'new') main = await renderAddItem();
    else if (route.path === 'items' && route.id && route.id.endsWith('/edit')) main = await renderEditItem(route.id.replace('/edit', ''));
    else if (route.path === 'my-items') main = await renderMyItems();
    else if (route.path === 'owner-bookings') main = await renderOwnerBookings();
    else if (route.path === 'messages') main = await renderMessages();
    else if (route.path === 'item' && route.id && route.id.includes('/reviews')) main = await renderItemReviews(route.id.split('/reviews')[0]);
    else if (route.path === 'bookings') main = await renderBookings();
    else main = await renderHome();
  } catch (e) {
    main = `<div class="card"><p class="error">${escapeHtml(e.message)}</p></div>`;
  }

  // Update main content
  const mainEl = app.querySelector('main');
  if (mainEl) mainEl.innerHTML = main;

  // Re-attach logout handler after content update
  app.querySelector('[data-logout]')?.addEventListener('click', () => {
    clearAuth();
    navigate('home');
  });
}

function escapeHtml(s) {
  if (s == null) return '';
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

// --- Views ---
async function renderLogin() {
  const html = `
    <h1 class="page-title">Log in</h1>
    <div class="card">
      <form id="login-form">
        <label>Email <input type="email" name="email" required /></label>
        <label>Password <input type="password" name="password" required /></label>
        <p id="login-error" class="error" style="display:none"></p>
        <button type="submit">Log in</button>
      </form>
    </div>
  `;
  setTimeout(() => {
    document.getElementById('login-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errEl = document.getElementById('login-error');
      errEl.style.display = 'none';
      const fd = new FormData(e.target);
      try {
        const tokens = await api('/auth/login', {
          method: 'POST',
          body: JSON.stringify({ email: fd.get('email'), password: fd.get('password') }),
        });
        const me = await api('/auth/me', { headers: { Authorization: `Bearer ${tokens.access_token}` } });
        setAuth(tokens.access_token, me);
        navigate('home');
      } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
      }
    });
  }, 0);
  return html;
}

async function renderRegister() {
  const html = `
    <h1 class="page-title">Register</h1>
    <div class="card">
      <form id="register-form">
        <label>Email <input type="email" name="email" required /></label>
        <label>Full name <input type="text" name="full_name" /></label>
        <label>Password <input type="password" name="password" minlength="8" required /></label>
        <label>Role
          <select name="role">
            <option value="RENTER">Renter</option>
            <option value="OWNER">Owner</option>
          </select>
        </label>
        <p id="register-error" class="error" style="display:none"></p>
        <button type="submit">Register</button>
      </form>
    </div>
  `;
  setTimeout(() => {
    document.getElementById('register-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errEl = document.getElementById('register-error');
      errEl.style.display = 'none';
      const fd = new FormData(e.target);
      try {
        await api('/auth/register', {
          method: 'POST',
          body: JSON.stringify({
            email: fd.get('email'),
            full_name: fd.get('full_name') || null,
            password: fd.get('password'),
            role: fd.get('role'),
          }),
        });
        navigate('login');
      } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
      }
    });
  }, 0);
  return html;
}

async function renderHome() {
  const data = await api('/items?limit=50');
  const items = data.items || [];
  const list = items.length
    ? `<div class="items-grid">${items.map((i) => `
        <a href="#item/${i.id}" class="item-card">
          <h3>${escapeHtml(i.title)}</h3>
          <p class="meta">${escapeHtml(i.description || '—')}</p>
          <p class="price">$${Number(i.daily_price).toFixed(2)} / day</p>
        </a>
      `).join('')}</div>`
    : '<p class="empty">No items yet. Register as Owner and add items via API or a future dashboard.</p>';
  return `<h1 class="page-title">Browse items</h1>${list}`;
}

async function renderItem(id) {
  const item = await api(`/items/${id}`);
  const user = getUser();
  const canBook = user && user.id !== item.owner_id;

  let bookForm = '';
  if (canBook) {
    bookForm = `
      <div class="card" style="margin-top:1rem">
        <h3>Request booking</h3>
        <form id="book-form">
          <input type="hidden" name="item_id" value="${escapeHtml(item.id)}" />
          <label>Start date <input type="date" name="start_date" required /></label>
          <label>End date <input type="date" name="end_date" required /></label>
          <label>Notes <input type="text" name="notes" /></label>
          <p id="book-error" class="error" style="display:none"></p>
          <p id="book-success" class="success" style="display:none"></p>
          <button type="submit">Request booking</button>
        </form>
      </div>
    `;
  } else if (!user) {
    bookForm = '<p class="muted">Log in to request a booking.</p>';
  }

  const html = `
    <a href="#home" class="btn-secondary" style="margin-bottom:1rem;display:inline-block">← Back</a>
    <div class="card">
      <h2>${escapeHtml(item.title)}</h2>
      <p class="meta">${escapeHtml(item.description || '—')}</p>
      <div class="detail-row"><strong>Price</strong> $${Number(item.daily_price).toFixed(2)} / day</div>
      <div class="detail-row"><strong>Deposit</strong> $${Number(item.security_deposit || 0).toFixed(2)}</div>
      ${item.location_text ? `<div class="detail-row"><strong>Location</strong> ${escapeHtml(item.location_text)}</div>` : ''}
    </div>
    ${bookForm}
  `;

  if (canBook) {
    setTimeout(() => {
      document.getElementById('book-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const errEl = document.getElementById('book-error');
        const okEl = document.getElementById('book-success');
        errEl.style.display = 'none';
        okEl.style.display = 'none';
        const fd = new FormData(e.target);
        try {
          await api('/bookings', {
            method: 'POST',
            body: JSON.stringify({
              item_id: item.id,
              start_date: fd.get('start_date'),
              end_date: fd.get('end_date'),
              notes: fd.get('notes') || null,
            }),
          });
          okEl.textContent = 'Booking requested. Check My bookings.';
          okEl.style.display = 'block';
          e.target.reset();
        } catch (err) {
          errEl.textContent = err.message;
          errEl.style.display = 'block';
        }
      });
    }, 0);
  }

  return html;
}

async function renderBookings() {
  const user = getUser();
  if (!user) {
    navigate('login');
    return '<p class="loading">Redirecting...</p>';
  }

  let data;
  try {
    data = await api('/bookings/me/renter');
  } catch {
    data = { bookings: [] };
  }
  const bookings = data.bookings || [];

  const list = bookings.length
    ? bookings.map((b) => `
        <div class="card booking-item">
          <div>
            <strong>Booking</strong> ${b.start_date} → ${b.end_date}
            <div class="meta">Total $${Number(b.total_price).toFixed(2)} · Status: <span class="status ${(b.status || '').toLowerCase()}">${escapeHtml(b.status)}</span></div>
          </div>
        </div>
      `).join('')
    : '<p class="empty">No bookings yet. Browse items and request a booking.</p>';

  return `<h1 class="page-title">My bookings</h1>${list}`;
}

// --- Owner Views ---

async function renderMyItems() {
  const user = getUser();
  if (!user) {
    navigate('login');
    return '<p class="loading">Redirecting...</p>';
  }
  
  if (user.role !== 'OWNER' && user.role !== 'ADMIN') {
    return `<div class="card"><p class="error">Only owners can view this page.</p></div>`;
  }

  let data;
  try {
    data = await api(`/items?owner_id=${user.id}&limit=50`);
  } catch {
    data = { items: [] };
  }
  const items = data.items || [];

  const list = items.length
    ? `<div class="items-grid">${items.map((i) => `
        <div class="item-card">
          <h3>${escapeHtml(i.title)}</h3>
          <p class="meta">${escapeHtml(i.description || '—')}</p>
          <p class="price">$${Number(i.daily_price).toFixed(2)} / day</p>
          <div style="margin-top:1rem;display:flex;gap:0.5rem">
            <a href="#item/${i.id}" class="btn btn-sm btn-secondary">View</a>
            <a href="#items/${i.id}/edit" class="btn btn-sm btn-primary">Edit</a>
          </div>
        </div>
      `).join('')}</div>`
    : '<p class="empty">You haven\'t added any items yet.</p>';

  return `<h1 class="page-title">My Items</h1>
    <a href="#items/new" class="btn btn-primary" style="margin-bottom:1rem">Add New Item</a>
    ${list}`;
}

async function renderAddItem() {
  const user = getUser();
  if (!user) {
    navigate('login');
    return '<p class="loading">Redirecting...</p>';
  }
  
  if (user.role !== 'OWNER' && user.role !== 'ADMIN') {
    return `<div class="card"><p class="error">Only owners can add items.</p></div>`;
  }

  const html = `
    <h1 class="page-title">Add New Item</h1>
    <a href="#my-items" class="btn-secondary" style="margin-bottom:1rem;display:inline-block">← Back to My Items</a>
    <div class="card">
      <form id="add-item-form">
        <label>Title <input type="text" name="title" required /></label>
        <label>Description <textarea name="description" rows="3"></textarea></label>
        <label>Daily Price ($) <input type="number" name="daily_price" step="0.01" min="0" required /></label>
        <label>Security Deposit ($) <input type="number" name="security_deposit" step="0.01" min="0" value="0" /></label>
        <label>Location <input type="text" name="location_text" /></label>
        <p id="add-item-error" class="error" style="display:none"></p>
        <p id="add-item-success" class="success" style="display:none"></p>
        <button type="submit" class="btn btn-primary">Create Item</button>
      </form>
    </div>
  `;

  setTimeout(() => {
    document.getElementById('add-item-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errEl = document.getElementById('add-item-error');
      const okEl = document.getElementById('add-item-success');
      errEl.style.display = 'none';
      okEl.style.display = 'none';
      const fd = new FormData(e.target);
      try {
        await api('/items', {
          method: 'POST',
          body: JSON.stringify({
            title: fd.get('title'),
            description: fd.get('description') || null,
            daily_price: parseFloat(fd.get('daily_price')),
            security_deposit: parseFloat(fd.get('security_deposit')) || 0,
            location_text: fd.get('location_text') || null,
          }),
        });
        okEl.textContent = 'Item created successfully!';
        okEl.style.display = 'block';
        e.target.reset();
        setTimeout(() => navigate('my-items'), 1500);
      } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
      }
    });
  }, 0);

  return html;
}

async function renderEditItem(id) {
  const user = getUser();
  if (!user) {
    navigate('login');
    return '<p class="loading">Redirecting...</p>';
  }
  
  if (user.role !== 'OWNER' && user.role !== 'ADMIN') {
    return `<div class="card"><p class="error">Only owners can edit items.</p></div>`;
  }

  let item;
  try {
    item = await api(`/items/${id}`);
  } catch (err) {
    return `<div class="card"><p class="error">Item not found.</p></div>`;
  }

  const html = `
    <h1 class="page-title">Edit Item</h1>
    <a href="#my-items" class="btn-secondary" style="margin-bottom:1rem;display:inline-block">← Back to My Items</a>
    <div class="card">
      <form id="edit-item-form">
        <label>Title <input type="text" name="title" value="${escapeHtml(item.title)}" required /></label>
        <label>Description <textarea name="description" rows="3">${escapeHtml(item.description || '')}</textarea></label>
        <label>Daily Price ($) <input type="number" name="daily_price" step="0.01" min="0" value="${item.daily_price}" required /></label>
        <label>Security Deposit ($) <input type="number" name="security_deposit" step="0.01" min="0" value="${item.security_deposit || 0}" /></label>
        <label>Location <input type="text" name="location_text" value="${escapeHtml(item.location_text || '')}" /></label>
        <p id="edit-item-error" class="error" style="display:none"></p>
        <p id="edit-item-success" class="success" style="display:none"></p>
        <button type="submit" class="btn btn-primary">Update Item</button>
      </form>
    </div>
  `;

  setTimeout(() => {
    document.getElementById('edit-item-form')?.addEventListener('submit', async (e) => {
      e.preventDefault();
      const errEl = document.getElementById('edit-item-error');
      const okEl = document.getElementById('edit-item-success');
      errEl.style.display = 'none';
      okEl.style.display = 'none';
      const fd = new FormData(e.target);
      try {
        await api(`/items/${id}`, {
          method: 'PATCH',
          body: JSON.stringify({
            title: fd.get('title'),
            description: fd.get('description') || null,
            daily_price: parseFloat(fd.get('daily_price')),
            security_deposit: parseFloat(fd.get('security_deposit')) || 0,
            location_text: fd.get('location_text') || null,
          }),
        });
        okEl.textContent = 'Item updated successfully!';
        okEl.style.display = 'block';
      } catch (err) {
        errEl.textContent = err.message;
        errEl.style.display = 'block';
      }
    });
  }, 0);

  return html;
}

async function renderOwnerBookings() {
  const user = getUser();
  if (!user) {
    navigate('login');
    return '<p class="loading">Redirecting...</p>';
  }
  
  if (user.role !== 'OWNER' && user.role !== 'ADMIN') {
    return `<div class="card"><p class="error">Only owners can view this page.</p></div>`;
  }

  let data;
  try {
    data = await api('/bookings/me/owner');
  } catch {
    data = { bookings: [] };
  }
  const bookings = data.bookings || [];

  const list = bookings.length
    ? bookings.map((b) => `
        <div class="card booking-item">
          <div>
            <strong>Booking #${b.id.slice(0, 8)}</strong>
            <div class="meta">${b.start_date} → ${b.end_date}</div>
            <div class="meta">Total: $${Number(b.total_price).toFixed(2)}</div>
            <div class="meta">Status: <span class="status ${(b.status || '').toLowerCase()}">${escapeHtml(b.status)}</span></div>
            <div style="margin-top:1rem;display:flex;gap:0.5rem">
              ${b.status === 'REQUESTED' ? `<button class="btn btn-sm btn-success" data-approve="${b.id}">Approve</button>` : ''}
              ${b.status === 'REQUESTED' ? `<button class="btn btn-sm btn-danger" data-reject="${b.id}">Reject</button>` : ''}
              ${b.status === 'APPROVED' ? `<button class="btn btn-sm btn-primary" data-complete="${b.id}">Mark Completed</button>` : ''}
            </div>
          </div>
        </div>
      `).join('')
    : '<p class="empty">No bookings for your items yet.</p>';

  setTimeout(() => {
    document.querySelectorAll('[data-approve]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const bookingId = btn.dataset.approve;
        try {
          await api(`/bookings/${bookingId}/status?new_status=APPROVED`, { method: 'PATCH' });
          render();
        } catch (err) {
          alert(err.message);
        }
      });
    });
    document.querySelectorAll('[data-reject]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const bookingId = btn.dataset.reject;
        try {
          await api(`/bookings/${bookingId}/status?new_status=REJECTED`, { method: 'PATCH' });
          render();
        } catch (err) {
          alert(err.message);
        }
      });
    });
    document.querySelectorAll('[data-complete]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const bookingId = btn.dataset.complete;
        try {
          await api(`/bookings/${bookingId}/status?new_status=COMPLETED`, { method: 'PATCH' });
          render();
        } catch (err) {
          alert(err.message);
        }
      });
    });
  }, 0);

  return `<h1 class="page-title">Owner Bookings</h1>${list}`;
}

// --- Messages/Chat ---

async function renderMessages() {
  const user = getUser();
  if (!user) {
    navigate('login');
    return '<p class="loading">Redirecting...</p>';
  }

  let data;
  try {
    data = await api('/chat/conversations?limit=50');
  } catch {
    data = { messages: [] };
  }
  
  const messages = data.messages || [];
  
  const conversations = {};
  messages.forEach(msg => {
    const convId = msg.conversation_id;
    if (!conversations[convId]) {
      conversations[convId] = {
        id: convId,
        lastMessage: msg,
        otherUserId: msg.sender_id === user.id ? msg.receiver_id : msg.sender_id
      };
    }
  });

  const convList = Object.values(conversations).length
    ? Object.values(conversations).map(c => `
        <div class="card" style="cursor:pointer" onclick="window.location.hash='#chat/${c.id}'">
          <strong>Conversation ${c.id.slice(0, 8)}</strong>
          <p class="meta">${escapeHtml(c.lastMessage.content || '')}</p>
          <div class="meta">${new Date(c.lastMessage.created_at).toLocaleString()}</div>
        </div>
      `).join('')
    : '<p class="empty">No conversations yet.</p>';

  return `<h1 class="page-title">Messages</h1>
    <div class="card">
      <p>Real-time chat is available via WebSocket at /chat/ws/{conversation_id}</p>
    </div>
    ${convList}`;
}

// --- Reviews ---

async function renderItemReviews(itemId) {
  let data;
  try {
    data = await api(`/reviews/items/${itemId}`);
  } catch {
    data = { reviews: [] };
  }
  
  const reviews = data.reviews || [];
  const user = getUser();
  
  let reviewForm = '';
  if (user && user.role === 'RENTER') {
    reviewForm = `
      <div class="card" style="margin-top:1rem">
        <h3>Add a Review</h3>
        <form id="review-form">
          <input type="hidden" name="item_id" value="${itemId}" />
          <label>Rating (1-5) <input type="number" name="rating" min="1" max="5" required /></label>
          <label>Comment <textarea name="comment" rows="3"></textarea></label>
          <p id="review-error" class="error" style="display:none"></p>
          <p id="review-success" class="success" style="display:none"></p>
          <button type="submit" class="btn btn-primary">Submit Review</button>
        </form>
      </div>
    `;
    
    setTimeout(() => {
      document.getElementById('review-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const errEl = document.getElementById('review-error');
        const okEl = document.getElementById('review-success');
        errEl.style.display = 'none';
        okEl.style.display = 'none';
        const fd = new FormData(e.target);
        try {
          await api('/reviews', {
            method: 'POST',
            body: JSON.stringify({
              item_id: itemId,
              rating: parseInt(fd.get('rating')),
              comment: fd.get('comment') || null,
            }),
          });
          okEl.textContent = 'Review submitted!';
          okEl.style.display = 'block';
          e.target.reset();
          render();
        } catch (err) {
          errEl.textContent = err.message;
          errEl.style.display = 'block';
        }
      });
    }, 0);
  }

  const reviewList = reviews.length
    ? reviews.map(r => `
        <div class="card">
          <div class="rating">
            ${Array(5).fill(0).map((_, i) => `<span class="rating-star ${i < r.rating ? '' : 'empty'}">★</span>`).join('')}
          </div>
          <p>${escapeHtml(r.comment || '')}</p>
          <div class="meta">By user ${r.author_id?.slice(0, 8) || 'unknown'} on ${new Date(r.created_at).toLocaleDateString()}</div>
        </div>
      `).join('')
    : '<p class="empty">No reviews yet.</p>';

  return `
    <a href="#item/${itemId}" class="btn-secondary" style="margin-bottom:1rem;display:inline-block">← Back to Item</a>
    <h1 class="page-title">Reviews</h1>
    ${reviewForm}
    ${reviewList}
  `;
}

// --- Init ---
window.addEventListener('hashchange', render);
window.addEventListener('load', render);
