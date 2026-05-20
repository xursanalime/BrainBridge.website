const API = '/api';
let TOKEN = localStorage.getItem('bb_tok') || null;

const E = id => document.getElementById(id);

async function api(method, path, body) {
  const h = { 'Content-Type': 'application/json' };
  if (TOKEN) h['Authorization'] = 'Bearer ' + TOKEN;
  const resp = await fetch(API + path, { method, headers: h, body: body ? JSON.stringify(body) : undefined });
  if (resp.status === 401) {
    location.href = '/';
    return;
  }
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.detail || 'Xato');
  return data;
}

async function loadData() {
  E('loader').classList.add('on');
  try {
    const stats = await api('GET', '/admin/stats');
    if (stats) {
      E('adm-tot').textContent = stats.total_users;
      E('adm-coins').textContent = (stats.total_coins || 0).toLocaleString();
      E('adm-xp').textContent = (stats.total_xp || 0).toLocaleString();
      E('adm-today').textContent = stats.new_today || 0;
    }

    const usrs = await api('GET', '/admin/users');
    if (usrs && usrs.users) {
      E('users-tbody').innerHTML = usrs.users.map(u => `
        <tr>
          <td>${u.id}</td>
          <td><div style="font-weight:700">${u.email}</div><div style="font-size:11px;color:var(--tx3)">${new Date(u.created_at).toLocaleDateString()}</div></td>
          <td>
            <div style="display:flex;gap:8px;align-items:center">
              <span>🪙 <input type="number" value="${u.coins || 0}" style="width:50px" onblur="updateUser(${u.id}, {coins: parseInt(this.value)})"></span>
              <span>⭐ <input type="number" value="${u.total_xp || 0}" style="width:60px" onblur="updateUser(${u.id}, {total_xp: parseInt(this.value)})"></span>
            </div>
          </td>
          <td>
            <button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id})">O'chirish</button>
          </td>
        </tr>
      `).join('');
    }
  } catch (err) {
    alert(err.message);
  } finally {
    E('loader').classList.remove('on');
  }
}

async function updateUser(id, data) {
  try {
    await api('POST', `/admin/users/${id}/update`, data);
  } catch (e) { alert(e.message); }
}

async function deleteUser(id) {
  if (!confirm("Foydalanuvchi o'chirilsinmi?")) return;
  try {
    await api('DELETE', `/admin/users/${id}`);
    loadData();
  } catch (e) { alert(e.message); }
}

// Initial load
if (!TOKEN) {
  location.href = '/';
} else {
  loadData();
}
