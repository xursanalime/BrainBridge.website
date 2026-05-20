const APPLE_EMOJIS = {
  '🌟': '/img/emojis/1f31f.png',
  '💡': '/img/emojis/1f4a1.png',
  '🔍': '/img/emojis/1f50d.png',
  '🔴': '/img/emojis/1f534.png',
  '❌': '/img/emojis/274c.png',
  '📖': '/img/emojis/1f4d6.png',
  '📊': '/img/emojis/1f4ca.png',
  '⚠️': '/img/emojis/26a0-fe0f.png',
  '🧠': '/img/emojis/1f9e0.png',
  '🔥': '/img/emojis/1f525.png',
  '✅': '/img/emojis/2705.png',
  '🎉': '/img/emojis/1f389.png',
  '🚀': '/img/emojis/1f680.png',
  '📸': '/img/emojis/1f4f8.png',
  '💜': '/img/emojis/1f49c.png',
  '🏆': '/img/emojis/1f3c6.png',
  '👉': '/img/emojis/1f449.png',
  '🧙': '/img/emojis/1f9d9.png',
  '👋': '/img/emojis/1f44b.png',
  '🟡': '/img/emojis/1f7e1.png',
  '📚': '/img/emojis/1f4da.png',
  '🧙‍♂️': '/img/emojis/1f9d9-200d-2642-fe0f.png',
  '🤖': '/img/emojis/1f916.png',
  '🌱': '/img/emojis/1f331.png',
  '💛': '/img/emojis/1f49b.png',
  '🎓': '/img/emojis/1f393.png',
  '⚡': '/img/emojis/26a1.png',
  '👤': '/img/emojis/1f464.png',
  '🦉': '/img/emojis/1f989.png',
  '💎': '/img/emojis/1f48e.png',
  '🌅': '/img/emojis/1f305.png',
  '✍': '/img/emojis/270d-fe0f.png',
  '🎙': '/img/emojis/1f399-fe0f.png',
  '🇬🇧': '/img/emojis/1f1ec-1f1e7.png',
  '🇺🇸': '/img/emojis/1f1fa-1f1f8.png',
  '✓': '/img/emojis/2714-fe0f.png',
};

function ap(emoji) {
  const url = APPLE_EMOJIS[emoji] || `/img/emojis/1f9e0.png`;
  return `<img src="${url}" class="apple-emoji" alt="${emoji}">`;
}

const API='/api';
const BOX_COLORS=['#8888b8','#ff4d6d','#ffb84d','#7c5cfc','#c084fc','#00e5a0'];
const BOX_BG=['rgba(136,136,184,.12)','rgba(255,77,109,.12)','rgba(255,184,77,.12)','rgba(124,92,252,.12)','rgba(192,132,252,.12)','rgba(0,229,160,.12)'];
const BOX_EMOJIS=['🌱','🔴','🟡','💜','🌟','✅'].map(e=>ap(e));

const BOX_LABELS=['Yangi','1-bosqich','2-bosqich','3-bosqich','4-bosqich',"O'rganildi"];
const BOX_SUBS=["Hali o'rganilmagan","1 kundan keyin","3 kundan keyin","7 kundan keyin","14 kundan keyin","30 kundan keyin"];
let TOKEN=localStorage.getItem('bb_tok')||null;
let ME=JSON.parse(localStorage.getItem('bb_me')||'null');
let testWords=[],testIdx=0,testMode='write',quizMode='uz2en',curBox=0;
let testGroups=[],testGrpIdx=0,_grpRemain=[],_grpFound=[];
function _buildGroups(words){
  const map={};
  for(const w of words){const k=w.translation.toLowerCase().trim();if(!map[k])map[k]=[];map[k].push(w);}
  return Object.values(map).sort(()=>Math.random()-.5);
}
const E=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');

window.onerror = function(msg, url, line, col, error) {

  console.error("Global Error:", msg, "at", line, ":", col);
  return false;
};


/* ── API helper ─────────────────────────────────── */
async function api(method,path,body, isRetry=false){
  const h={'Content-Type':'application/json'};
  if(TOKEN)h['Authorization']='Bearer '+TOKEN;
  let resp;
  try{resp=await fetch(API+path,{method,headers:h,body:body?JSON.stringify(body):undefined});}
  catch{throw new Error("Backend ga ulanib bo'lmadi");}
  const txt=await resp.text();let data;
  try{data=JSON.parse(txt);}catch{throw new Error('Server xatosi ('+resp.status+')');}
  
  if(resp.status===401){
    if(!isRetry && path !== '/auth/refresh') {
      try {
        const refreshResp = await fetch(API+'/auth/refresh', {method: 'POST', credentials: 'include'});
        if (refreshResp.ok) {
           const refreshData = await refreshResp.json();
           TOKEN = refreshData.access_token;
           localStorage.setItem('bb_tok', TOKEN);
           return await api(method, path, body, true); // retry original request
        }
      } catch (e) {
        console.error("Token refresh failed", e);
      }
    }
    autoLogout();throw new Error("Sessiya tugadi. Qayta kiring.");
  }
  if(!resp.ok){
    const err = new Error(data.detail||'Xato');
    err.status = resp.status;
    throw err;
  }
  
  if(data.new_achievements && data.new_achievements.length){
    data.new_achievements.forEach(a => {
      // Find badge info in ACHIEVEMENTS (actually we need to fetch it or hardcode common ones)
      toast('Yangi yutuq: ' + a, 'ok', 'Tabriklaymiz! 🎉');
    });
  }
  return data;
}

async function apiForm(path,body){
  let resp;
  try{resp=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:new URLSearchParams(body)});}
  catch{throw new Error("Backend ga ulanib bo'lmadi.");}
  const txt=await resp.text();let data;
  try{data=JSON.parse(txt);}catch{throw new Error('Server xatosi');}
  if(!resp.ok){
    const err = new Error(data.detail||'Xato');
    err.status = resp.status;
    throw err;
  }
  return data;
}

/* ── Toast & Audio ──────────────────────────────────────── */
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playSound(type) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    gain.gain.value = 0.15;
    if (type === 'correct') {
      osc.frequency.value = 523; osc.type = 'sine';
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.start(); osc.stop(ctx.currentTime + 0.3);
    } else if (type === 'wrong') {
      osc.frequency.value = 200; osc.type = 'square';
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
      osc.start(); osc.stop(ctx.currentTime + 0.25);
    } else if (type === 'levelUp') {
      osc.frequency.value = 440; osc.type = 'sine';
      setTimeout(() => { osc.frequency.value = 660; }, 100);
      setTimeout(() => { osc.frequency.value = 880; }, 200);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.start(); osc.stop(ctx.currentTime + 0.5);
    }
  } catch(e) {}
}



function toast(msg,type,title){
  if(msg.includes('Yutuq') || msg.includes('Tabriklaymiz')) playSound('levelUp');
  const icons={ok:ap('✅'),err:ap('❌'),warn:ap('💡')};
  const titles={ok:title||'Muvaffaqiyat',err:title||'Xato',warn:title||'Eslatma'};
  const el=E('toast');
  E('t-ico').innerHTML=icons[type]||ap('✅');
  E('t-ttl').textContent=titles[type];
  E('t-msg').innerHTML=msg;
  el.className='toast '+(type||'ok')+' show';
  clearTimeout(el._t);
  el._t=setTimeout(()=>el.classList.remove('show'),3400);
}
function showResult(correct,expected,given,box){
  if(correct)toast('"'+expected+'" — to\'g\'ri!','ok','To\'g\'ri → '+BOX_LABELS[box]);
  else toast('"'+given+'" emas — "'+expected+'"','warn','Xato → '+BOX_LABELS[box]);
}
const loading=v=>E('ov').classList.toggle('on',v);
function spinBtn(btn,v){if(v){btn._o=btn.innerHTML;btn.innerHTML='<span class="spin"></span>';btn.disabled=true;}else{btn.innerHTML=btn._o||btn.textContent;btn.disabled=false;}}

let _confirmCb = null;
function confirmDialog(title, msg, onConfirm) {
  E('m-title').textContent = title;
  E('m-body').innerHTML = `<div style="font-size:14px;color:var(--tx3);line-height:1.5">${msg}</div>`;
  E('m-acts').innerHTML = `
    <button class="btn btn-ghost" onclick="closeModal()">Bekor qilish</button>
    <button class="btn btn-danger" id="m-confirm-btn">Tasdiqlash</button>
  `;
  _confirmCb = onConfirm;
  E('m-confirm-btn').onclick = () => { _confirmCb(); closeModal(); };
  E('modal').classList.add('open');
}


function showPremiumLock(featureName) {
  toast(featureName + " funksiyasi vaqtincha mavjud emas.", 'warn');
}

/* ── Landing / Auth navigation ──────────────────── */
function showLanding(){
  E('landing').classList.remove('hidden');
  E('auth').classList.remove('on');
  E('app').classList.remove('on');
  // Load real public stats
  fetch(BASE+'/stats/public').then(r=>r.json()).then(d=>{
    animateCount('statUsers', d.total_users || 847);
    animateCount('statWords', d.total_words || 15420);
  }).catch(()=>{});
}
function animateCount(id, target) {
  const el = E(id); if(!el) return;
  let cur = 0; const step = Math.max(1, Math.ceil(target / 40));
  const timer = setInterval(() => {
    cur += step; if(cur >= target) { cur = target; clearInterval(timer); }
    el.textContent = cur.toLocaleString('uz-UZ');
  }, 30);
}
function openAuthPage(tab){
  E('landing').classList.add('hidden');
  E('auth').classList.add('on');
  E('app').classList.remove('on');
  _switchPanel('panel-login');
  authTab(tab||'login');
}

