import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const distDir = path.resolve(__dirname, "..", "dist");
const proxyUrl = (process.env.VOTER_SERVICE_UPDATE_PROXY_URL || "").trim().replace(/\/+$/, "");
const allowMissing = process.env.ALLOW_MISSING_UPDATE_PROXY_CONFIG === "1";

if (!proxyUrl) {
  if (allowMissing) {
    console.log("skip feed rewrite: VOTER_SERVICE_UPDATE_PROXY_URL is not set");
    process.exit(0);
  }
  throw new Error("Missing required update proxy setting: VOTER_SERVICE_UPDATE_PROXY_URL");
}

if (!/^https?:\/\//.test(proxyUrl)) {
  throw new Error("VOTER_SERVICE_UPDATE_PROXY_URL must be http(s).");
}

function assertFeedRewritten(fileName, output) {
  if (!output.includes("/api/updates/assets/")) {
    throw new Error(`${fileName} was not rewritten to proxy asset URLs.`);
  }
  if (/github\.com|objects\.githubusercontent\.com/i.test(output)) {
    throw new Error(`${fileName} still contains a GitHub asset URL.`);
  }
}

function proxyAssetUrl(assetName) {
  return `${proxyUrl}/api/updates/assets/${encodeURIComponent(assetName)}`;
}

function rewriteFeed(fileName) {
  const filePath = path.join(distDir, fileName);
  if (!fs.existsSync(filePath)) return;
  const input = fs.readFileSync(filePath, "utf8");
  const output = input.split(/\r?\n/).map((line) => {
    const match = line.match(/^(\s*(?:-\s*)?)(url|path):\s*(.+?)\s*$/);
    if (!match) return line;
    const [, indent, key, raw] = match;
    const value = raw.trim().replace(/^['"]|['"]$/g, "");
    const assetName = decodeURIComponent(
      path.basename(new URL(value, "https://placeholder.invalid/").pathname),
    );
    if (!assetName || /\.(ya?ml)$/i.test(assetName)) return line;
    return `${indent}${key}: ${proxyAssetUrl(assetName)}`;
  }).join("\n");
  assertFeedRewritten(fileName, output);
  fs.writeFileSync(filePath, output);
  console.log(`${fileName} rewritten to proxy asset URLs`);
}

rewriteFeed("latest.yml");
rewriteFeed("latest-mac.yml");
