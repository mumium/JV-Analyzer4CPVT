// Development-only: npm install --no-save sharp, then node packaging/generate_icons.cjs.
// Render each ICO frame directly from vector artwork instead of scaling a bitmap.
const fs = require('node:fs');
const path = require('node:path');
const sharp = require('sharp');
const assets = path.resolve(__dirname, '../assets');
const sizes = [16, 20, 24, 28, 32, 40, 48, 56, 64, 96, 128, 256];

(async () => {
  const frames = await Promise.all(sizes.map(size => sharp(path.join(assets,
    size <= 24 ? 'logo-small.svg' : 'logo.svg'), { density: 384 })
    .resize(size, size).png().toBuffer()));
  const header = Buffer.alloc(6 + 16 * frames.length);
  header.writeUInt16LE(1, 2);
  header.writeUInt16LE(frames.length, 4);
  let offset = header.length;
  frames.forEach((frame, i) => {
    const entry = 6 + i * 16;
    header[entry] = header[entry + 1] = sizes[i] === 256 ? 0 : sizes[i];
    header.writeUInt16LE(1, entry + 4);
    header.writeUInt16LE(32, entry + 6);
    header.writeUInt32LE(frame.length, entry + 8);
    header.writeUInt32LE(offset, entry + 12);
    offset += frame.length;
  });
  fs.writeFileSync(path.join(assets, 'logo.ico'), Buffer.concat([header, ...frames]));
  await sharp(path.join(assets, 'logo.svg'), { density: 384 }).resize(512, 512)
    .png().toFile(path.join(assets, 'logo.png'));
  console.log(`Generated logo.png and ${frames.length} native ICO resolutions.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