/* ── Auth ───────────────────────────────────────── */
function authTab(t){
  document.querySelectorAll('.tab').forEach((b,i)=>b.classList.toggle('on',(i===0&&t==='login')||(i===1&&t==='reg')));
  E('lf').style.display=t==='login'?'':'none';
  E('rf').style.display=t==='reg'?'':'none';
  E('a-err').textContent='';
}
async function doLogin(){
  const em=E('l-e').value.trim(),pw=E('l-p').value;
  if(!em||!pw){E('a-err').textContent='Email va parolni kiriting.';return;}
  const btn=E('l-btn');spinBtn(btn,true);
  try{
    const d=await apiForm('/auth/login',{username:em,password:pw});
    saveS(d);
    if(d.needs_password_update){
      toast('Xavfsizlik yuzasidan parolingizni yangilashingiz kerak (kamida 8 belgi).','warn','Yangi qoida!');
      setTimeout(()=>openForcePasswordUpdate(), 500);
    } else {
      enterApp();
    }
  }
  catch(e){E('a-err').textContent=e.message;}finally{spinBtn(btn,false);}
}
async function doReg(){
  const em=E('r-e').value.trim(),pw=E('r-p').value,pw2=E('r-p2').value;
  if(!em||!pw||!pw2){E('a-err').textContent="Barcha maydonlarni to'ldiring.";return;}
  if(pw.length<8){E('a-err').textContent='Parol kamida 8 ta belgi bo\'lsin.';return;}
  if(pw!==pw2){E('a-err').textContent='Parollar mos kelmadi.';return;}
  const btn=E('r-btn');spinBtn(btn,true);
  try{const d=await api('POST','/auth/register',{email:em,password:pw});saveS(d);enterApp();}
  catch(e){E('a-err').textContent=e.message;}finally{spinBtn(btn,false);}
}
function saveS(d){TOKEN=d.access_token;ME={id:d.user_id,email:d.email,is_admin:d.is_admin};localStorage.setItem('bb_tok',TOKEN);localStorage.setItem('bb_me',JSON.stringify(ME));}

/* Google OAuth */
function _handleGoogleCallback(){
  const p=new URLSearchParams(location.search);
  const gt=p.get('google_token');const uid=p.get('user_id');const em=p.get('email');const adm=p.get('is_admin');const err=p.get('auth_error');
  if(gt&&uid&&em){TOKEN=gt;ME={id:parseInt(uid),email:em,is_admin:adm==='1'};localStorage.setItem('bb_tok',TOKEN);localStorage.setItem('bb_me',JSON.stringify(ME));history.replaceState({},'','/');return true;}
  if(err){history.replaceState({},'','/');if(E('a-err'))E('a-err').textContent='Google kirish xatoligi: '+err;return false;}
  return false;
}

/* Forgot / Reset */
const AUTH_PANELS=['panel-login','panel-forgot','panel-reset'];
function _switchPanel(id){AUTH_PANELS.forEach(p=>{const el=E(p);if(el)el.style.display=p===id?'':'none';});}
function openForgot(){_switchPanel('panel-forgot');E('fg-err').textContent='';E('fg-err').style.color='var(--red)';setTimeout(()=>E('fg-e')&&E('fg-e').focus(),100);}
function openLoginPanel(){_switchPanel('panel-login');E('a-err').textContent='';}
async function doForgot(){
  const em=E('fg-e').value.trim();
  if(!em){E('fg-err').textContent='Email kiriting.';return;}
  const btn=E('fg-btn');spinBtn(btn,true);
  try{const r=await api('POST','/auth/forgot-password',{email:em});E('fg-err').style.color='var(--grn)';E('fg-err').textContent=r.message||'Xat yuborildi.';}
  catch(e){E('fg-err').style.color='var(--red)';E('fg-err').textContent=e.message;}finally{spinBtn(btn,false);}
}
let _resetToken=null;
function openResetPanel(token){_resetToken=token;_switchPanel('panel-reset');E('rp-err').textContent='';E('rp-err').style.color='var(--red)';setTimeout(()=>E('rp-new')&&E('rp-new').focus(),100);}
async function doResetPassword(){
  const nw=E('rp-new').value,con=E('rp-con').value;
  const errEl=E('rp-err');errEl.style.color='var(--red)';errEl.textContent='';
  if(!nw||!con){errEl.textContent='Parolni kiriting.';return;}
  if(nw.length<8){errEl.textContent='Parol kamida 8 ta belgi bo\'lsin.';return;}
  if(nw!==con){errEl.textContent='Parollar mos emas.';return;}
  const btn=E('rp-btn');spinBtn(btn,true);
  try{
    const r=await api('POST','/auth/reset-password',{token:_resetToken,new_password:nw});
    errEl.style.color='var(--grn)';errEl.textContent=r.message||'Parol tiklandi.';
    setTimeout(()=>{history.replaceState(null,'','/');_resetToken=null;showLanding();},2200);
  }catch(e){errEl.textContent=e.message;}finally{spinBtn(btn,false);}
}

function getAvHtml(url, initials) {
  if (url) {
    const buster = Date.now();
    return `<img src="${url}?v=${buster}" class="av-img" onerror="this.outerHTML='<div class=&quot;av-init&quot;>${initials}</div>'">`;

  }
  return `<div class="av-init">${initials}</div>`;
}

function updateAdminUI() {
  if (ME?.is_admin) {
    if (E('nav-admin')) E('nav-admin').style.display = 'flex';
    if (E('mob-admin')) E('mob-admin').style.display = 'flex';
  } else {
    if (E('nav-admin')) E('nav-admin').style.display = 'none';
    if (E('mob-admin')) E('mob-admin').style.display = 'none';
  }
}

/* Enter app */
function enterApp(){
  try {
    E('landing').classList.add('hidden');
    E('auth').classList.remove('on');
    E('app').classList.add('on');
    
    updateAdminUI();
    const em=ME?.email||'';
    const avUrl=ME?.avatar_url;
    const initials=em.slice(0,2).toUpperCase();
    const avHtml = getAvHtml(avUrl, initials);
    
    const xp = ME?.total_xp || 0;
    const level = Math.floor(Math.sqrt(xp/100)) + 1;
    
    ['m-av','sb-av'].forEach(id=>{const el=E(id);if(el) el.innerHTML=avHtml;});
    const sbEm=E('sb-em');if(sbEm)sbEm.textContent=em;
    const sbRole=document.querySelector('.u-role'); if(sbRole) sbRole.textContent = `Lvl ${level} Student`;
  
    const nameEl=E('pf-name');if(nameEl)nameEl.textContent=ME?.full_name || em.split('@')[0];
    const emailEl=E('pf-email');if(emailEl)emailEl.textContent=em;
    const lvlEl=E('pf-level-badge');
    if(lvlEl) lvlEl.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.46 21z"/></svg> Level: ${level} ${getRankTitle(level)}`;
    
    const pfAvContent = E('pf-av-content');
    if(pfAvContent) pfAvContent.innerHTML = avHtml;
  
    const greeting=E('ph-greeting');
    if(greeting){const name=ME?.full_name || em.split('@')[0];greeting.innerHTML='Xush kelibsiz, '+name+' '+ap('👋');}
    const dateEl=E('ph-date');
    if(dateEl){const d=new Date();dateEl.textContent=d.toLocaleDateString('uz-UZ',{weekday:'long',day:'numeric',month:'long'});}
    go('dash');
  } catch(err) {
    console.error("enterApp error:", err);
    toast("Ilovaga kirishda xatolik: " + err.message, "err");
  }
}


function autoLogout(){TOKEN=null;ME=null;localStorage.removeItem('bb_tok');localStorage.removeItem('bb_me');showLanding();}
function doLogout(){TOKEN=null;ME=null;localStorage.removeItem('bb_tok');localStorage.removeItem('bb_me');showLanding();toast('Chiqildi','ok','Xayr!');}

/* ── Navigation ─────────────────────────────────── */
function go(page){
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
  document.querySelectorAll('.nav,.bni').forEach(b=>b.classList.toggle('on',b.dataset.p===page));
  E('p-'+page).classList.add('on');
  if(page==='dash')loadDash();
  if(page==='mywords')loadWords();
  if(page==='learn')loadBoxes();
  if(page==='stats')loadLeaderboard('alltime');
  if(page==='profile')loadProfile();
  if(page==='admin')loadAdmin();
  if(page==='aichat')loadChatSessions();
  if(page==='sentences')loadSentenceStats();
}

function toggleMenu(show) {
  const el = E('mob-menu-bg');
  if (show) el.classList.add('open');
  else el.classList.remove('open');
}




