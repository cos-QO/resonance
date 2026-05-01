// Quick status check: is the bridge running and what does its session contain?
const bridgeUrl = process.env.UI_DOM_INSPECTOR_BRIDGE_URL || "http://127.0.0.1:47771";

try {
  const res = await fetch(`${bridgeUrl}/health`, { signal: AbortSignal.timeout(2000) });
  const data = await res.json();
  console.log("Bridge: connected");
  console.log(`  Port:        ${data.port}`);
  console.log(`  Has session: ${data.hasSession}`);
  console.log(`  Has snapshot:${data.hasSnapshot}`);
  if (data.pinnedTab) {
    console.log(`  Pinned tab:  ${data.pinnedTab.url}`);
  } else {
    console.log("  Pinned tab:  none");
  }
} catch {
  console.log("Bridge: not running");
  console.log("  Start with: npm run bridge");
  console.log("  Or run /qo-ui-inspector-setup in Claude Code to set up auto-start");
}
