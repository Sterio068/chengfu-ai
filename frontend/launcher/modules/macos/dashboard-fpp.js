/**
 * Dashboard F++ v1.5 · 主畫面 IA 重構(誠實版)
 * =====================================
 * 設計:design_handoff_main_screen_ia/README.md
 * 路線:F++ macOS Finder + iOS App 卡 混合
 *
 * 結構(由上而下):
 *   1. Toolbar(承 logo · 上下頁 · 視圖切換 · inline composer · 搜尋 · ?)
 *   2. Mini-Today(時間 + 問候 + 3 widget)· 只 root
 *   3. Path bar(麵包屑 + demo 切換)
 *   4. Smart Folder segments(全部 / 今天回過 / @我 / 待我審 / 3 天沒動 / 工作區 / + 自訂(v1.6 dimmed))
 *   5. Main grid · 21 對話圖示
 *   6. Status bar(在 dock 上方 · 連線 / 用量 / 待回應 / 鍵盤提示)
 *
 * 鍵盤:
 *   j/↓ k/↑ h/← l/→ · 移動選擇
 *   space · Quick Look
 *   enter · 開啟對話(暫:跳工作包頁)
 *   ? · toggle 鍵盤提示
 *   esc · 關 Quick Look / popover
 *
 * v1.5 誠實處理:
 *   - AI banner 拿掉(v1.6 才有)
 *   - 「+ 自訂 (v1.6)」segment dimmed dashed
 *   - 「待回應 3 · ✨ 看建議 (v1.6)」widget 點 → 預告 popover
 */
import { escapeHtml } from "../util.js";

// Mock data · 21 對話 · 與設計一致
const MOCK_ITEMS = [
  { id: 1, name: "中秋禮盒",   date: "今天",  kind: "PDF", presence: "typing",  unread: 3, ws: "投標", color: "#FF3B30" },
  { id: 2, name: "RFP v3",     date: "昨天",  kind: "DOC", presence: "idle",    unread: 0, ws: "投標", color: "#FF3B30" },
  { id: 3, name: "客戶回信",   date: "3 天前", kind: "📧",  presence: "idle",    unread: 1, ws: "公關", color: "#34C759" },
  { id: 4, name: "設計初稿",   date: "上週",  kind: "IMG", presence: "running", unread: 0, ws: "設計", color: "#AF52DE" },
  { id: 5, name: "現場照",     date: "5/12",  kind: "IMG", presence: "idle",    unread: 0, ws: "活動", color: "#FF9500" },
  { id: 6, name: "預算表",     date: "5/10",  kind: "DOC", presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 7, name: "公關稿",     date: "5/08",  kind: "DOC", presence: "idle",    unread: 0, ws: "公關", color: "#34C759" },
  { id: 8, name: "工地巡查",   date: "5/05",  kind: "IMG", presence: "typing",  unread: 2, ws: "活動", color: "#FF9500" },
  { id: 9, name: "財報 Q1",    date: "4/28",  kind: "DOC", presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 10, name: "會議紀錄",  date: "4/22",  kind: "MTG", presence: "idle",    unread: 0, ws: "公關", color: "#34C759" },
  { id: 11, name: "LOGO",      date: "4/15",  kind: "IMG", presence: "idle",    unread: 0, ws: "設計", color: "#AF52DE" },
  { id: 12, name: "下週進度",  date: "4/10",  kind: "💬",  presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 13, name: "客戶 A",    date: "4/08",  kind: "💬",  presence: "idle",    unread: 0, ws: "公關", color: "#34C759" },
  { id: 14, name: "成本表",    date: "4/03",  kind: "DOC", presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 15, name: "問卷",      date: "3/28",  kind: "DOC", presence: "idle",    unread: 0, ws: "公關", color: "#34C759" },
  { id: 16, name: "合約",      date: "3/22",  kind: "PDF", presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 17, name: "人事",      date: "3/18",  kind: "DOC", presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 18, name: "差旅",      date: "3/14",  kind: "DOC", presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 19, name: "報表",      date: "3/10",  kind: "DOC", presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 20, name: "備忘",      date: "3/05",  kind: "💬",  presence: "idle",    unread: 0, ws: "營運", color: "#007AFF" },
  { id: 21, name: "補件",      date: "3/02",  kind: "PDF", presence: "idle",    unread: 0, ws: "投標", color: "#FF3B30" },
];

