import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const required = [
  "extension/manifest.json",
  "extension/service-worker.js",
  "extension/content-script.js",
  "bridge/server.js",
  "mcp-server/server.js"
];

let ok = true;

for (const rel of required) {
  const full = path.join(root, rel);
  if (!fs.existsSync(full)) {
    console.error(`missing: ${rel}`);
    ok = false;
  }
}

if (!ok) {
  process.exit(1);
}

console.log("ui-dom-inspector setup looks present");
