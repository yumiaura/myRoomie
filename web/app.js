"use strict";

// Served from the same origin as the API, so the base is empty.
const STAT_KEYS = ["hunger", "hygiene", "energy", "mood", "health", "loneliness", "affection"];
const POLL_MS = 5000;

let catalog = {};
let state = {};
let pollHandle = null;

function token() { return localStorage.getItem("token") || ""; }
function setToken(value) { value ? localStorage.setItem("token", value) : localStorage.removeItem("token"); }
function petId() { return localStorage.getItem("pet_id") || ""; }
function setPetId(value) { value ? localStorage.setItem("pet_id", value) : localStorage.removeItem("pet_id"); }

const el = (id) => document.getElementById(id);

async function api(path, method = "GET", body = null) {
  const headers = { "Content-Type": "application/json" };
  if (token()) headers["Authorization"] = "Bearer " + token();
  let response;
  try {
    response = await fetch(path, { method, headers, body: body == null ? null : JSON.stringify(body) });
  } catch (err) {
    return { ok: false, status: 0, error: "server is offline" };
  }
  let data = null;
  const text = await response.text();
  if (text) { try { data = JSON.parse(text); } catch (err) { data = null; } }
  if (response.status === 401 && token()) onSessionExpired();
  if (response.ok) return { ok: true, status: response.status, data };
  const detail = data && data.detail ? data.detail : "request failed (" + response.status + ")";
  return { ok: false, status: response.status, error: detail };
}

function showScreen(name) {
  for (const id of ["auth", "creation", "room"]) el(id).classList.toggle("hidden", id !== name);
}

// --- Auth ----------------------------------------------------------------
async function onRegister() {
  const res = await api("/auth/register", "POST", { username: el("username").value.trim(), password: el("password").value });
  el("auth-status").textContent = res.ok ? "Account created — now log in." : res.error;
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
  el("auth-status").textContent = "Session expired — please sign in again.";
}

// --- Creation ------------------------------------------------------------
let previewSeed = 0;
async function reroll() {
  const res = await api("/preview", "POST", {});
  if (!res.ok) { el("preview").textContent = "(server unavailable)"; return; }
  previewSeed = res.data.seed;
  const t = res.data.traits;
  el("preview").textContent = `${t.personality} · loves ${t.love_language.replace(/_/g, " ")} · into ${t.hobby} · favourite food: ${t.favorite_food.replace(/_/g, " ")}`;
}

async function onMoveIn() {
  const name = el("roomie-name").value.trim();
  if (!name) { el("create-status").textContent = "Give them a name first."; return; }
  const payload = { name, gender: el("gender").value };
  if (previewSeed) payload.seed = previewSeed;
  const res = await api("/pets", "POST", payload);
  if (!res.ok) { el("create-status").textContent = res.error; return; }
  const visited = await api("/pets/" + res.data.id + "/visit", "POST");
  enterRoom(visited.ok ? visited.data : res.data);
}

// --- Room ----------------------------------------------------------------
function enterRoom(data) {
  setPetId(data.id);
  showScreen("room");
  render(data);
  startPolling();
}

async function poll() {
  if (!petId()) return;
  const res = await api("/pets/" + petId());
  if (res.ok) render(res.data);
}
function startPolling() { stopPolling(); pollHandle = setInterval(poll, POLL_MS); }
function stopPolling() { if (pollHandle) { clearInterval(pollHandle); pollHandle = null; } }

async function act(path, body = null) {
  if (!petId()) return;
  const res = await api("/pets/" + petId() + path, "POST", body);
  if (res.ok) render(res.data);
  else el("header").textContent = "⚠ " + res.error;
}

async function onMoveOut() {
  stopPolling();
  setPetId(""); state = {};
  showScreen("creation");
  reroll();
}

async function onMarkRead() {
  if (!petId()) return;
  const res = await api("/pets/" + petId() + "/inbox/seen", "POST");
  if (res.ok) render(res.data);
}

// Build the catalog-driven action controls once.
function buildActions() {
  const make = (container, label, items, handler) => {
    const row = document.createElement("div");
    row.className = "action-row";
    const select = document.createElement("select");
    for (const key of items) {
      const opt = document.createElement("option");
      opt.value = key; opt.textContent = key.replace(/_/g, " ");
      select.appendChild(opt);
    }
    const button = document.createElement("button");
    button.textContent = label;
    button.onclick = () => handler(select.value);
    row.appendChild(select); row.appendChild(button);
    container.appendChild(row);
    return select;
  };
  const simple = (container, label, handler) => {
    const button = document.createElement("button");
    button.textContent = label; button.onclick = handler;
    container.appendChild(button);
  };
  const actions = el("actions");
  actions.innerHTML = "";
  make(actions, "Feed", Object.keys(catalog.foods || {}), (v) => act("/feed", { food: v }));
  simple(actions, "Wash", () => act("/wash"));
  make(actions, "Play", Object.keys(catalog.activities || {}), (v) => act("/play", { activity: v }));
  make(actions, "Gift", Object.keys(catalog.gifts || {}), (v) => act("/gift", { item: v }));
  make(actions, "Chore", Object.keys(catalog.chores || {}), (v) => act("/chore", { task: v }));
  make(actions, "Work", Object.keys(catalog.jobs || {}), (v) => act("/work", { job: v }));
  simple(actions, "Pay rent", () => act("/pay-rent"));

  const shop = el("shop-actions");
  shop.innerHTML = "";
  make(shop, "Buy", Object.keys(catalog.shop || {}), (v) => act("/buy", { item: v }));
  wearSelect = make(shop, "Wear", [], (v) => v && act("/wear", { item: v }));
}
let wearSelect = null;

