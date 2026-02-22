import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // Asegurar que los archivos PWA se copien al build
        assetFileNames: (assetInfo) => {
          if (assetInfo.name === 'manifest.json' || assetInfo.name === 'sw.js') {
            return '[name][extname]';
          }
          return 'assets/[name]-[hash][extname]';
        }
      }
    }
  }
})
