const input = document.getElementById("base-url");
const save = document.getElementById("save");
const URL_KEY = "company_ai_base_url";
const LEGACY_URL_KEY = ["cheng", "fu_base_url"].join("");

// 載入既有設定
chrome.storage.sync.get([URL_KEY, LEGACY_URL_KEY]).then((values) => {
  input.value = values[URL_KEY] || values[LEGACY_URL_KEY] || "http://localhost";
});

save.addEventListener("click", async () => {
  const url = input.value.trim().replace(/\/$/, "");
  if (!url) return;
  await chrome.storage.sync.set({ [URL_KEY]: url });
  save.textContent = "✅ 已儲存";
  setTimeout(() => save.textContent = "儲存", 1500);
});
