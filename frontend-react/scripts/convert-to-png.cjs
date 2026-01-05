/**
 * Generate favicon variants and OG image from original favicon.ico
 * Run with: node scripts/convert-to-png.cjs
 */

const sharp = require('sharp');
const decodeIco = require('decode-ico');
const fs = require('fs');
const path = require('path');

const PUBLIC_DIR = path.join(__dirname, '../public');

// Brand colors (matching the app theme)
const COLORS = {
  background: '#09090b',
  primary: '#8b5cf6',
  text: '#fafafa',
  textMuted: '#a1a1aa'
};

async function main() {
  console.log('Generating assets from favicon.ico...\n');

  const faviconPath = path.join(PUBLIC_DIR, 'favicon.ico');

  if (!fs.existsSync(faviconPath)) {
    console.error('Error: favicon.ico not found in public/');
    process.exit(1);
  }

  try {
    // Read and decode the ICO file
    const icoBuffer = fs.readFileSync(faviconPath);
    const images = decodeIco(icoBuffer);

    if (!images || images.length === 0) {
      throw new Error('No images found in favicon.ico');
    }

    // Find the largest image in the ICO
    const largestImage = images.reduce((prev, current) =>
      (prev.width > current.width) ? prev : current
    );

    console.log(`Found ${images.length} images in ICO, using ${largestImage.width}x${largestImage.height}`);

    // Convert the raw RGBA data to a sharp-compatible buffer
    const iconSharp = sharp(Buffer.from(largestImage.data), {
      raw: {
        width: largestImage.width,
        height: largestImage.height,
        channels: 4
      }
    });

    // 32x32 favicon
    await iconSharp
      .clone()
      .resize(32, 32)
      .png()
      .toFile(path.join(PUBLIC_DIR, 'favicon-32x32.png'));
    console.log('✓ Created favicon-32x32.png');

    // 16x16 favicon
    await iconSharp
      .clone()
      .resize(16, 16)
      .png()
      .toFile(path.join(PUBLIC_DIR, 'favicon-16x16.png'));
    console.log('✓ Created favicon-16x16.png');

    // 180x180 Apple Touch Icon with violet background
    const iconBuffer = await iconSharp
      .clone()
      .resize(120, 120)
      .png()
      .toBuffer();

    await sharp({
      create: {
        width: 180,
        height: 180,
        channels: 4,
        background: { r: 139, g: 92, b: 246, alpha: 1 } // violet-500
      }
    })
      .composite([{
        input: iconBuffer,
        top: 30,
        left: 30
      }])
      .png()
      .toFile(path.join(PUBLIC_DIR, 'apple-touch-icon.png'));
    console.log('✓ Created apple-touch-icon.png (180x180)');

    // Create OG Image (1200x630)
    const ogIconBuffer = await iconSharp
      .clone()
      .resize(140, 140)
      .png()
      .toBuffer();

    const ogWidth = 1200;
    const ogHeight = 630;

    // Create SVG for text overlay
    const textOverlay = Buffer.from(`
      <svg width="${ogWidth}" height="${ogHeight}">
        <style>
          .title { fill: ${COLORS.text}; font-size: 72px; font-family: Arial, sans-serif; font-weight: bold; }
          .tagline { fill: ${COLORS.textMuted}; font-size: 28px; font-family: Arial, sans-serif; }
          .url { fill: ${COLORS.textMuted}; font-size: 18px; font-family: Arial, sans-serif; }
        </style>
        <text x="50%" y="370" text-anchor="middle" class="title">Ception</text>
        <text x="50%" y="430" text-anchor="middle" class="tagline">Discover Your Team Archetype</text>
        <text x="50%" y="590" text-anchor="middle" class="url">personality.ception.one</text>
      </svg>
    `);

    await sharp({
      create: {
        width: ogWidth,
        height: ogHeight,
        channels: 4,
        background: { r: 9, g: 9, b: 11, alpha: 1 } // #09090b
      }
    })
      .composite([
        {
          input: ogIconBuffer,
          top: 100,
          left: Math.floor((ogWidth - 140) / 2)
        },
        {
          input: textOverlay,
          top: 0,
          left: 0
        }
      ])
      .png()
      .toFile(path.join(PUBLIC_DIR, 'og-image.png'));

    const ogStats = fs.statSync(path.join(PUBLIC_DIR, 'og-image.png'));
    console.log(`✓ Created og-image.png (${Math.round(ogStats.size / 1024)}KB)`);

    // Clean up old SVG files
    const svgFiles = ['og-image.svg', 'favicon-32x32.svg', 'favicon-16x16.svg', 'apple-touch-icon.svg'];
    for (const svgFile of svgFiles) {
      const svgPath = path.join(PUBLIC_DIR, svgFile);
      if (fs.existsSync(svgPath)) {
        fs.unlinkSync(svgPath);
        console.log(`✓ Removed ${svgFile}`);
      }
    }

    console.log('\nDone! All assets generated from favicon.ico');

  } catch (err) {
    console.error('Error generating assets:', err.message);
    process.exit(1);
  }
}

main();