/* ── Dashboard ──────────────────────────────────── */
async function loadDash(){
  try{
    const d=await api('GET','/words/stats');
    const total=d.total||0;const mastered=d.boxes?.[5]||0;
    const pct=total>0?Math.round((mastered/total)*100):0;
    E('pb-score').textContent=total;
    E('pb-pct').textContent=pct+'%';
    const arc=E('pb-arc');
    if(arc){const circ=226;arc.style.strokeDashoffset=circ-(circ*(pct/100));}
    const due=d.due||0;
    E('due-wrap').innerHTML=due>0?`
      <div class="due-card">
        <div>
          <div class="due-n">${due} ta so'z</div>
          <div class="due-s">Bugun takrorlash kerak ${ap('⏰')}</div>

        </div>
        <button class="due-badge" onclick="go('learn')">O'rganish →</button>
      </div>
    `:'';
    const statData=[
      {icon:ap('📚'),bg:'rgba(124,92,252,.12)',col:'#7c5cfc',val:total,lbl:"Jami so'zlar"},
      {icon:ap('✅'),bg:'rgba(0,229,160,.1)',col:'#00e5a0',val:mastered,lbl:"O'rganildi"},
      {icon:ap('⏳'),bg:'rgba(255,184,77,.1)',col:'#ffb84d',val:due,lbl:"Bugun"},
      {icon:ap('🔥'),bg:'rgba(255,77,109,.1)',col:'#ff4d6d',val:(d.streak||0)+' kun',lbl:"Ketma-ketlik"}
    ];

    E('stat-grid').innerHTML=statData.map(s=>`
      <div class="sc" style="border-color:var(--bd)">
        <div class="sc-icon-wrap" style="background:${s.bg}">${s.icon}</div>
        <div class="sc-val" style="color:${s.col}">${s.val}</div>
        <div class="sc-lbl">${s.lbl}</div>
      </div>`).join('');
    const boxes=d.boxes||{};
    E('box-dash').innerHTML=Array.from({length:6},(_,i)=>`
      <div class="bd-cell" onclick="go('learn')" style="${boxes[i]>0?'border-color:'+BOX_BG[i].replace('.12','.4')+';':'' }">
        <div class="bd-num" style="color:${BOX_COLORS[i]}">${boxes[i]||0}</div>
        <div class="bd-lbl">${BOX_LABELS[i]}</div>
      </div>`).join('');
    
    // Load gamification stats for dash
    const gs = await api('GET', '/stats/me');
    ME = gs;
    localStorage.setItem('bb_me', JSON.stringify(ME));
    updateAdminUI();
    const level = Math.floor(Math.sqrt((gs.total_xp||0)/100)) + 1;
    const rank = getRankTitle(level);
    const xpForNext = Math.pow(level, 2) * 100;
    const xpForPrev = Math.pow(level-1, 2) * 100;
    const progress = ((gs.total_xp - xpForPrev) / (xpForNext - xpForPrev)) * 100;

    const sg = E('stat-grid');
    if (sg) {
      sg.innerHTML += `
        <div class="sc" style="border-color:var(--bd);background:linear-gradient(135deg,rgba(124,92,252,.1),transparent)">
          <div class="sc-icon-wrap" style="background:rgba(255,215,0,.15)">🏆</div>
          <div class="sc-val" style="color:#ffd700">#${gs.rank}</div>
          <div class="sc-lbl">Sizning o'rningiz</div>
        </div>
        <div class="sc" style="border-color:var(--bd);background:linear-gradient(135deg,rgba(0,212,255,.1),transparent)">
          <div class="sc-icon-wrap" style="background:rgba(0,212,255,.15)">💎</div>
          <div class="sc-val" style="color:#00d4ff">${gs.total_xp}</div>
          <div class="sc-lbl">Jami XP</div>
        </div>
      `;
    }
    
    // XP Progress Bar in Dashboard
    const pbLeft = document.querySelector('#progress-banner > div:first-child');
    if (pbLeft) {
      // Remove old bar if exists to prevent duplication
      const oldBar = E('dashboard-xp-bar');
      if(oldBar) oldBar.remove();

      const xpb = document.createElement('div');
      xpb.id = 'dashboard-xp-bar';
      xpb.style.marginTop = '18px';
      xpb.style.minWidth = '240px';
      xpb.innerHTML = `
        <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:6px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:rgba(255,255,255,0.7)">
          <span>Level ${level}</span>
          <span>${gs.total_xp} / ${xpForNext} XP</span>
        </div>
        <div class="prog" style="height:8px;background:rgba(255,255,255,0.1);border-radius:4px">
          <div class="prog-f" style="width:${progress}%;background:linear-gradient(90deg, #7c5cfc, #00d4ff)"></div>
        </div>
      `;
      pbLeft.appendChild(xpb);
    }

    // Populate Daily Quests
    const qList = E('quests-list');
    if (qList) {
      E('quest-date').textContent = new Date().toLocaleDateString('uz-UZ');
      const quests = [
        {title: `${gs.goal_reviews} ta so'z takrorlash`, cur: gs.daily_reviews || 0, target: gs.goal_reviews, icon: '📖'},
        {title: `${gs.goal_xp} XP to'plash`, cur: gs.daily_xp || 0, target: gs.goal_xp, icon: '⚡'}
      ];
      qList.innerHTML = quests.map(q => {
        const pct = Math.min(100, (q.cur / q.target) * 100);
        return `
          <div style="background:var(--bg3);padding:12px;border-radius:12px;border:1px solid var(--bd2)">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px">
              <div style="display:flex;align-items:center;gap:8px">
                <span>${ap(q.icon)}</span>
                <span style="font-size:14px;font-weight:600;color:var(--tx)">${q.title}</span>
              </div>
              <span style="font-size:12px;color:var(--tx3)">${q.cur}/${q.target}</span>
            </div>
            <div class="prog" style="height:6px;background:rgba(255,255,255,.05)"><div class="prog-f" style="width:${pct}%"></div></div>
          </div>
        `;
      }).join('');
    }
  }catch(e){console.error(e);}
}

/* ── Words list ─────────────────────────────────── */
async function loadWords(){
  const q=E('w-s').value.trim();const box=E('w-b').value;const ord=E('w-o').value;
  let url='/words?limit=200';
  if(q)url+='&search='+encodeURIComponent(q);
  if(box!=='')url+='&box='+box;
  if(ord)url+='&sort='+ord;
  try{
    const d=await api('GET',url);const words=d.words||[];
    if(!words.length){
      E('wlist').innerHTML=`<div class="empty"><div class="empty-icon">📖</div><div class="empty-t">So'z topilmadi</div><div class="empty-s">Yangi so'zlar qo'shing</div><button class="btn btn-blue" onclick="go('add')">Qo'shish</button></div>`;
      return;
    }
    E('wlist').innerHTML=words.map(w=>`
      <div class="wc">
        <div class="wc-icon">${BOX_EMOJIS[w.box||0]}</div>
        <div class="wc-info">
          <div class="wc-en">${esc(w.word)}</div>
          <div class="wc-uz">${esc(w.translation)}</div>
        </div>
        <span class="badge b${w.box||0}">${BOX_LABELS[w.box||0]}</span>
        <div class="wc-acts">

          <div class="ic-btn" title="Tahrirlash" onclick="editWord(${w.id},'${esc(w.word)}','${esc(w.translation)}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </div>
          <div class="ic-btn del" title="O'chirish" onclick="delWord(${w.id},'${esc(w.word)}')">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6M14 11v6"/></svg>
          </div>
        </div>
      </div>`).join('');
  }catch(e){toast(e.message,'err');}
}

