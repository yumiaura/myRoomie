"use strict";

// 2D point-and-click client. Served from the same origin as the API.
const STAT_KEYS = ["hunger", "hygiene", "energy", "mood", "health", "loneliness", "affection"];
const POLL_MS = 5000;
const t = (key) => window.I18n.t(key);

let catalog = {};
let state = {};
let currentScene = "apartment";
let openPanelBuilder = null;
let pollHandle = null;

const el = (id) => document.getElementById(id);
const token = () => localStorage.getItem("token") || "";
const setToken = (v) => { v ? localStorage.setItem("token", v) : localStorage.removeItem("token"); };
const petId = () => localStorage.getItem("pet_id") || "";
const setPetId = (v) => { v ? localStorage.setItem("pet_id", v) : localStorage.removeItem("pet_id"); };

async function api(path, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  if (token()) headers["Authorization"] = "Bearer " + token();
  let response;
  try {
    response = await fetch(path, { method, headers, body: body == null ? null : JSON.stringify(body) });
  } catch (err) {
    return { ok: false, status: 0, error: t("toast.offline") };
  }
  let data = null;
  const text = await response.text();
  if (text) { try { data = JSON.parse(text); } catch (err) { data = null; } }
  if (response.status === 401 && token()) onSessionExpired();
  if (response.ok) return { ok: true, status: response.status, data };
  return { ok: false, status: response.status, error: (data && data.detail) || ("error " + response.status) };
}

// --- Toast / screens -----------------------------------------------------
let toastTimer = null;
function toast(message) {
  const node = el("toast");
  node.textContent = message;
  node.classList.remove("hidden");
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.add("hidden"), 2200);
}

function showScreen(name) {
  for (const id of ["auth", "creation", "room"]) el(id).classList.toggle("hidden", id !== name);
  el("top-logout").classList.toggle("hidden", name === "auth");
}

// --- i18n chrome ---------------------------------------------------------
function buildLangSwitch() {
  const box = el("lang-switch");
  box.innerHTML = "";
  for (const lang of window.I18n.LANGS) {
    const button = document.createElement("button");
    button.textContent = lang.toUpperCase();
    button.classList.toggle("active", lang === window.I18n.getLang());
    button.onclick = () => window.I18n.setLang(lang);
    box.appendChild(button);
  }
}

function applyChrome() {
  el("auth-subtitle").textContent = t("auth.subtitle");
  el("username").placeholder = t("auth.username");
  el("password").placeholder = t("auth.password");
  el("login-btn").textContent = t("btn.login");
  el("register-btn").textContent = t("btn.register");
  el("create-subtitle").textContent = t("create.subtitle");
  el("roomie-name").placeholder = t("create.name");
  el("reroll-btn").textContent = t("create.reroll");
  el("movein-btn").textContent = t("create.movein");
  if (!el("preview").dataset.set) el("preview").textContent = t("create.rolling");
  el("gender").options[0].textContent = t("gender.girl");
  el("gender").options[1].textContent = t("gender.boy");
  el("top-logout").textContent = t("btn.logout");
  el("panel-close").textContent = t("btn.close");
  buildLangSwitch();
}

function onLangChanged() {
  applyChrome();
  if (!el("room").classList.contains("hidden")) {
    setScene(currentScene);
    renderHud();
  }
  if (openPanelBuilder) openPanelBuilder();
}

// --- Auth ----------------------------------------------------------------
async function onRegister() {
  const res = await api("/auth/register", "POST", { username: el("username").value.trim(), password: el("password").value });
  el("auth-status").textContent = res.ok ? t("auth.created") : res.error;
}
async function onLogin() {
  const res = await api("/auth/login", "POST", { username: el("username").value.trim(), password: el("password").value });
  if (!res.ok) { el("auth-status").textContent = res.error; return; }
  setToken(res.data.token);
  await afterLogin();
}
async function afterLogin() {
  if (petId()) {
    const existing = await api("/pets/" + petId());
    if (existing.ok) { enterRoom(existing.data); return; }
    setPetId("");
  }
  showScreen("creation");
  reroll();
}
async function onLogout() {
  stopPolling();
  if (token()) await api("/auth/logout", "POST");
  setToken(""); setPetId(""); state = {};
  showScreen("auth");
}
function onSessionExpired() {
  stopPolling();
  setToken(""); state = {};
  showScreen("auth");
  el("auth-status").textContent = t("auth.expired");
}

