import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const pidFile = path.join(__dirname, "..", "bridge", "bridge.pid");

if (!fs.existsSync(pidFile)) {
  console.log("No bridge.pid found — bridge may not have been started with npm run bridge:bg");
  process.exit(0);
}

const pid = parseInt(fs.readFileSync(pidFile, "utf8").trim(), 10);
if (isNaN(pid)) {
  console.error("Invalid PID in bridge.pid");
  process.exit(1);
}

try {
  process.kill(pid, "SIGTERM");
  fs.unlinkSync(pidFile);
  console.log(`Bridge process ${pid} stopped.`);
} catch (err) {
  if (err.code === "ESRCH") {
    console.log(`Bridge process ${pid} was not running. Cleaning up pid file.`);
    fs.unlinkSync(pidFile);
  } else {
    console.error(`Failed to stop bridge: ${err.message}`);
    process.exit(1);
  }
}
