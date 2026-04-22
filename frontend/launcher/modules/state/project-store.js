/**
 * Project Store · ROADMAP §11.2
 * =====================================
 * Single source of truth for project / handoff / chat context
 *
 * Why:
 *   modules/chat.js 555 行 已是 god object
 *   crm/projects/knowledge 多 module 散處抓 currentProject
 *   v1.2 Project-first shell 前不重構 · 永遠撞耦合
 *
 * Design:
 *   - 不引 Redux/Zustand · 純 vanilla EventTarget + Map
 *   - 訂閱者 store.subscribe(key, callback) 收 key 變動
 *   - 寫者 store.set(key, value) 自動 broadcast
 *   - 跨分頁同步走既有 BroadcastChannel(modules/projects.js)
 *
 * Usage:
 *   import { projectStore } from "./state/project-store.js";
 *   projectStore.subscribe("currentProject", (proj) => renderHeader(proj));
 *   projectStore.set("currentProject", { id, name, ... });
 */

class ProjectStore extends EventTarget {
  constructor() {
    super();
    this._state = new Map();
    // Cross-tab sync via existing channel
    if ("BroadcastChannel" in globalThis) {
      this._bc = new BroadcastChannel("chengfu-project-store");
      this._bc.onmessage = (e) => {
        if (e.data && e.data.type === "set" && e.data.key) {
          this._state.set(e.data.key, e.data.value);
          this.dispatchEvent(new CustomEvent(`change:${e.data.key}`, {
            detail: { value: e.data.value, source: "remote-tab" },
          }));
        }
      };
    }
  }

  get(key, defaultValue = null) {
    return this._state.has(key) ? this._state.get(key) : defaultValue;
  }

  set(key, value, opts = {}) {
    const prev = this._state.get(key);
    if (prev === value) return;  // no-op
    this._state.set(key, value);
    this.dispatchEvent(new CustomEvent(`change:${key}`, {
      detail: { value, prev, source: "local" },
    }));
    // Cross-tab broadcast(opts.silent skip)
    if (!opts.silent && this._bc) {
      try {
        this._bc.postMessage({ type: "set", key, value });
      } catch (e) {
        // 結構不可序列化(例:有 function) · 跨分頁不同步但本地仍 OK
        console.warn("[project-store] BC postMessage fail:", e);
      }
    }
  }

  /**
   * Subscribe to changes of a specific key.
   * @param {string} key
   * @param {(value, detail) => void} callback
   * @returns {() => void} unsubscribe function
   */
  subscribe(key, callback) {
    const handler = (ev) => callback(ev.detail.value, ev.detail);
    this.addEventListener(`change:${key}`, handler);
    return () => this.removeEventListener(`change:${key}`, handler);
  }

  /** clear single key or all */
  clear(key = null) {
    if (key === null) {
      this._state.clear();
    } else {
      this._state.delete(key);
    }
  }

  /** snapshot for debugging */
  dump() {
    return Object.fromEntries(this._state);
  }
}

export const projectStore = new ProjectStore();

// Standard keys(避免 typo · IDE 自動完成)
export const KEYS = Object.freeze({
  CURRENT_PROJECT: "currentProject",       // {id, name, client, ...}
  CURRENT_AGENT: "currentAgent",           // {num, name, model}
  HANDOFF_DRAFT: "handoffDraft",           // {goal, constraints, ...}
  CHAT_PROMPT_DRAFT: "chatPromptDraft",    // 草稿 · 不送出
});

// Debug helper · window.projectStore 直接看
if (typeof window !== "undefined") {
  window.projectStore = projectStore;
}
