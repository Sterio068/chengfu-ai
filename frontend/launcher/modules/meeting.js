/**
 * Meeting · Feature #1 會議速記自動化
 * ==========================================================
 * 流程:
 *   1. 選音檔(m4a/mp3/wav)
 *   2. 選 project(選配)
 *   3. 上傳 → /memory/transcribe · 回 meeting_id
 *   4. 每 3 秒 poll /memory/meetings/{id} 看 status
 *   5. status=done → 顯示結構化紀錄
 *   6. 一鍵「推到 Handoff」
 */
import { authFetch } from "./auth.js";
import { escapeHtml } from "./util.js";
import { toast } from "./toast.js";

const BASE = "/api-accounting";

export const meeting = {
  _currentId: null,
  _pollTimer: null,

  async openUpload() {
    // 建 modal · 簡單版:上傳 + project 選
    const root = document.getElementById("modal-root") || document.body;
    const modal = document.createElement("div");
    modal.className = "modal2-overlay";
    modal.innerHTML = `
      <div class="modal2-box" style="max-width: 480px">
        <div class="modal2-header">🎤 會議速記 · 上傳音檔</div>
        <form id="meeting-upload-form" class="modal2-form">
          <label>音檔(m4a / mp3 / wav · ≤ 25MB)
            <input type="file" name="audio" accept="audio/*,video/mp4" required>
          </label>
          <label>專案 ID(選填 · 完成後可一鍵推到 Handoff)
            <input type="text" name="project_id" placeholder="留空也 OK">
          </label>
          <div style="font-size:12px; color: var(--text-tertiary); margin:8px 0">
            ⏱ 處理時間約 音檔長度 × 0.3(10 分鐘音檔 → 3 分鐘)<br>
            🔒 PDPA · 處理完音檔自動刪 · 只留逐字稿 + 結構化 JSON
          </div>
          <div class="modal2-actions">
            <button type="button" data-cancel>取消</button>
            <button type="submit" class="primary">開始 · Whisper + Haiku</button>
          </div>
        </form>
      </div>
    `;
    root.appendChild(modal);

    const form = modal.querySelector("form");
    modal.querySelector("[data-cancel]").addEventListener("click", () => modal.remove());
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const fd = new FormData(form);
      try {
        const r = await authFetch(`${BASE}/memory/transcribe`, {
          method: "POST",
          body: fd,
        });
        if (!r.ok) {
          const err = await r.json().catch(() => ({}));
          toast.error(`上傳失敗:${err.detail || r.status}`);
          return;
        }
        const body = await r.json();
        toast.success(`已上傳 ${body.size_mb}MB · 處理中...`);
        modal.remove();
        this._currentId = body.meeting_id;
        this._startPolling();
      } catch (e) {
        toast.error(`網路錯:${String(e)}`);
      }
    });
  },

  _startPolling() {
    if (this._pollTimer) clearInterval(this._pollTimer);
    let attempts = 0;
    this._pollTimer = setInterval(async () => {
      attempts++;
      if (attempts > 60) {  // 3 分鐘
        clearInterval(this._pollTimer);
        toast.error("超時 · 到「使用教學 → API Key」看 OpenAI 是否有效");
        return;
      }
      try {
        const r = await authFetch(`${BASE}/memory/meetings/${this._currentId}`);
        if (!r.ok) return;
        const body = await r.json();
        if (body.status === "done") {
          clearInterval(this._pollTimer);
          this._showResult(body);
        } else if (body.status === "failed") {
          clearInterval(this._pollTimer);
          toast.error(`處理失敗:${body.error || "未知錯"}`);
        }
      } catch {}
    }, 3000);
  },

  _showResult(body) {
    const s = body.structured || {};
    const root = document.getElementById("modal-root") || document.body;
    const modal = document.createElement("div");
    modal.className = "modal2-overlay";
    modal.innerHTML = `
      <div class="modal2-box" style="max-width:640px; max-height:80vh; overflow-y:auto">
        <div class="modal2-header">✅ 會議紀錄完成</div>
        <h3 style="margin:0 0 8px">${escapeHtml(s.title || "(未命名會議)")}</h3>
        ${s.attendees?.length ? `
          <p style="color:var(--text-secondary); font-size:13px">
            👥 與會:${s.attendees.map(escapeHtml).join(", ")}
          </p>
        ` : ""}

        ${s.decisions?.length ? `
          <h4>📌 決議</h4>
          <ul>${s.decisions.map(d => `<li>${escapeHtml(d)}</li>`).join("")}</ul>
        ` : ""}

        ${s.action_items?.length ? `
          <h4>✓ 待辦</h4>
          <ul>
            ${s.action_items.map(a => `
              <li>
                <b>${escapeHtml(a.who || "?")}</b> · ${escapeHtml(a.what || "")}
                ${a.due ? ` <span style="color:var(--red)">(期限 ${escapeHtml(a.due)})</span>` : ""}
              </li>
            `).join("")}
          </ul>
        ` : ""}

        ${s.key_numbers?.length ? `
          <h4>💰 關鍵數字</h4>
          <ul>${s.key_numbers.map(n => `<li><b>${escapeHtml(n.label)}</b>:${escapeHtml(n.value)}</li>`).join("")}</ul>
        ` : ""}

        ${s.next_meeting ? `
          <p><b>📅 下次會議:</b> ${escapeHtml(s.next_meeting)}</p>
        ` : ""}

        <details style="margin-top:16px">
          <summary style="cursor:pointer; color:var(--text-tertiary); font-size:12px">
            逐字稿 (${body.transcript_length} 字)
          </summary>
          <pre style="white-space:pre-wrap; font-size:11px; color:var(--text-secondary); max-height:200px; overflow-y:auto; background:var(--surface-2); padding:8px; border-radius:6px">${escapeHtml(body.transcript_preview)}</pre>
        </details>

        <div class="modal2-actions">
          <button type="button" data-close>關閉</button>
          ${body.project_id ? `<button type="button" class="primary" data-push>推到 Handoff</button>` : ""}
        </div>
      </div>
    `;
    root.appendChild(modal);
    modal.querySelector("[data-close]").addEventListener("click", () => modal.remove());
    modal.querySelector("[data-push]")?.addEventListener("click", async () => {
      try {
        const r = await authFetch(
          `${BASE}/memory/meetings/${this._currentId}/push-to-handoff`,
          { method: "POST" }
        );
        if (!r.ok) {
          const err = await r.json().catch(() => ({}));
          toast.error(`推失敗:${err.detail || r.status}`);
          return;
        }
        const body = await r.json();
        toast.success(`已推 ${body.next_actions_count} 項待辦到 Handoff`);
        modal.remove();
      } catch (e) {
        toast.error(`網路錯:${String(e)}`);
      }
    });
  },
};
