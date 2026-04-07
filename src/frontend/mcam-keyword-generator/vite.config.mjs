import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '../../..')

export default defineConfig({
  plugins: [tailwindcss(), react()],
  server: {
    fs: { allow: [repoRoot] },
    proxy: {
      '/predict': 'https://stilliform-celine-plaintively.ngrok-free.dev',
    },
  },
})