// --- Creation ------------------------------------------------------------
let previewSeed = 0;
async function reroll() {
  const res = await api("/preview", "POST", {});
  if (!res.ok) { el("preview").textContent = res.error; return; }
  previewSeed = res.data.seed;
  const tr = res.data.traits;
  el("preview").dataset.set = "1";
  el("preview").textContent = `${tr.personality} · ${tr.love_language.replace(/_/g, " ")} · ${tr.hobby} · ${t(tr.favorite_food)}`;
}
async function onMoveIn() {
  const name = el("roomie-name").value.trim();
  if (!name) { el("create-status").textContent = t("create.needname"); return; }
  const payload = { name, gender: el("gender").value };
  if (previewSeed) payload.seed = previewSeed;
  const res = await api("/pets", "POST", payload);
  if (!res.ok) { el("create-status").textContent = res.error; return; }
  const visited = await api("/pets/" + res.data.id + "/visit", "POST");
  enterRoom(visited.ok ? visited.data : res.data);
}

// --- Room / scenes -------------------------------------------------------
function enterRoom(data) {
  setPetId(data.id);
  state = data;
  showScreen("room");
  setScene("apartment");
  renderHud();
  startPolling();
}

function setScene(name) {
  currentScene = name;
  const scene = window.SCENES[name];
  el("scene-bg").src = scene.bg;
  const layer = el("hotspots");
  layer.innerHTML = "";
  for (const spot of scene.hotspots) {
    const button = document.createElement("button");
    button.className = "hotspot";
    button.style.left = spot.x + "%";
    button.style.top = spot.y + "%";
    button.style.width = spot.w + "%";
    button.style.height = spot.h + "%";
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = t(spot.label);
    button.appendChild(chip);
    button.onclick = () => runAction(spot.action);
    layer.appendChild(button);
  }
  // Roomie avatar only stands in the apartment.
  const avatar = el("avatar");
  if (name === "apartment" && scene.avatar) {
    avatar.classList.remove("hidden");
    avatar.style.left = scene.avatar.x + "%";
    avatar.style.top = scene.avatar.y + "%";
    avatar.style.width = scene.avatar.w + "%";
    avatar.style.height = scene.avatar.h + "%";
    updateAvatar();
  } else {
    avatar.classList.add("hidden");
  }
}

function moodKey(s) {
  if (s.health < 30) return "sick";
  if (s.mood < 35) return "sad";
  if (s.mood > 70) return "happy";
  return "neutral";
}
function updateAvatar() {
  if (!state.stats) return;
  el("avatar-portrait").src = `/assets/${state.gender}_${moodKey(state.stats)}.png`;
  const outfit = el("avatar-outfit");
  if (state.outfit) {
    outfit.style.display = "block";
    outfit.onerror = () => { outfit.onerror = () => { outfit.style.display = "none"; }; outfit.src = `/assets/outfit_${state.outfit}.png`; };
    outfit.src = `/assets/outfit_${state.outfit}_${state.gender}.png`;
  } else {
    outfit.style.display = "none";
  }
}

function renderHud() {
  if (!state.stats) return;
  const w = state.wallet;
  const rent = `${t("hud.rent")} ${w.rent_amount}` + (w.rent_overdue ? " " + t("hud.overdue") : "");
  el("topbar-info").textContent =
    `${t("loc." + currentScene)}  ·  💰 ${w.money} ${t("hud.coins")}  ·  🏠 ${rent}  ·  ${t("rel." + state.relationship)}  ·  Lv ${state.level}` +
    (state.season ? "  ·  " + t("season." + state.season) : "");
  const hud = el("hud");
  hud.innerHTML = "";
  for (const key of STAT_KEYS) {
    const value = Math.round(state.stats[key]);
    const div = document.createElement("div");
    div.className = "stat";
    div.innerHTML = `<div class="label"><span>${t("stat." + key)}</span><span>${value}</span></div><div class="track"><div class="fill" style="width:${value}%"></div></div>`;
    hud.appendChild(div);
  }
}

// --- Actions / panels ----------------------------------------------------
function runAction(action) {
  if (action.kind === "goto") { setScene(action.to); renderHud(); return; }
  if (action.kind === "act") { doAction(action.path); return; }
  if (action.kind === "hint") { toast(t(action.key)); return; }
  if (action.kind === "notes") { openNotes(); return; }
  if (action.kind === "work") { openPicker("panel.work", "jobs", "/work", "job"); return; }
  if (action.kind === "panel") {
    if (action.source === "wardrobe") openWardrobe(action);
    else openPicker(action.title, action.category, action.path, action.field);
  }
}

