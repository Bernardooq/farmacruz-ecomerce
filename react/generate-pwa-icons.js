/**
 * Script para generar iconos PWA desde el favicon
 * Ejecutar: node generate-pwa-icons.js
 * 
 * Requiere: npm install sharp
 */

import sharp from 'sharp';
import { mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import { join } from 'path';

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const inputFile = './public/favicon.webp';
const outputDir = './public/pwa-icons';

async function generateIcons() {
  try {
    // Crear directorio si no existe
    if (!existsSync(outputDir)) {
      await mkdir(outputDir, { recursive: true });
      console.log('Carpeta pwa-icons creada');
    }

    // Verificar que existe el favicon
    if (!existsSync(inputFile)) {
      console.error('Error: No se encontró favicon.webp en public/');
      console.log('Coloca tu logo/favicon en public/favicon.webp y vuelve a ejecutar');
      process.exit(1);
    }

    console.log('🎨 Generando iconos PWA...\n');

    // Generar cada tamaño
    for (const size of sizes) {
      const outputFile = join(outputDir, `icon-${size}x${size}.png`);
      
      await sharp(inputFile)
        .resize(size, size, {
          fit: 'contain',
          background: { r: 255, g: 255, b: 255, alpha: 0 }
        })
        .png()
        .toFile(outputFile);
      
      console.log(`Generado: icon-${size}x${size}.png`);
    }

    console.log('\n¡Todos los iconos generados exitosamente!');
    console.log('Ubicación:', outputDir);
    console.log('\nSiguiente paso: npm run build');

  } catch (error) {
    console.error('Error generando iconos:', error.message);
    process.exit(1);
  }
}

generateIcons();