function moodKey(s) {
  if (s.health < 30) return "sick";
  if (s.mood < 35) return "sad";
  if (s.mood > 70) return "happy";
  return "neutral";
}

function render(data) {
  state = data;
  el("header").textContent = `${data.name} · ${String(data.relationship).replace(/_/g, " ")} · Lv ${data.level}` + (data.season ? " · " + data.season : "");
  const t = data.traits;
  el("traits").textContent = `${t.personality} · loves ${t.love_language.replace(/_/g, " ")} · into ${t.hobby} · favourite food: ${t.favorite_food.replace(/_/g, " ")}`;
  const w = data.wallet;
  el("wallet").textContent = `💰 ${w.money} coins   ·   🏠 rent ${w.rent_amount}` + (w.rent_overdue ? " (OVERDUE!)" : "");

  const bars = el("bars");
  bars.innerHTML = "";
  for (const key of STAT_KEYS) {
    const value = Math.round(data.stats[key]);
    const div = document.createElement("div");
    div.className = "bar";
    div.innerHTML = `<div class="label"><span>${key}</span><span>${value}</span></div><div class="track"><div class="fill" style="width:${value}%"></div></div>`;
    bars.appendChild(div);
  }

  // Portrait + outfit overlay (prefer per-gender art, fall back, else hide).
  el("portrait").src = `/assets/${data.gender}_${moodKey(data.stats)}.png`;
  const outfitImg = el("outfit");
  if (data.outfit) {
    outfitImg.style.display = "block";
    outfitImg.onerror = () => { outfitImg.onerror = () => { outfitImg.style.display = "none"; }; outfitImg.src = `/assets/outfit_${data.outfit}.png`; };
    outfitImg.src = `/assets/outfit_${data.outfit}_${data.gender}.png`;
  } else {
    outfitImg.style.display = "none";
  }

  // Wardrobe / decor.
  const worn = data.outfit ? String(data.outfit).replace(/_/g, " ") : "nothing in particular";
  const decorNames = (data.decor || []).map((d) => d.replace(/_/g, " "));
  el("outfit-label").textContent = `Wearing: ${worn} · Decor: ${decorNames.length ? decorNames.join(", ") : "none"}`;
  if (wearSelect) {
    wearSelect.innerHTML = "";
    for (const item of (data.wardrobe || [])) {
      const opt = document.createElement("option");
      opt.value = item; opt.textContent = item.replace(/_/g, " ");
      wearSelect.appendChild(opt);
    }
  }
  const decor = el("decor");
  decor.innerHTML = "";
  for (const item of (data.decor || [])) {
    const img = document.createElement("img");
    img.src = `/assets/decor_${item}.png`; img.alt = item;
    decor.appendChild(img);
  }

  renderFeed("inbox", data.inbox, true);
  renderFeed("diary", data.diary, false, "✦ ");
  const unread = (data.inbox || []).filter((e) => !e.seen).length;
  el("inbox-title").textContent = unread > 0 ? `Notes from them (${unread} new)` : "Notes from them";
}

function renderFeed(containerId, items, markUnread, prefix) {
  const box = el(containerId);
  box.innerHTML = "";
  const list = (items || []).slice(-8).reverse();
  for (const entry of list) {
    const div = document.createElement("div");
    div.className = "item";
    if (markUnread) {
      div.classList.add(entry.seen ? "seen" : "unread");
      div.textContent = (entry.seen ? "• " : "● ") + entry.text;
    } else {
      div.textContent = (prefix || "") + entry.text;
    }
    box.appendChild(div);
  }
}

// --- Boot ----------------------------------------------------------------
async function init() {
  el("login-btn").onclick = onLogin;
  el("register-btn").onclick = onRegister;
  el("reroll-btn").onclick = reroll;
  el("movein-btn").onclick = onMoveIn;
  el("creation-logout").onclick = onLogout;
  el("switch-btn").onclick = onMoveOut;
  el("logout-btn").onclick = onLogout;
  el("mark-read").onclick = onMarkRead;

  const cat = await api("/catalog");
  if (cat.ok) { catalog = cat.data; buildActions(); }

  if (token()) {
    const check = await api("/pets");
    if (check.ok) { await afterLogin(); return; }
    setToken("");
  }
  showScreen("auth");
}

init();