async function doAction(path, body = null) {
  if (!petId()) return;
  const res = await api("/pets/" + petId() + path, "POST", body);
  if (res.ok) { state = res.data; updateAvatar(); renderHud(); if (openPanelBuilder) openPanelBuilder(); }
  else toast(res.error);
}

function costLabel(category, value) {
  if (category === "foods") return `−${value[1]}⛁`;
  if (category === "gifts") return `−${value[0]}⛁`;
  if (category === "shop") return `−${value.cost}⛁`;
  if (category === "activities") return `−${value[2]}⚡`;
  if (category === "chores") return `−${value[1]}⚡`;
  if (category === "jobs") return `+${value[0]}⛁`;
  return "";
}

function openPicker(titleKey, category, path, field) {
  openPanelBuilder = () => {
    const items = catalog[category] || {};
    const rows = Object.keys(items).map((key) => ({ key, sub: costLabel(category, items[key]) }));
    renderPanel(titleKey, rows, (key) => doAction(path, { [field]: key }));
  };
  openPanelBuilder();
}

function openWardrobe(action) {
  openPanelBuilder = () => {
    const rows = (state.wardrobe || []).map((key) => ({ key, sub: "" }));
    renderPanel(action.title, rows, (key) => doAction(action.path, { [action.field]: key }));
  };
  openPanelBuilder();
}

function renderPanel(titleKey, rows, onPick) {
  el("panel-title").textContent = t(titleKey);
  const body = el("panel-body");
  body.innerHTML = "";
  if (!rows.length) {
    const p = document.createElement("p");
    p.className = "muted";
    p.textContent = t("panel.empty");
    body.appendChild(p);
  }
  for (const row of rows) {
    const button = document.createElement("button");
    button.className = "pick";
    button.innerHTML = `<span>${t(row.key)}</span><span class="cost">${row.sub}</span>`;
    button.onclick = () => onPick(row.key);
    body.appendChild(button);
  }
  el("panel-overlay").classList.remove("hidden");
}

function openNotes() {
  openPanelBuilder = () => {
    el("panel-title").textContent = t("notes.title");
    const body = el("panel-body");
    body.innerHTML = "";
    const unread = (state.inbox || []).filter((e) => !e.seen).length;
    const markBtn = document.createElement("button");
    markBtn.textContent = t("notes.markread") + (unread ? ` (${unread} ${t("notes.new")})` : "");
    markBtn.onclick = async () => { const r = await api("/pets/" + petId() + "/inbox/seen", "POST"); if (r.ok) { state = r.data; openPanelBuilder(); renderHud(); } };
    body.appendChild(markBtn);
    appendFeed(body, state.inbox, true);
    const diaryTitle = document.createElement("h3");
    diaryTitle.textContent = t("diary.title");
    body.appendChild(diaryTitle);
    appendFeed(body, state.diary, false);
    el("panel-overlay").classList.remove("hidden");
  };
  openPanelBuilder();
}

function appendFeed(parent, items, markUnread) {
  const list = (items || []).slice(-8).reverse();
  for (const entry of list) {
    const div = document.createElement("div");
    div.className = "feed-item" + (markUnread ? (entry.seen ? " seen" : " unread") : "");
    div.textContent = (markUnread ? (entry.seen ? "• " : "● ") : "✦ ") + entry.text;
    parent.appendChild(div);
  }
}

function closePanel() {
  openPanelBuilder = null;
  el("panel-overlay").classList.add("hidden");
}

// --- Polling -------------------------------------------------------------
async function poll() {
  if (!petId()) return;
  const res = await api("/pets/" + petId());
  if (res.ok) { state = res.data; updateAvatar(); renderHud(); }
}
function startPolling() { stopPolling(); pollHandle = setInterval(poll, POLL_MS); }
function stopPolling() { if (pollHandle) { clearInterval(pollHandle); pollHandle = null; } }

// --- Boot ----------------------------------------------------------------
async function init() {
  window.I18n.onChange(onLangChanged);
  applyChrome();
  el("login-btn").onclick = onLogin;
  el("register-btn").onclick = onRegister;
  el("reroll-btn").onclick = reroll;
  el("movein-btn").onclick = onMoveIn;
  el("top-logout").onclick = onLogout;
  el("panel-close").onclick = closePanel;
  el("panel-overlay").onclick = (e) => { if (e.target === el("panel-overlay")) closePanel(); };

  const cat = await api("/catalog");
  if (cat.ok) catalog = cat.data;

  if (token()) {
    const check = await api("/pets");
    if (check.ok) { await afterLogin(); return; }
    setToken("");
  }
  showScreen("auth");
}

init();
