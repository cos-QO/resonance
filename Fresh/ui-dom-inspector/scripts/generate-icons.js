import sharp from "sharp";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const svgPath = resolve(__dirname, "../extension/icon.svg");
const svgBuffer = readFileSync(svgPath);

const sizes = [16, 32, 48, 128];

for (const size of sizes) {
  const outPath = resolve(__dirname, `../extension/icon-${size}.png`);
  await sharp(svgBuffer)
    .resize(size, size)
    .png()
    .toFile(outPath);
  console.log(`Generated icon-${size}.png`);
}