const SEGMENTS = [
  { k: "all",     l: "全部 24",       active: true,  smart: false },
  { k: "today",   l: "◐ 今天回過 5",   active: false, smart: true },
  { k: "mention", l: "@我 3",          active: false, smart: true },
  { k: "review",  l: "待我審 2",       active: false, smart: true },
  { k: "stale",   l: "3 天沒動 7",     active: false, smart: true },
  { k: "ws-1",    l: "投標 6",         active: false, smart: false },
  { k: "ws-2",    l: "活動 8",         active: false, smart: false },
  { k: "ws-3",    l: "設計 4",         active: false, smart: false },
];

let _state = {
  view: "grid",      // grid / list / column
  selected: 0,       // current selected index
  segment: "all",
  showHints: true,
  quickLook: false,
  v15TeasePop: false,
  initialized: false,
};

let _root = null;
let _items = MOCK_ITEMS;

// ============================================================
// Render
// ============================================================
function _render() {
  if (!_root) return;
  _root.innerHTML = `
    ${_renderToolbar()}
    ${_renderMiniToday()}
    ${_renderPathBar()}
    ${_renderSegments()}
    <div class="fpp-main" id="fpp-main">
      ${_renderGrid()}
    </div>
    ${_renderStatusBar()}
  `;
  _bindToolbar();
  _bindGrid();
  _bindWidgets();
  _bindHints();
  _bindSegments();
}

function _renderToolbar() {
  return `
    <div class="fpp-toolbar">
      <button class="fpp-logo" data-fpp-logo title="導覽 (⌘0)">
        <span class="fpp-logo-text">承</span>
        <span class="fpp-logo-arrow">▾</span>
      </button>
      <div class="fpp-nav-arrows">
        <button class="fpp-arrow" disabled aria-label="上一頁">‹</button>
        <button class="fpp-arrow" disabled aria-label="下一頁">›</button>
      </div>
      <div class="fpp-view-switch" role="tablist">
        ${["grid", "list", "column"].map(v => `
          <button class="fpp-view-btn ${_state.view === v ? "active" : ""}"
                  data-fpp-view="${v}" role="tab" aria-selected="${_state.view === v}">
            ${v === "grid" ? "圖示" : v === "list" ? "清單" : "分欄"}
          </button>
        `).join("")}
      </div>
      <div class="fpp-composer">
        <span class="fpp-composer-dot" aria-hidden="true"></span>
        <input type="text" class="fpp-composer-input"
               placeholder="交給主管家…(輸入後 ↵ 送出)"
               aria-label="主管家對話">
        <kbd class="fpp-composer-hint">↵</kbd>
      </div>
      <button class="fpp-search" data-fpp-search title="全域搜尋 (⌘K)" aria-label="搜尋">
        <svg width="13" height="13" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" fill="none">
          <circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <kbd>⌘F</kbd>
      </button>
      <button class="fpp-hints-toggle ${_state.showHints ? "active" : ""}"
              data-fpp-hints title="鍵盤提示 (?)">?</button>
    </div>
  `;
}

function _renderMiniToday() {
  const now = new Date();
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  const day = ["日", "一", "二", "三", "四", "五", "六"][now.getDay()];
  const dateStr = `週${day} ${now.getMonth() + 1}/${now.getDate()}`;
  const userName = window.app?.user?.name || window.app?.user?.email?.split("@")[0] || "你";
  const greeting = now.getHours() < 12 ? "早安" : now.getHours() < 18 ? "午安" : "晚安";

  return `
    <div class="fpp-today">
      <div class="fpp-today-time">
        <div class="fpp-time-big">${hh}:${mm}</div>
        <div class="fpp-time-date">${dateStr}</div>
      </div>
      <div class="fpp-today-greeting">
        <div class="fpp-greeting-text">${greeting} ${escapeHtml(userName)}</div>
        <div class="fpp-greeting-sub">本週省了 7.4 小時</div>
      </div>
      <div class="fpp-widgets">
        <div class="fpp-widget" data-fpp-widget="conversations">
          <div class="fpp-widget-row">
            <span class="fpp-widget-big">12</span>
            <span class="fpp-widget-unit">次</span>
          </div>
          <div class="fpp-widget-label">今日對話</div>
        </div>
        <div class="fpp-widget" data-fpp-widget="saved">
          <div class="fpp-widget-row">
            <span class="fpp-widget-big">7.4</span>
            <span class="fpp-widget-unit">小時</span>
          </div>
          <div class="fpp-widget-label">本週節省</div>
        </div>
        <div class="fpp-widget fpp-widget-accent" data-fpp-widget="inbox">
          <div class="fpp-widget-row">
            <span class="fpp-widget-big">3</span>
            <span class="fpp-widget-unit">件</span>
            <span class="fpp-widget-cta">✨ 看建議 (v1.6)</span>
          </div>
          <div class="fpp-widget-label">待回應</div>
        </div>
      </div>
    </div>
  `;
}