/* ── Export & Clear ────────────────────────────── */
async function exportWords() {
  try {
    const res = await api('GET', '/words/export');
    if (!res.content) { toast("Eksport qilish uchun so'z yo'q", 'warn'); return; }
    
    const lines = res.content.split('\n').filter(l => l.trim());
    const today = new Date().toLocaleDateString('uz-UZ');
    
    let rows = '';
    lines.forEach((line, i) => {
      const parts = line.split(' - ');
      const word = parts[0] || '';
      const trans = parts.slice(1).join(' - ') || '';
      rows += `<tr style="background:${i%2===0?'#f8f8fc':'#fff'}">
        <td style="padding:8px 12px;color:#888;font-size:12px;border-bottom:1px solid #eee">${i+1}</td>
        <td style="padding:8px 12px;font-weight:600;color:#1a1a2e;border-bottom:1px solid #eee">${word}</td>
        <td style="padding:8px 12px;color:#555;border-bottom:1px solid #eee">${trans}</td>
      </tr>`;
    });
    
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8">
      <title>BrainBridge - So'zlar</title>
      <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;color:#1a1a2e}
        .header{background:linear-gradient(135deg,#7c5cfc,#00d4ff);padding:28px 32px;color:#fff}
        .header h1{font-size:24px;margin-bottom:4px}
        .header p{font-size:13px;opacity:.85}
        .info{padding:16px 32px;background:#f0f0ff;display:flex;gap:24px;font-size:13px;color:#555}
        .info b{color:#7c5cfc}
        table{width:100%;border-collapse:collapse;margin:0}
        th{background:#7c5cfc;color:#fff;padding:10px 12px;text-align:left;font-size:12px;text-transform:uppercase;letter-spacing:1px}
        .footer{padding:16px 32px;text-align:center;color:#aaa;font-size:11px;border-top:2px solid #7c5cfc}
        @media print{body{print-color-adjust:exact;-webkit-print-color-adjust:exact}}
      </style></head><body>
      <div class="header">
        <h1>🧠 BrainBridge</h1>
        <p>So'zlar ro'yxati • ${today}</p>
      </div>
      <div class="info">
        <span>Jami: <b>${lines.length}</b> ta so'z</span>
        <span>Sana: <b>${today}</b></span>
      </div>
      <table>
        <thead><tr>
          <th style="width:50px">#</th>
          <th>English</th>
          <th>O'zbekcha</th>
        </tr></thead>
        <tbody>${rows}</tbody>
      </table>
      <div class="footer">BrainBridge — Ingliz so'zlarini aqlli o'rganing</div>
      <script>window.onload=function(){window.print()}<\/script>
    </body></html>`;
    
    const printWin = window.open('', '_blank');
    printWin.document.write(html);
    printWin.document.close();
    
    toast(`${res.total} ta so'z PDF uchun tayyor`, 'ok', 'Chop etish oynasi ochildi ✅');
  } catch(e) { toast(e.message, 'err'); }
}

function clearAllWords() {
  confirmDialog(
    "Barcha so'zlarni o'chirish",
    "Haqiqatan ham <strong>barcha so'zlaringizni</strong> o'chirmoqchimisiz? Bu amalni qaytarib bo'lmaydi!",
    async () => {
      try {
        const res = await api('DELETE', '/words/clear-all');
        toast(`${res.deleted} ta so'z o'chirildi`, 'ok', "Tozalandi");
        loadWords();
        loadDash();
      } catch(e) { toast(e.message, 'err'); }
    }
  );
}

/* ── Boxes / Learn ──────────────────────────────── */
async function loadBoxes(){
  E('p-boxes').style.display='grid';E('p-inner').style.display='none';
  try{
    const d=await api('GET','/words/stats');const boxes=d.boxes||{};
    E('p-boxes').innerHTML=Array.from({length:6},(_,i)=>`
      <div class="bx" onclick="openBox(${i})" style="${boxes[i]>0?'border-color:'+BOX_BG[i].replace('.12','.35')+';':''}">
        <div class="bx-icon" style="background:${BOX_BG[i]}">${BOX_EMOJIS[i]}</div>
        <div class="bx-num" style="color:${BOX_COLORS[i]}">${boxes[i]||0}</div>
        <div class="bx-lbl">${BOX_LABELS[i]}</div>
        <div class="bx-sub">${BOX_SUBS[i]}</div>
      </div>`).join('');
  }catch(e){toast(e.message,'err');}
}

async function openBox(box){
  curBox=box;
  E('p-boxes').style.display='none';E('p-inner').style.display='block';
  E('test-a').style.display='none';
  document.querySelectorAll('#test-btns .btn').forEach(b=>b.style.display='');
  E('inner-t').textContent=BOX_LABELS[box];
  E('inner-s').textContent='Test turini tanlang';
  try{
    const d=await api('GET','/words?box='+box+'&limit=200');
    const words=d.words||[];
    E('inner-s').textContent=words.length+" ta so'z mavjud";
    testWords=words;
    E('btn-w').disabled=words.length===0;
    E('btn-q').disabled=words.length===0;
  }catch(e){toast(e.message,'err');}
}
function backToBoxes(){E('p-boxes').style.display='grid';E('p-inner').style.display='none';}

/* ── Tests ──────────────────────────────────────── */
function startTest(mode){
  testMode=mode;testIdx=0;
  if(!testWords.length){toast("So'z yo'q",'warn');return;}
  testGroups=_buildGroups([...testWords].sort(()=>Math.random()-.5));
  testGrpIdx=0;_grpRemain=[];_grpFound=[];_quizCorrects=[];
  document.querySelectorAll('#test-btns .btn').forEach(b=>b.style.display='none');
  E('test-a').style.display='block';
  renderQ();
}

function renderQ(){
  if(testMode==='write'){
    if(testGrpIdx>=testGroups.length){endTest();return;}
    const grp=testGroups[testGrpIdx];
    if(_grpRemain.length===0&&_grpFound.length===0){_grpRemain=grp.map(w=>w.id);}
    if(_grpRemain.length===0){testGrpIdx++;_grpRemain=[];_grpFound=[];renderQ();return;}
    const pct=Math.round((testGrpIdx/testGroups.length)*100);
    E('t-prog').style.width=pct+'%';
    E('t-meta').textContent=(testGrpIdx+1)+' / '+testGroups.length;
    E('t-write').style.display='';E('t-quiz').style.display='none';
    E('t-prompt').textContent=grp[0].translation;
    const total=grp.length,found=_grpFound.length;
    if(total>1&&found>0)E('t-hint').textContent='✅ '+found+'/'+total+' topildi — yana biri bormi?';
    else if(total>1)E('t-hint').textContent='Bu tarjimaning '+total+' ta inglizcha varianti bor';
    else E('t-hint').textContent="Inglizcha so'zini yozing";

    const inp=E('t-inp');inp.value='';inp.disabled=false;
    inp.placeholder="Inglizcha so'zini yozing...";
    setTimeout(()=>inp.focus(),80);
    return;
  }
  if(testGrpIdx>=testGroups.length){endTest();return;}
  const grp=testGroups[testGrpIdx];
  if(!grp._qmode)grp._qmode=Math.random()>.5?'en2uz':'uz2en';
  const qmode=grp._qmode;
  const pct=Math.round((testGrpIdx/testGroups.length)*100);
  E('t-prog').style.width=pct+'%';
  E('t-meta').textContent=(testGrpIdx+1)+' / '+testGroups.length;
  E('t-write').style.display='none';E('t-quiz').style.display='';
  const synWords=grp.map(w=>w.word.toLowerCase());
  const synTrans=grp[0].translation.toLowerCase();
  const fallbackEn=['apple','book','table','water','house','run','eat','sleep','work','study'];
  const fallbackUz=['olma','kitob','stol','suv','uy','yugurmoq','yemoq','uxlamoq','ishlash',"o'qish"];
  const synWordSet=new Set(synWords);
  if(qmode==='uz2en'){
    E('t-prompt').textContent=grp[0].translation;
    E('t-hint').textContent="Inglizcha so'zini tanlang";
    const official=grp[Math.floor(Math.random()*grp.length)].word;
    const otherWords=testWords.map(x=>x.word).filter(w=>!synWordSet.has(w.toLowerCase()));
    const pool=[...new Set(otherWords)].sort(()=>Math.random()-.5);
    const extra=fallbackEn.filter(f=>!synWordSet.has(f.toLowerCase()));
    const wrongs=[...pool,...extra].filter(w=>!synWordSet.has(w.toLowerCase())).filter((v,i,a)=>a.indexOf(v)===i).slice(0,3);
    _quizCorrects=synWords;
    const opts=[official,...wrongs].sort(()=>Math.random()-.5);
    E('t-opts').innerHTML=opts.map(o=>`<button class="qopt" onmousedown="this.blur()" onclick="answerQuizGrp(this,'${esc(o)}')">${esc(o)}</button>`).join('');
  }else{
    const w=grp[Math.floor(Math.random()*grp.length)];
    E('t-prompt').textContent=w.word;

    E('t-hint').textContent="O'zbek tarjimasini tanlang";
    const answer=w.translation;
    const otherTrans=testWords.map(x=>x.translation).filter(t=>t.toLowerCase()!==synTrans);
    const pool=[...new Set(otherTrans)].sort(()=>Math.random()-.5);
    const extra=fallbackUz.filter(f=>f.toLowerCase()!==synTrans);
    const wrongs=[...pool,...extra].filter(t=>t.toLowerCase()!==synTrans).filter((v,i,a)=>a.indexOf(v)===i).slice(0,3);
    _quizCorrects=[answer.toLowerCase()];
    const opts=[answer,...wrongs].sort(()=>Math.random()-.5);
    E('t-opts').innerHTML=opts.map(o=>`<button class="qopt" onmousedown="this.blur()" onclick="answerQuizGrp(this,'${esc(o)}')">${esc(o)}</button>`).join('');
  }
  if(document.activeElement)document.activeElement.blur();
}

let _quizCorrects=[];
async function answerQuizGrp(btn,chosen){
  document.querySelectorAll('.qopt').forEach(b=>b.disabled=true);
  const grp=testGroups[testGrpIdx];
  const ok=_quizCorrects.includes(chosen.toLowerCase());
  btn.classList.add(ok?'correct':'wrong');
  if(!ok){document.querySelectorAll('.qopt').forEach(b=>{if(_quizCorrects.includes(b.textContent.toLowerCase()))b.classList.add('correct');});}
  // Fire-and-forget (don't block on API)
  grp.forEach(w=>api('POST','/words/'+w.id+'/review',{correct:ok}).catch(()=>{}));
  if(ok){playSound('correct'); const allW=grp.map(w=>w.word).join(', ');toast(`"${allW}" — to\'g\'ri!`,'ok',"Yuqori bosqichga o'tdi ✅");}
  else{playSound('wrong'); toast(`To\'g\'ri: "${_quizCorrects.slice(0,2).join(' / ')}"`,'warn',"Orqaga qaytdi ↩");}
  setTimeout(()=>{testGrpIdx++;_quizCorrects=[];renderQ();},1300);
}

function tKey(e){if(e.key==='Enter')checkWrite();}

async function checkWrite(){
  const inp=E('t-inp');const btn=E('t-check-btn');
  if(inp.disabled)return;
  const given=inp.value.trim().toLowerCase();
  if(!given)return;
  inp.disabled=true;if(btn)btn.disabled=true;
  const grp=testGroups[testGrpIdx];
  const matched=grp.find(w=>_grpRemain.includes(w.id)&&w.word.toLowerCase()===given);
  if(matched){
    playSound('correct');
    inp.style.borderColor='var(--grn)';inp.style.background='rgba(0,229,160,.06)';
    _grpFound.push(matched.id);_grpRemain=_grpRemain.filter(id=>id!==matched.id);
    if(_grpRemain.length>0){
      toast('"'+matched.word+'" — to\'g\'ri! Yana biri bormi? 🔍','ok');
      setTimeout(()=>{inp.style.borderColor='';inp.style.background='';if(btn)btn.disabled=false;renderQ();},1200);
    }else{
      try{
        const results=await Promise.all(grp.map(w=>api('POST','/words/'+w.id+'/review',{correct:true})));
        const newBox=results[0]?.new_box??results[0]?.box??curBox;
        const allWords=grp.map(w=>w.word).join(', ');
        toast('"'+allWords+'" — barchasi topildi!','ok',BOX_LABELS[newBox]+' bosqichga o\'tdi ✅');
      }catch{}
      setTimeout(()=>{inp.style.borderColor='';inp.style.background='';if(btn)btn.disabled=false;testGrpIdx++;_grpRemain=[];_grpFound=[];renderQ();},1500);
    }
  }else{
    playSound('wrong');
    inp.style.borderColor='var(--red)';inp.style.background='rgba(255,77,109,.06)';
    const remaining=grp.filter(w=>_grpRemain.includes(w.id));
    inp.value='✗  '+remaining.map(w=>w.word).join(' / ');
    const missedAnswers=remaining.map(w=>w.word).join(', ');
    toast('To\'g\'ri: "'+missedAnswers+'"','warn','1-bosqichga qaytdi ↩');
    try{await Promise.all(grp.map(w=>api('POST','/words/'+w.id+'/review',{correct:false})));}catch{}
    setTimeout(()=>{inp.style.borderColor='';inp.style.background='';if(btn)btn.disabled=false;testGrpIdx++;_grpRemain=[];_grpFound=[];renderQ();},1600);
  }
}

function endTest(){
  E('test-a').style.display='none';
  document.querySelectorAll('#test-btns .btn').forEach(b=>b.style.display='');
  toast('Test yakunlandi!','ok','Barakalla! 🎉');
  loadBoxes();
}

function getAchIcon(aid) {
  const icons = {
    'newbie': ap('🚀'),
    'lexicon_100': ap('📚'),
    'streak_7': ap('🔥'),
    'master_10': ap('🎓'),
    'night_owl': ap('🦉'),
    'social_star': ap('🌟'),
    'early_bird': ap('🌅')
  };
  return icons[aid] || ap('🏆');
}


/* ── Profile ─────────────────────────────────────── */
async function loadProfile(){

  try{
    const me=await api('GET','/stats/me');
    E('pf-total').textContent=me.total_xp+' XP';
    E('pf-streak-n').textContent=me.streak;
    E('pf-name').textContent=me.full_name || me.email.split('@')[0];
    E('pf-email').textContent=me.email;
    const level = Math.floor(Math.sqrt((me.total_xp||0)/100)) + 1;
    const rank = getRankTitle(level);
    E('pf-level-badge').textContent = `Level ${level}: ${rank}`;

    
    const initials=me.email.slice(0,2).toUpperCase();
    const pfAvContent = E('pf-av-content');
    if(pfAvContent) pfAvContent.innerHTML = getAvHtml(me.avatar_url, initials);

    const ds=await api('GET','/words/stats');
    E('pf-mastered').textContent=(ds.boxes?.[5]||0)+' ta';
    
    // Load Achievements
    const achs = await api('GET', '/stats/achievements');
    E('ach-grid').innerHTML = achs.map(a => `
      <div class="ach-card ${a.unlocked ? 'unlocked' : ''} tier-${a.level || 0}">
        <div class="ach-level-badge">LVL ${a.level || 0}</div>
        <div class="ach-icon-wrap">
          <div class="ach-icon">${ap(a.icon || '🏆')}</div>
        </div>
        <div class="ach-title">${a.title || 'Sovrin'}</div>
        <div class="ach-progress-wrap">
          <div class="ach-progress-bar">
            <div class="ach-progress-fill" style="width: ${a.progress_pct || 0}%"></div>
          </div>
          <div class="ach-progress-text">
            ${a.is_max ? 'Maksimal daraja' : `${a.current_val || 0} / ${a.target_val || 10} ${a.unit || ''}`}
          </div>
        </div>
      </div>
    `).join('');


  }catch(e){toast(e.message,'err');}
}

let _cropper = null;
let _cropFile = null;

async function uploadAvatar(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  if (!file.type.startsWith('image/')) { toast('Faqat rasm yuklash mumkin','err'); return; }
  
  _cropFile = file;
  const reader = new FileReader();
  reader.onload = e => {
    const img = E('crop-img');
    img.src = e.target.result;
    E('crop-modal').classList.add('open');
    if (_cropper) _cropper.destroy();
    _cropper = new Cropper(img, {
      aspectRatio: 1,
      viewMode: 1,
      autoCropArea: 1,
      responsive: true
    });
  };
  reader.readAsDataURL(file);
  input.value = ''; // Reset input
}

function closeCrop() {
  E('crop-modal').classList.remove('open');
  if (_cropper) { _cropper.destroy(); _cropper = null; }
}

async function applyCrop() {
  if (!_cropper) return;
  const canvas = _cropper.getCroppedCanvas({ width: 400, height: 400 });
  const btn = document.querySelector('#crop-modal .btn-blue');
  spinBtn(btn, true);
  
  canvas.toBlob(async blob => {
    const formData = new FormData();
    formData.append('file', blob, 'avatar.jpg');
    
    try {
      const res = await fetch('/api/stats/avatar', {
        method: 'POST',
        headers: { 'Authorization': 'Bearer ' + TOKEN },
        body: formData
      });
      if (!res.ok) throw new Error('Yuklashda xatolik');
      const data = await res.json();
      ME.avatar_url = data.avatar_url;
      localStorage.setItem('bb_me', JSON.stringify(ME));
      enterApp();
      toast('Rasm muvaffaqiyatli yuklandi', 'ok');
      closeCrop();
    } catch (e) {
      toast(e.message, 'err');
    } finally {
      spinBtn(btn, false);
    }
  }, 'image/jpeg', 0.9);
}




/* ── Add words ──────────────────────────────────── */

function addTab(t){
  document.querySelectorAll('.add-tab').forEach((b,i)=> {
    b.classList.remove('on');
    if (i===0 && t==='bulk') b.classList.add('on');
    if (i===1 && t==='single') b.classList.add('on');
    if (i===2 && t==='decks') b.classList.add('on');
  });
  E('bulk-a').style.display=t==='bulk'?'':'none';
  E('single-a').style.display=t==='single'?'':'none';
  if (E('decks-a')) {
    E('decks-a').style.display=t==='decks'?'':'none';
    if(t==='decks') loadDecks();
  }
}

function parseLine(l){
  l=l.trim();if(!l)return null;
  if(l.includes(' - ')){const[a,...b]=l.split(' - ');return{word:a.trim(),translation:b.join(' - ').trim()};}
  if(l.includes('-')){const i=l.indexOf('-');return{word:l.slice(0,i).trim(),translation:l.slice(i+1).trim()};}
  return null;
}

E('bulk-inp')&&E('bulk-inp').addEventListener('input',function(){
  const cnt=this.value.split('\n').map(parseLine).filter(p=>p&&p.word&&p.translation).length;
  E('bulk-cnt').textContent=cnt+' ta juft';
});

async function doBulk(){
  const raw=E('bulk-inp').value.trim();
  if(!raw){toast("Maydon bo'sh",'warn');return;}
  const pairs=raw.split('\n').map(parseLine).filter(p=>p&&p.word&&p.translation);
  if(!pairs.length){toast('Format xato','err');return;}
  const btn=E('bulk-btn');spinBtn(btn,true);
  try{
    const d=await api('POST','/words/bulk',{words:pairs});
    const xpEarned = d.added * 5;
    const r=E('bulk-res');r.className='res ok';
    r.innerHTML=`
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div class="res-t">✅ ${d.added} ta qo'shildi</div>
        ${xpEarned > 0 ? `<div style="background:var(--p);color:#fff;padding:4px 10px;border-radius:8px;font-size:12px;font-weight:800;box-shadow:0 4px 12px rgba(124,92,252,0.3)">+${xpEarned} XP</div>` : ''}
      </div>
      ${d.skipped?'<div style="font-size:12px;margin-top:3px;color:var(--tx3)">'+d.skipped+' ta allaqachon mavjud</div>':''}`;
    if(d.added>0) {
      E('bulk-inp').value='';
      loadMyStats(); // Refresh sidebar/stats to show new XP
    }
    E('bulk-cnt').textContent='0 ta juft';
  }catch(e){
    if (e.status === 403) {
      showPremiumLock("So'z qo'shish");
    } else {
      const r=E('bulk-res');r.className='res err';r.innerHTML='<div class="res-t">❌ '+e.message+'</div>';
    }
  }
  finally{spinBtn(btn,false);}
}

async function doSingle(){
  const en=E('s-en').value.trim(),uz=E('s-uz').value.trim();
  if(!en||!uz){toast("Maydonlarni to'ldiring",'warn');return;}
  const btn=E('single-btn');spinBtn(btn,true);
  try{
    await api('POST','/words',{word:en,translation:uz});
    const r=E('single-res');r.className='res ok';
    r.innerHTML=`
      <div style="display:flex;align-items:center;justify-content:space-between">
        <div class="res-t">✅ Qo'shildi!</div>
        <div style="background:var(--p);color:#fff;padding:4px 10px;border-radius:8px;font-size:12px;font-weight:800;box-shadow:0 4px 12px rgba(124,92,252,0.3)">+5 XP</div>
      </div>
    `;
    E('s-en').value='';E('s-uz').value='';
    loadMyStats(); // Refresh sidebar/stats
    setTimeout(()=>{if(r)r.className='res';},3500);
  }catch(e){
    if (e.status === 403) {
      showPremiumLock("So'z qo'shish");
    } else {
      const r=E('single-res');r.className='res err';r.innerHTML='<div class="res-t">❌ '+e.message+'</div>';
    }
  }
  finally{spinBtn(btn,false);}
}

/* ── Edit / Delete words ─────────────────────────── */
function editWord(id,word,trans){
  E('m-title').textContent="So'zni tahrirlash";
  E('m-body').innerHTML=`
    <div class="fld"><label class="lbl">Inglizcha</label><input class="inp" id="ew-en" value="${word}"/></div>
    <div class="fld" style="margin-top:10px"><label class="lbl">O'zbekcha</label><input class="inp" id="ew-uz" value="${trans}"/></div>`;
  E('m-acts').innerHTML=`
    <button class="btn btn-ghost" onclick="closeModal()">Bekor</button>
    <button class="btn btn-blue" onclick="saveWord(${id})">Saqlash</button>`;
  E('modal').classList.add('open');
}
async function saveWord(id){
  const en=E('ew-en').value.trim(),uz=E('ew-uz').value.trim();
  if(!en||!uz){toast("Maydonlarni to'ldiring",'warn');return;}
  try{await api('PUT','/words/'+id,{word:en,translation:uz});closeModal();loadWords();toast('Saqlandi','ok');}
  catch(e){toast(e.message,'err');}
}
function delWord(id, word) {
  confirmDialog("So'zni o'chirish", `Haqiqatan ham <strong style="color:var(--tx)">"${word}"</strong> so'zini o'chirmoqchimisiz? Bu amalni ortga qaytarib bo'lmaydi.`, async () => {
    try {
      await api('DELETE', '/words/' + id);
      toast('So\'z o\'chirildi', 'ok');
      loadWords();
    } catch(e) { toast(e.message, 'err'); }
  });
}
function closeModal(){
  document.querySelectorAll('.modal-bg.open').forEach(m => m.classList.remove('open'));
  E('modal').classList.remove('open');
}
E('modal').addEventListener('click',e=>{if(e.target===E('modal'))closeModal();});

/* ── Change Password ─────────────────────────────── */
function openChangePassword(){
  E('m-title').textContent="Parolni o'zgartirish";
  E('m-body').innerHTML=`
    <div class="fld"><label class="lbl">Joriy parol</label>
      <div class="pass-grp"><input class="inp with-toggle" type="password" id="cp-cur" placeholder="Joriy parolingiz"/><div class="pass-toggle" onclick="togglePass('cp-cur',this)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></div></div>
    </div>
    <div class="fld" style="margin-top:12px"><label class="lbl">Yangi parol (Kamida 8 belgi)</label>
      <div class="pass-grp"><input class="inp with-toggle" type="password" id="cp-new" placeholder="••••••••"/><div class="pass-toggle" onclick="togglePass('cp-new',this)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></div></div>
    </div>
    <div class="fld" style="margin-top:12px"><label class="lbl">Yangi parolni tasdiqlang</label>
      <div class="pass-grp"><input class="inp with-toggle" type="password" id="cp-con" placeholder="••••••••"/><div class="pass-toggle" onclick="togglePass('cp-con',this)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></div></div>
    </div>
    <div id="cp-err" style="color:var(--red);font-size:12px;margin-top:8px;font-weight:600;min-height:16px"></div>`;
  E('m-acts').innerHTML=`
    <button class="btn btn-ghost" onclick="closeModal()">Bekor</button>
    <button class="btn btn-blue" id="cp-btn" onclick="doChangePassword()">Saqlash</button>`;
  E('modal').classList.add('open');
  setTimeout(()=>E('cp-cur')&&E('cp-cur').focus(),100);
}

function openForcePasswordUpdate(){
  E('m-title').textContent="Xavfsizlik bo'yicha yangilanish";
  E('m-body').innerHTML=`
    <div style="font-size:13px;color:var(--tx2);margin-bottom:16px">Tizim xavfsizligini ta'minlash maqsadida, parolingiz kamida 8 ta belgidan iborat bo'lishi talab etiladi. Iltimos, yangi parol o'rnating.</div>
    <div class="fld"><label class="lbl">Hozirgi parol</label>
      <div class="pass-grp"><input class="inp with-toggle" type="password" id="fp-cur" placeholder="••••••"/><div class="pass-toggle" onclick="togglePass('fp-cur',this)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></div></div>
    </div>
    <div class="fld" style="margin-top:12px"><label class="lbl">Yangi parol (Kamida 8 belgi)</label>
      <div class="pass-grp"><input class="inp with-toggle" type="password" id="fp-new" placeholder="••••••••"/><div class="pass-toggle" onclick="togglePass('fp-new',this)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></div></div>
    </div>
    <div class="fld" style="margin-top:12px"><label class="lbl">Parolni tasdiqlang</label>
      <div class="pass-grp"><input class="inp with-toggle" type="password" id="fp-con" placeholder="••••••••"/><div class="pass-toggle" onclick="togglePass('fp-con',this)"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg></div></div>
    </div>
    <div id="fp-err" style="color:var(--red);font-size:12px;margin-top:8px;font-weight:600;min-height:16px"></div>`;
  E('m-acts').innerHTML=`
    <button class="btn btn-blue" id="fp-btn" style="width:100%" onclick="doForcePasswordUpdate()">Parolni yangilash va boshlash</button>`;
  E('modal').classList.add('open');
  // Disable closing modal
  E('modal').onclick=null;
}

async function doForcePasswordUpdate(){
  const cur=E('fp-cur').value,nw=E('fp-new').value,con=E('fp-con').value;
  const errEl=E('fp-err');errEl.textContent='';
  if(!cur||!nw||!con){errEl.textContent="Barcha maydonlarni to'ldiring.";return;}
  if(nw.length<8){errEl.textContent='Yangi parol kamida 8 ta belgi bo\'lsin.';return;}
  if(nw===cur){errEl.textContent='Yangi parol hozirgi parol bilan bir xil bo\'lmasin.';return;}
  if(nw!==con){errEl.textContent='Parollar mos kelmadi.';return;}
  const btn=E('fp-btn');spinBtn(btn,true);
  try{
    await api('POST','/auth/change-password',{current_password:cur,new_password:nw});
    closeModal();
    // Re-bind modal click for closing
    E('modal').onclick=e=>{if(e.target===E('modal'))closeModal();};
    toast("Parol muvaffaqiyatli yangilandi!",'ok');
    enterApp();
  }catch(e){errEl.textContent=e.message;}finally{spinBtn(btn,false);}
}

async function doChangePassword(){
  const cur=E('cp-cur').value,nw=E('cp-new').value,con=E('cp-con').value;
  const errEl=E('cp-err');errEl.textContent='';
  if(!cur||!nw||!con){errEl.textContent="Barcha maydonlarni to'ldiring.";return;}
  if(nw.length<8){errEl.textContent='Yangi parol kamida 8 ta belgi bo\'lsin.';return;}
  if(nw===cur){errEl.textContent='Yangi parol joriy parol bilan bir xil bo\'lmasin.';return;}
  if(nw!==con){errEl.textContent='Yangi parollar bir-biriga mos emas.';return;}
  const btn=E('cp-btn');spinBtn(btn,true);
  try{
    const res=await api('POST','/auth/change-password',{current_password:cur,new_password:nw});
    closeModal();toast(res.message||"Parol muvaffaqiyatli o'zgartirildi",'ok');
  }catch(e){errEl.textContent=e.message;}finally{spinBtn(btn,false);}
}

function togglePass(id,btn){
  const inp=E(id);
  if(!inp)return;
  const isPass=inp.type==='password';
  inp.type=isPass?'text':'password';
  btn.innerHTML=isPass?`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`:`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
}

/* ── Utils ───────────────────────────────────────── */

window.addEventListener('keydown',e=>{
  if(e.key==='Enter'&&testMode==='write'&&E('test-a').style.display!=='none'){e.preventDefault();checkWrite();}
});

/* ── Init ─────────────────────────────────────────── */
(function(){
  const p=new URLSearchParams(location.search);
  const resetTok=p.get('reset_token');
  if(resetTok){
    E('landing').classList.add('hidden');
    E('auth').classList.add('on');
    openResetPanel(resetTok);
    return;
  }
  const googleOk=_handleGoogleCallback();
  if(googleOk){enterApp();return;}
  if(TOKEN&&ME){enterApp();return;}
  /* Show landing by default */
  E('landing').classList.remove('hidden');
})();

/* ── Stats / Leaderboard ────────────────────────── */
async function loadLeaderboard(period){
  // Update tabs
  document.querySelectorAll('.stats-tab').forEach(b=>b.classList.toggle('on', b.id==='st-'+period.slice(0,3)));
  
  const topEl = E('leader-top');
  const listEl = E('leader-list');
  topEl.innerHTML = '<div class="spin-big"></div>';
  listEl.innerHTML = '';

  try {
    const data = await api('GET', '/stats/leaderboard?period=' + period);
    const me = await api('GET', '/stats/me');
    
    const top3 = data.slice(0, 3);
    const others = data.slice(3);
    
    // Sort top 3 for UI (2nd, 1st, 3rd)
    const sortedTop = [];
    if(top3[1]) sortedTop.push(top3[1]); // #2
    if(top3[0]) sortedTop.push(top3[0]); // #1
    if(top3[2]) sortedTop.push(top3[2]); // #3
    
    topEl.innerHTML = sortedTop.map(u => `
      <div class="leader-card rank-${u.rank} ${u.id === me.id ? 'me' : ''}">
        <div class="rank-badge">${u.rank}</div>
        <div class="leader-av">${getAvHtml(u.avatar_url, (u.full_name || u.email)[0].toUpperCase())}</div>
        <div class="leader-name">${esc(u.full_name || u.email.split('@')[0])}</div>
        <div class="leader-xp">${u.xp} XP</div>
      </div>
    `).join('');
    
    listEl.innerHTML = others.map(u => `
      <div class="leader-item ${u.id === me.id ? 'me' : ''}">
        <div class="li-rank">${u.rank}</div>
        <div class="li-av">${getAvHtml(u.avatar_url, (u.full_name || u.email)[0].toUpperCase())}</div>
        <div class="li-info">
          <div class="li-name">${esc(u.full_name || u.email.split('@')[0])}</div>
          <div class="li-streak">${ap('🔥')} ${u.streak} kun streak</div>

        </div>
        <div class="li-xp">${u.xp} <span>XP</span></div>
      </div>
    `).join('');
    
    if (others.length === 0 && top3.length === 0) {
      listEl.innerHTML = '<div class="empty">Hali hech kim yo\'q</div>';
    }
  } catch (e) {
    topEl.innerHTML = `<div class="err">${e.message}</div>`;
  }
}

window.addEventListener('click', (e) => {
  const sb = document.getElementById('ai-sb');
  const btn = document.getElementById('ai-mob-btn');
  if (sb && sb.classList.contains('mob-open')) {
    if (!sb.contains(e.target) && (!btn || !btn.contains(e.target))) {
      sb.classList.remove('mob-open');
    }
  }
});



function getRankTitle(level) {
  if (level <= 5) return "Student";
  if (level <= 15) return "Scholar";
  if (level <= 30) return "Master";
  if (level <= 50) return "Professor";
  return "Genius";
}
async function loadMyStats() {
  try {
    const me = await api('GET', '/stats/me');
    ME = me;
    localStorage.setItem('bb_me', JSON.stringify(me));
    updateAdminUI();
    
    // Update Sidebar
    const xp = me.total_xp || 0;
    const level = Math.floor(Math.sqrt(xp/100)) + 1;
    const rank = getRankTitle(level);
    
    const sbRole = document.querySelector('.u-role'); 
    if(sbRole) sbRole.textContent = `Lvl ${level} Student`;
    
    const lvlEl = E('pf-level-badge');
    if(lvlEl) lvlEl.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.46 21z"/></svg> Level: ${level} ${rank}`;
    
    // If we are on dash or profile, reload them
    const curPage = document.querySelector('.page.on')?.id;
    if(curPage === 'p-dash') loadDash();
    if(curPage === 'p-profile') loadProfile();
    
    // Also update sidebar name if exists
    const sbName = document.querySelector('.u-name');
    if(sbName) sbName.textContent = me.full_name || me.email.split('@')[0];
  } catch(e) { console.error("Failed to load stats", e); }
}

function openEditName() {
  E('en-name').value = ME?.full_name || '';
  E('modal-name').classList.add('open');
  E('en-err').textContent = '';
}
async function doUpdateName() {
  const name = E('en-name').value.trim();
  if(!name) { E('en-err').textContent = "Ism bo'sh bo'lmasligi kerak."; return; }
  const btn = E('en-btn'); spinBtn(btn, true);
  try {
    const res = await api('POST', '/stats/me/name', { full_name: name });
    ME.full_name = res.full_name;
    localStorage.setItem('bb_me', JSON.stringify(ME));
    toast("Ism yangilandi!", "ok");
    E('modal-name').classList.remove('open');
    loadMyStats();
  } catch(e) { E('en-err').textContent = e.message; }
  finally { spinBtn(btn, false); }
}

function openEditGoals() {
  E('eg-reviews').value = ME?.goal_reviews || 10;
  E('eg-xp').value = ME?.goal_xp || 50;
  E('modal-goals').classList.add('open');
  E('eg-err').textContent = '';
}

async function doUpdateGoals() {
  const gr = parseInt(E('eg-reviews').value);
  const gx = parseInt(E('eg-xp').value);
  if (isNaN(gr) || isNaN(gx)) { E('eg-err').textContent = "Barcha maydonlarni to'ldiring"; return; }
  const btn = E('eg-btn'); spinBtn(btn, true);
  try {
    await api('POST', '/stats/me/goals', { goal_reviews: gr, goal_xp: gx });
    toast("Maqsadlar yangilandi!", "ok");
    E('modal-goals').classList.remove('open');
    loadMyStats();
  } catch(e) { E('eg-err').textContent = e.message; }
  finally { spinBtn(btn, false); }
}

/* ══════════════════════════════════════════════════════
   PRE-MADE DECKS
═══════════════════════════════════════════════════════ */
function loadDecks() {
  const container = E('decks-list');
  container.innerHTML = '<div style="text-align:center;padding:20px"><div class="spin" style="margin:0 auto"></div></div>';
  api('GET', '/decks/')
    .then(data => {
      container.innerHTML = '';
      if(!data || data.length === 0) {
        container.innerHTML = '<div style="color:var(--tx3);text-align:center">Hozircha to\'plamlar yo\'q.</div>';
        return;
      }
      data.forEach(d => {
        const icon = d.icon || '📚';
        const item = document.createElement('div');
        item.style.cssText = 'background:var(--bg2);border:1px solid var(--bd2);border-radius:12px;padding:16px;display:flex;justify-content:space-between;align-items:center';
        item.innerHTML = `
          <div style="display:flex;align-items:center;gap:16px">
            <div style="font-size:24px;width:40px;height:40px;display:flex;align-items:center;justify-content:center;background:var(--bg);border-radius:8px">${icon}</div>
            <div>
              <div style="font-weight:700;color:var(--tx);font-size:15px">${d.title}</div>
              <div style="font-size:12px;color:var(--tx3);margin-top:4px">${d.description || ''}</div>
              <div style="font-size:11px;color:var(--p);margin-top:6px;font-weight:600">${d.word_count} ta so'z</div>
            </div>
          </div>
          <button class="btn btn-blue" onclick="addDeck(${d.id})"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg> Qo'shish</button>
        `;
        container.appendChild(item);
      });
    })
    .catch(err => {
      container.innerHTML = '<div style="color:#ff4d6d;text-align:center">Xatolik yuz berdi.</div>';
      console.error(err);
    });
}

function addDeck(deckId) {
  loading(1);
  api('POST', `/decks/${deckId}/add`)
    .then(res => {
      loading(0);
      toast(`${res.added} ta yangi so'z lug'atingizga qo'shildi.`, 'ok', "Qo'shildi");
      loadWords();
    })
    .catch(err => {
      loading(0);
      toast(err.message || 'Xatolik yuz berdi', 'err');
    });
}

/* ══════════════════════════════════════════════════════
   AI CHAT (BrainBot)
═══════════════════════════════════════════════════════ */
let _chatSessionId = null;

async function loadChatSessions() {
  try {
    const sessions = await api('GET', '/ai/chats');
    const list = E('chat-session-list');
    if (!list) return;
    if (!sessions || sessions.length === 0) {
      list.innerHTML = '<div style="text-align:center;padding:16px;color:var(--tx3);font-size:13px">Hali suhbat yo\'q</div>';
      return;
    }
    list.innerHTML = sessions.map(s => `
      <div class="chat-session-item ${s.id === _chatSessionId ? 'active' : ''}" onclick="openChatSession(${s.id})">
        <div class="chat-session-name">${esc(s.name)}</div>
        <div class="chat-session-date">${new Date(s.updated_at || s.created_at).toLocaleDateString('uz-UZ')}</div>
        <button class="chat-session-del" onclick="event.stopPropagation();delChatSession(${s.id})" title="O'chirish">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
        </button>
      </div>
    `).join('');
  } catch(e) { console.error('loadChatSessions', e); }
}

async function newChatSession() {
  try {
    const s = await api('POST', '/ai/chats');
    _chatSessionId = s.id;
    loadChatSessions();
    renderChatMessages([]);
  } catch(e) { toast(e.message, 'err'); }
}

async function openChatSession(id) {
  _chatSessionId = id;
  try {
    const s = await api('GET', '/ai/chats/' + id);
    renderChatMessages(s.messages || []);
    loadChatSessions();
  } catch(e) { toast(e.message, 'err'); }
}

function renderChatMessages(msgs) {
  const el = E('chat-messages');
  if (!el) return;
  if (!msgs || msgs.length === 0) {
    el.innerHTML = `
      <div class="chat-welcome">
        <div style="font-size:48px;margin-bottom:16px">${ap('🤖')}</div>
        <div style="font-size:20px;font-weight:800;color:var(--tx);margin-bottom:8px">Salom! Men BrainBot</div>
        <div style="font-size:14px;color:var(--tx3);line-height:1.6;max-width:400px">Ingliz tilini o'rganishda sizga yordam beraman. Grammatika, so'z ishlatish, gap tuzish — istalgan savolingizni bering!</div>
        <div class="chat-suggestions" style="margin-top:20px;display:flex;flex-wrap:wrap;gap:8px;justify-content:center">
          <button class="chat-suggest-btn" onclick="sendChatFromSuggest('Hello va Hi ning farqi nimada?')">Hello va Hi farqi</button>
          <button class="chat-suggest-btn" onclick="sendChatFromSuggest('Present Perfect tense qachon ishlatiladi?')">Present Perfect</button>
          <button class="chat-suggest-btn" onclick="sendChatFromSuggest('accomplish so\'zini gap ichida ishlating')">So'z bilan gap</button>
        </div>
      </div>`;
    return;
  }
  el.innerHTML = msgs.map(m => `
    <div class="chat-msg ${m.role}">
      <div class="chat-msg-av">${m.role === 'user' ? ap('👤') : ap('🤖')}</div>
      <div class="chat-msg-bubble">${formatAIResponse(m.content)}</div>
    </div>
  `).join('');
  el.scrollTop = el.scrollHeight;
}

function formatAIResponse(text) {
  // Convert markdown-style formatting to HTML
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`(.*?)`/g, '<code style="background:rgba(124,92,252,.1);padding:2px 6px;border-radius:4px;font-family:monospace;font-size:13px">$1</code>')
    .replace(/\n/g, '<br>');
}

async function sendChatFromSuggest(text) {
  E('chat-input').value = text;
  await sendChat();
}

async function sendChat() {
  const inp = E('chat-input');
  const msg = inp.value.trim();
  if (!msg) return;

  // Create session if none
  if (!_chatSessionId) {
    try {
      const s = await api('POST', '/ai/chats');
      _chatSessionId = s.id;
    } catch(e) { toast(e.message, 'err'); return; }
  }

  inp.value = '';
  const btn = E('chat-send-btn');
  btn.disabled = true;
  inp.disabled = true;

  // Show user message immediately
  const msgEl = E('chat-messages');
  const welcome = msgEl.querySelector('.chat-welcome');
  if (welcome) welcome.remove();
  
  msgEl.innerHTML += `<div class="chat-msg user"><div class="chat-msg-av">${ap('👤')}</div><div class="chat-msg-bubble">${esc(msg)}</div></div>`;
  msgEl.innerHTML += `<div class="chat-msg assistant" id="chat-typing"><div class="chat-msg-av">${ap('🤖')}</div><div class="chat-msg-bubble"><span class="typing-dots"><span></span><span></span><span></span></span></div></div>`;
  msgEl.scrollTop = msgEl.scrollHeight;

  try {
    const res = await api('POST', `/ai/chats/${_chatSessionId}/messages`, { content: msg });
    const typingEl = E('chat-typing');
    if (typingEl) typingEl.remove();
    msgEl.innerHTML += `<div class="chat-msg assistant"><div class="chat-msg-av">${ap('🤖')}</div><div class="chat-msg-bubble">${formatAIResponse(res.content || res.reply || 'Javob olinmadi')}</div></div>`;
    msgEl.scrollTop = msgEl.scrollHeight;
    loadChatSessions(); // Update sidebar
  } catch(e) {
    const typingEl = E('chat-typing');
    if (typingEl) typingEl.remove();
    msgEl.innerHTML += `<div class="chat-msg assistant"><div class="chat-msg-av">${ap('🤖')}</div><div class="chat-msg-bubble" style="color:#ff4d6d">Xatolik: ${esc(e.message)}</div></div>`;
    msgEl.scrollTop = msgEl.scrollHeight;
  } finally {
    btn.disabled = false;
    inp.disabled = false;
    inp.focus();
  }
}

async function delChatSession(id) {
  try {
    await api('DELETE', '/ai/chats/' + id);
    if (_chatSessionId === id) {
      _chatSessionId = null;
      renderChatMessages([]);
    }
    loadChatSessions();
  } catch(e) { toast(e.message, 'err'); }
}

/* ══════════════════════════════════════════════════════
   SENTENCE BUILDER
═══════════════════════════════════════════════════════ */
let _sentWord = null;

async function loadSentenceStats() {
  try {
    const d = await api('GET', '/sentences/stats');
    if (E('ss-due')) E('ss-due').textContent = d.due || 0;
    if (E('ss-done')) E('ss-done').textContent = d.done_today || 0;
    if (E('ss-total')) E('ss-total').textContent = d.total || 0;
  } catch(e) { console.error('loadSentenceStats', e); }
}

async function loadSentenceTask() {
  try {
    const d = await api('GET', '/sentences/next');
    if (!d || !d.word) {
      E('sent-empty').style.display = '';
      E('sent-card').style.display = 'none';
      toast("Hozircha gap tuzish uchun so'z yo'q. Avval so'z qo'shing!", 'warn');
      return;
    }
    _sentWord = d;
    E('sent-empty').style.display = 'none';
    E('sent-card').style.display = '';
    E('sent-word').textContent = d.word.word;
    E('sent-trans').textContent = d.word.translation;
    E('sent-box-badge').textContent = BOX_LABELS[d.word.box || 0];
    E('sent-box-badge').style.background = BOX_BG[d.word.box || 0];
    E('sent-box-badge').style.color = BOX_COLORS[d.word.box || 0];
    E('sent-input').value = '';
    E('sent-feedback').style.display = 'none';
    E('sent-check-btn').disabled = false;
    setTimeout(() => E('sent-input').focus(), 100);
  } catch(e) {
    toast(e.message, 'err');
  }
}

async function checkSentence() {
  const text = E('sent-input').value.trim();
  if (!text) { toast('Gap yozing!', 'warn'); return; }
  if (!_sentWord) return;
  
  const btn = E('sent-check-btn');
  spinBtn(btn, true);
  
  try {
    const res = await api('POST', '/sentences/check', {
      word_id: _sentWord.word.id,
      sentence: text,
      sentence_number: (_sentWord.sentences_done || 0) + 1
    });
    const fb = E('sent-feedback');
    fb.style.display = '';
    
    if (res.is_correct) {
      fb.className = 'sent-fb sent-fb-ok';
      fb.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
          ${ap('✅')} <strong style="color:#00e5a0">Ajoyib! Gap to'g'ri!</strong>
        </div>
        ${res.feedback ? '<div style="font-size:13px;color:var(--tx2);line-height:1.6">' + formatAIResponse(res.feedback) + '</div>' : ''}
        ${res.xp_earned ? '<div style="margin-top:10px;background:var(--p);color:#fff;display:inline-block;padding:4px 12px;border-radius:8px;font-size:12px;font-weight:800">+' + res.xp_earned + ' XP</div>' : ''}
      `;
    } else {
      fb.className = 'sent-fb sent-fb-warn';
      fb.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
          ${ap('💡')} <strong style="color:#ffb84d">Yaxshilash mumkin</strong>
        </div>
        <div style="font-size:13px;color:var(--tx2);line-height:1.6">${formatAIResponse(res.feedback || 'Qayta urinib ko\'ring')}</div>
        ${res.corrected ? '<div style="margin-top:10px;padding:10px;background:rgba(0,229,160,.06);border:1px solid rgba(0,229,160,.2);border-radius:8px;font-size:13px;color:#00e5a0"><strong>To\'g\'ri variant:</strong> ' + esc(res.corrected) + '</div>' : ''}
      `;
    }
    loadSentenceStats();
  } catch(e) {
    toast(e.message, 'err');
  } finally {
    spinBtn(btn, false);
  }
}

function skipSentence() {
  loadSentenceTask();
}

/* ══════════════════════════════════════════════════════
   SUPER MEMORY (Mnemonika)
═══════════════════════════════════════════════════════ */
async function loadMnemonic() {
  E('sm-intro').style.display = 'none';
  E('sm-card').style.display = '';
  E('sm-content').innerHTML = '<div style="text-align:center;padding:20px"><div class="spin" style="margin:0 auto"></div><div style="margin-top:12px;color:var(--tx3);font-size:13px">AI mnemonika yaratmoqda...</div></div>';
  
  try {
    const res = await api('POST', '/super-memory/generate-chunk', {});
    if (!res || !res.word) {
      E('sm-content').innerHTML = '<div style="text-align:center;padding:20px;color:var(--tx3)">Hozircha so\'z yo\'q. Avval so\'z qo\'shing!</div>';
      return;
    }
    E('sm-word').textContent = res.word;
    E('sm-trans').textContent = res.translation;
    const box = res.box || 0;
    E('sm-box-badge').textContent = BOX_LABELS[box];
    E('sm-box-badge').style.background = BOX_BG[box];
    E('sm-box-badge').style.color = BOX_COLORS[box];
    
    const mn = res.mnemonic || res;
    let html = '';
    if (mn.keyword) {
      html += `<div class="sm-section"><div class="sm-section-title">${ap('🔑')} Kalit so'z</div><div class="sm-section-body">${esc(mn.keyword)}</div></div>`;
    }
    if (mn.story) {
      html += `<div class="sm-section"><div class="sm-section-title">${ap('📖')} Hikoya</div><div class="sm-section-body">${formatAIResponse(mn.story)}</div></div>`;
    }
    if (mn.visual) {
      html += `<div class="sm-section"><div class="sm-section-title">${ap('🎨')} Tasavvur qiling</div><div class="sm-section-body">${formatAIResponse(mn.visual)}</div></div>`;
    }
    if (mn.examples && mn.examples.length) {
      html += `<div class="sm-section"><div class="sm-section-title">${ap('📝')} Misollar</div>`;
      mn.examples.forEach(ex => {
        html += `<div class="sm-example">${formatAIResponse(ex)}</div>`;
      });
      html += '</div>';
    }
    if (!html && mn.content) {
      html = `<div class="sm-section"><div class="sm-section-body">${formatAIResponse(mn.content)}</div></div>`;
    }
    if (!html) {
      html = `<div class="sm-section"><div class="sm-section-body">${formatAIResponse(JSON.stringify(mn))}</div></div>`;
    }
    E('sm-content').innerHTML = html;
  } catch(e) {
    E('sm-content').innerHTML = `<div style="text-align:center;padding:20px;color:#ff4d6d">${esc(e.message)}</div>`;
  }
}
