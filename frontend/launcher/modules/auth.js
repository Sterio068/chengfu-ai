/**
 * LibreChat JWT 認證
 * httpOnly cookie · JS 無法直接讀 · 用 /api/auth/refresh 交換 Bearer token
 * v4.2 起:401 自動 refresh · 失敗則 redirect /login · 並通知 banner
 */
import { API } from "./config.js";

let _jwt = null;
let _userEmail = null;
let _sessionExpiredNotified = false;

export function setUserEmail(email) { _userEmail = (email || "").trim() || null; }
export function getUserEmail() { return _userEmail; }

/**
 * 包好的 fetch · 自帶 Authorization header
 * · 遇 401 自動呼叫一次 refreshAuth 後重試 1 次
 * · 若 refresh 也失敗(表示 session 真的過期) → 顯示 banner 然後 reload /login
 */
export async function authFetch(url, opts = {}) {
  const res = await _doFetch(url, opts);
  if (res.status === 401) {
    try {
      await refreshAuth();
      return await _doFetch(url, opts);  // 重試 1 次
    } catch (e) {
      // refresh 也 401 · 真的過期 · 引導重新登入
      if (!_sessionExpiredNotified) {
        _sessionExpiredNotified = true;
        _showSessionExpiredBanner();
      }
      return res;
    }
  }
  return res;
}

async function _doFetch(url, opts) {
  const headers = { ...(opts.headers || {}) };
  if (_jwt) headers["Authorization"] = `Bearer ${_jwt}`;
  if (_userEmail) headers["X-User-Email"] = _userEmail;  // 給後端 require_admin 用
  return fetch(url, { credentials: "include", ...opts, headers });
}

export async function refreshAuth() {
  const r = await fetch(API.refresh, { method: "POST", credentials: "include" });
  if (!r.ok) throw new Error(`refresh ${r.status}`);
  const data = await r.json();
  _jwt = data.token;
  return data;
}

export function getJwt() { return _jwt; }

// ---------- 系統狀態 Banner(auth 過期 / 後端離線)----------

function _showSessionExpiredBanner() {
  _showBanner({
    message: "你的登入已過期,請重新登入。",
    actionLabel: "重新登入",
    onClick: () => window.location.href = "/login",
    variant: "warn",
  });
}

/**
 * 通用 banner · 給 auth / health / 其他需要告知使用者的狀態共用
 * variant: "error" | "warn" | "info"
 */
export function _showBanner({ message, actionLabel, onClick, variant = "error" }) {
  let el = document.getElementById("sys-banner");
  if (!el) {
    el = document.createElement("div");
    el.id = "sys-banner";
    el.className = `sys-banner ${variant}`;
    document.body.prepend(el);
  } else {
    el.className = `sys-banner ${variant}`;
  }
  el.innerHTML = `
    <span>${message}</span>
    ${actionLabel ? `<button class="banner-action" type="button">${actionLabel}</button>` : ""}
  `;
  if (actionLabel && onClick) {
    el.querySelector(".banner-action")?.addEventListener("click", onClick);
  }
  document.body.classList.add("has-banner");
  requestAnimationFrame(() => el.classList.add("show"));
}

export function _hideBanner() {
  const el = document.getElementById("sys-banner");
  if (!el) return;
  el.classList.remove("show");
  document.body.classList.remove("has-banner");
  setTimeout(() => el.remove(), 250);
}