function _renderPathBar() {
  return `
    <div class="fpp-path">
      <span class="fpp-path-label">路徑</span>
      <span class="fpp-path-segment fpp-path-current">主畫面</span>
    </div>
  `;
}

function _renderSegments() {
  return `
    <div class="fpp-segments" role="tablist">
      ${SEGMENTS.map(s => `
        <button class="fpp-segment ${s.active ? "active" : ""} ${s.smart ? "smart" : ""}"
                data-fpp-segment="${s.k}" role="tab" aria-selected="${s.active}">
          ${escapeHtml(s.l)}
        </button>
      `).join("")}
      <button class="fpp-segment fpp-segment-disabled"
              title="v1.6 開放" aria-disabled="true">+ 自訂 (v1.6)</button>
      <span class="fpp-segments-hint">橘色 · Smart Folder 條件查詢</span>
    </div>
  `;
}

function _renderGrid() {
  return `
    <div class="fpp-grid" id="fpp-grid">
      ${_items.map((it, i) => `
        <button class="fpp-item ${i === _state.selected ? "selected" : ""}"
                data-fpp-item="${i}" tabindex="${i === _state.selected ? 0 : -1}"
                aria-label="${escapeHtml(it.name)} · ${it.date}">
          <div class="fpp-icon" style="--ws-color:${it.color}">
            <span class="fpp-icon-kind">${it.kind}</span>
            ${it.presence === "typing" ? `<span class="fpp-icon-presence typing" title="對方輸入中">✏</span>` : ""}
            ${it.presence === "running" ? `<span class="fpp-icon-presence running" title="主管家進行中">⟳</span>` : ""}
            ${it.unread > 0 ? `<span class="fpp-icon-badge">${it.unread}</span>` : ""}
          </div>
          <span class="fpp-item-name">${escapeHtml(it.name)}</span>
          <span class="fpp-item-date">${it.date}</span>
        </button>
      `).join("")}
    </div>
  `;
}

function _renderStatusBar() {
  const item = _items[_state.selected];
  return `
    <div class="fpp-status">
      <span class="fpp-status-dot" aria-hidden="true"></span>
      <span>6 容器 healthy</span>
      <span class="fpp-status-sep">│</span>
      <span>選中: <b>${escapeHtml(item?.name || "—")}</b></span>
      <span class="fpp-status-sep">│</span>
      <span>$0.45 / $20</span>
      <span class="fpp-status-sep">│</span>
      <span class="fpp-status-accent">● 2 待回應</span>
      <span class="fpp-status-spacer"></span>
      <span class="fpp-status-keys">j/k 移動 · space 預覽 · enter 開啟 · ? 提示</span>
    </div>
  `;
}

// ============================================================
// Bind
// ============================================================
function _bindToolbar() {
  _root.querySelectorAll("[data-fpp-view]").forEach(b => {
    b.addEventListener("click", () => {
      _state.view = b.dataset.fppView;
      _render();
    });
  });
  _root.querySelector("[data-fpp-logo]")?.addEventListener("click", () => {
    if (window.app?.openPalette) window.app.openPalette();
  });
  _root.querySelector("[data-fpp-search]")?.addEventListener("click", () => {
    if (window.app?.openPalette) window.app.openPalette();
  });
  // composer enter → 開新對話
  const composer = _root.querySelector(".fpp-composer-input");
  composer?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && composer.value.trim()) {
      const text = composer.value.trim();
      window.app?.openAgent?.("00");
      window.toast?.info?.(`已交給主管家:${text.slice(0, 30)}${text.length > 30 ? "…" : ""}`);
      composer.value = "";
    }
  });
}

function _bindGrid() {
  _root.querySelectorAll("[data-fpp-item]").forEach(btn => {
    const idx = parseInt(btn.dataset.fppItem, 10);
    btn.addEventListener("click", () => {
      _state.selected = idx;
      _renderGridOnly();
      _renderStatusOnly();
    });
    btn.addEventListener("dblclick", () => {
      _openItem(_items[idx]);
    });
  });
}

function _bindSegments() {
  _root.querySelectorAll("[data-fpp-segment]").forEach(b => {
    b.addEventListener("click", () => {
      const k = b.dataset.fppSegment;
      SEGMENTS.forEach(s => s.active = (s.k === k));
      _state.segment = k;
      _render();
    });
  });
}

