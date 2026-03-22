import sharp from "sharp";
import { mkdirSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outDir = join(__dirname, "..", "public", "icons");
mkdirSync(outDir, { recursive: true });

// Generate a simple "F" icon on dark background
async function generateIcon(size, filename) {
  const fontSize = Math.round(size * 0.6);
  const svg = `<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
    <rect width="${size}" height="${size}" rx="${Math.round(size * 0.15)}" fill="#0a0a0a"/>
    <text x="50%" y="54%" dominant-baseline="middle" text-anchor="middle"
      font-family="system-ui, sans-serif" font-weight="bold" font-size="${fontSize}" fill="#fafafa">
      F
    </text>
  </svg>`;
  await sharp(Buffer.from(svg)).png().toFile(join(outDir, filename));
  console.log(`Generated ${filename} (${size}x${size})`);
}

await generateIcon(192, "icon-192x192.png");
await generateIcon(512, "icon-512x512.png");
await generateIcon(180, "apple-touch-icon.png");
console.log("All icons generated.");
