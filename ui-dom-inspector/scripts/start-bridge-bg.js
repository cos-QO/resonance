// Start the bridge as a background process with logging and PID tracking.
// Used by the /qo-ui-inspector-setup command and npm run bridge:bg.
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.join(__dirname, "..");
const pidFile = path.join(rootDir, "bridge", "bridge.pid");
const logFile = path.join(rootDir, "bridge", "bridge.log");

// Check if already running
if (fs.existsSync(pidFile)) {
  const pid = parseInt(fs.readFileSync(pidFile, "utf8").trim(), 10);
  try {
    process.kill(pid, 0); // signal 0 = check existence only
    console.log(`Bridge already running (PID ${pid}). Use npm run status to verify.`);
    process.exit(0);
  } catch {
    // Process not found — stale pid file, continue to start
    fs.unlinkSync(pidFile);
  }
}

const logStream = fs.openSync(logFile, "a");
const child = spawn("node", [path.join(rootDir, "bridge", "server.js")], {
  detached: true,
  stdio: ["ignore", logStream, logStream],
  cwd: rootDir
});

child.unref();
fs.writeFileSync(pidFile, String(child.pid));
console.log(`Bridge started in background (PID ${child.pid})`);
console.log(`Log: ${logFile}`);

// Give it a moment then check health
await new Promise((r) => setTimeout(r, 1500));
try {
  const res = await fetch("http://127.0.0.1:47771/health", {
    signal: AbortSignal.timeout(2000)
  });
  const data = await res.json();
  if (data.ok) {
    console.log("Bridge health: OK");
  } else {
    console.warn("Bridge responded but health check unexpected:", data);
  }
} catch {
  console.error("Bridge did not respond after start. Check the log:");
  console.error(`  tail -20 ${logFile}`);
  process.exit(1);
}