function _bindWidgets() {
  _root.querySelector('[data-fpp-widget="inbox"]')?.addEventListener("click", () => {
    _state.v15TeasePop = true;
    _renderTease();
  });
}

function _bindHints() {
  _root.querySelector("[data-fpp-hints]")?.addEventListener("click", () => {
    _state.showHints = !_state.showHints;
    _renderHintsOverlay();
    _root.querySelector("[data-fpp-hints]")?.classList.toggle("active", _state.showHints);
  });
}

// 局部 render(避免整頁閃)
function _renderGridOnly() {
  const main = _root.querySelector("#fpp-main");
  if (main) {
    main.innerHTML = _renderGrid();
    _bindGrid();
  }
}

function _renderStatusOnly() {
  const status = _root.querySelector(".fpp-status");
  if (status) status.outerHTML = _renderStatusBar();
}

// ============================================================
// Quick Look overlay
// ============================================================
function _openQuickLook() {
  if (_state.quickLook) return;
  _state.quickLook = true;
  const item = _items[_state.selected];
  const overlay = document.createElement("div");
  overlay.className = "fpp-quicklook-overlay";
  overlay.id = "fpp-quicklook";
  overlay.innerHTML = `
    <div class="fpp-quicklook">
      <div class="fpp-quicklook-head">
        <div class="fpp-quicklook-title">
          <div class="fpp-icon fpp-icon-large" style="--ws-color:${item.color}">
            <span class="fpp-icon-kind">${item.kind}</span>
          </div>
          <div>
            <div class="fpp-quicklook-name">${escapeHtml(item.name)}</div>
            <div class="fpp-quicklook-meta">${item.ws} · ${item.date}</div>
          </div>
        </div>
        <button class="fpp-quicklook-close" aria-label="關閉">space / esc 關閉</button>
      </div>
      <div class="fpp-quicklook-section">
        <div class="fpp-quicklook-label">最近 3 訊</div>
        <div class="fpp-msg fpp-msg-them">
          <div class="fpp-msg-bubble">客戶 A:RFP v3 收到了 · 有 3 個地方要再確認…</div>
        </div>
        <div class="fpp-msg fpp-msg-me">
          <div class="fpp-msg-bubble fpp-msg-bubble-accent">主管家:已整理回應草稿,需要您審核</div>
        </div>
        <div class="fpp-msg fpp-msg-them">
          <div class="fpp-msg-bubble">Sterio:第 2 點建議改成…</div>
        </div>
      </div>
      <div class="fpp-quicklook-section">
        <div class="fpp-quicklook-label">素材</div>
        <div class="fpp-quicklook-files">
          <div class="fpp-file"><span class="fpp-file-icon">PDF</span> RFP_v3.pdf</div>
          <div class="fpp-file"><span class="fpp-file-icon">📧</span> 客戶回信.eml</div>
        </div>
      </div>
      <div class="fpp-quicklook-actions">
        <button class="fpp-btn fpp-btn-primary" data-fpp-ql-open>開啟對話 ↵</button>
        <button class="fpp-btn" data-fpp-ql-reply>快速回覆</button>
      </div>
    </div>
  `;
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) _closeQuickLook();
  });
  overlay.querySelector("[data-fpp-ql-open]")?.addEventListener("click", () => {
    _closeQuickLook();
    _openItem(item);
  });
  document.body.appendChild(overlay);
  setTimeout(() => overlay.classList.add("open"), 10);
}

function _closeQuickLook() {
  _state.quickLook = false;
  const overlay = document.getElementById("fpp-quicklook");
  if (overlay) {
    overlay.classList.remove("open");
    setTimeout(() => overlay.remove(), 160);
  }
}

function _openItem(item) {
  // 暫時:跳到對應 workspace · 之後 v1.6 改開對話 window
  const wsMap = { "投標": 1, "活動": 2, "設計": 3, "公關": 4, "營運": 5 };
  const wsId = wsMap[item.ws];
  if (wsId && window.app?.openWorkspace) {
    window.app.openWorkspace(wsId);
  } else {
    window.toast?.info?.(`開啟 ${item.name}`);
  }
}

// ============================================================
// v1.5 Tease popover
// ============================================================
function _renderTease() {
  const old = document.getElementById("fpp-v15-tease");
  if (old) old.remove();
  if (!_state.v15TeasePop) return;

  const t = document.createElement("div");
  t.id = "fpp-v15-tease";
  t.className = "fpp-tease-overlay";
  t.innerHTML = `
    <div class="fpp-tease">
      <div class="fpp-tease-head">
        <div class="fpp-tease-title">✨ 主管家建議</div>
        <button class="fpp-tease-close" aria-label="關閉">×</button>
      </div>
      <div class="fpp-tease-body">
        主管家會掃描你的對話 · 主動提醒截止日 / 待回信 / 停滯項目。
        <br><br>
        此功能將在 <strong>v1.6</strong> 推出 · 需要先補齊對話 metadata + 觸發管線。
      </div>
      <div class="fpp-tease-actions">
        <button class="fpp-btn fpp-btn-primary" data-fpp-tease-ack>知道了</button>
      </div>
    </div>
  `;
  t.addEventListener("click", (e) => {
    if (e.target === t || e.target.classList.contains("fpp-tease-close") ||
        e.target.dataset.fppTeaseAck !== undefined) {
      _state.v15TeasePop = false;
      _renderTease();
    }
  });
  document.body.appendChild(t);
}

// ============================================================
// Hints overlay
// ============================================================
function _renderHintsOverlay() {
  const old = document.getElementById("fpp-hints");
  if (old) old.remove();
  if (!_state.showHints) return;
  const h = document.createElement("div");
  h.id = "fpp-hints";
  h.className = "fpp-hints";
  h.innerHTML = `
    <div class="fpp-hints-head">
      <span class="fpp-hints-title">鍵盤</span>
      <button class="fpp-hints-close" aria-label="關閉" data-fpp-hints-close>×</button>
    </div>
    <div class="fpp-hints-body">
      <div><kbd>j / k</kbd><span>上下移動</span></div>
      <div><kbd>h / l</kbd><span>左右移動</span></div>
      <div><kbd>space</kbd><span>Quick Look</span></div>
      <div><kbd>↵</kbd><span>開啟對話</span></div>
      <div><kbd>esc</kbd><span>關閉</span></div>
      <div><kbd>?</kbd><span>切換此提示</span></div>
    </div>
  `;
  h.querySelector("[data-fpp-hints-close]")?.addEventListener("click", () => {
    _state.showHints = false;
    h.remove();
    _root?.querySelector("[data-fpp-hints]")?.classList.remove("active");
  });
  document.body.appendChild(h);
}

// ============================================================
// Global keyboard
// ============================================================
function _onKey(e) {
  // 不在 dashboard view 不處理
  if (window.app?.currentView !== "dashboard") return;
  // input 中只處理 esc / 特定 key
  const t = e.target;
  const inInput = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);

  if (_state.quickLook) {
    if (e.key === "Escape" || e.key === " ") {
      e.preventDefault();
      _closeQuickLook();
    }
    return;
  }
  if (inInput) return;

  const total = _items.length;
  const cols = 7;
  let handled = true;
  switch (e.key) {
    case "j": case "ArrowDown":
      _state.selected = Math.min(total - 1, _state.selected + cols);
      break;
    case "k": case "ArrowUp":
      _state.selected = Math.max(0, _state.selected - cols);
      break;
    case "h": case "ArrowLeft":
      _state.selected = Math.max(0, _state.selected - 1);
      break;
    case "l": case "ArrowRight":
      _state.selected = Math.min(total - 1, _state.selected + 1);
      break;
    case " ":
      _openQuickLook();
      break;
    case "Enter":
      _openItem(_items[_state.selected]);
      break;
    case "?":
      _state.showHints = !_state.showHints;
      _renderHintsOverlay();
      _root?.querySelector("[data-fpp-hints]")?.classList.toggle("active", _state.showHints);
      break;
    default:
      handled = false;
  }
  if (handled) {
    e.preventDefault();
    if (e.key !== "?") {
      _renderGridOnly();
      _renderStatusOnly();
      // 滾動 selected 進入視野
      const sel = _root?.querySelector(`[data-fpp-item="${_state.selected}"]`);
      sel?.focus();
      sel?.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
  }
}

// ============================================================
// Public API
// ============================================================
export const dashboardFpp = {
  /** 把 view-dashboard innerHTML 接管 */
  init(viewEl) {
    if (_state.initialized && _root === viewEl) {
      _render();
      return;
    }
    _root = viewEl;
    _root.classList.add("view-dashboard-fpp");
    _state.initialized = true;
    _render();
    _renderHintsOverlay();
    document.addEventListener("keydown", _onKey);
  },

  destroy() {
    document.removeEventListener("keydown", _onKey);
    document.getElementById("fpp-hints")?.remove();
    document.getElementById("fpp-quicklook")?.remove();
    document.getElementById("fpp-v15-tease")?.remove();
  },
};

if (typeof window !== "undefined") window.dashboardFpp = dashboardFpp;
