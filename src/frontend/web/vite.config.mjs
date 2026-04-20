/**
 * Vite config for `src/frontend/web`.
 *
 * - `server.fs.allow`: the app imports the museum logo from outside this folder
 *   (`media/logo.png` under the repo root). Vite blocks arbitrary parent reads
 *   unless the repo root is explicitly allowed.
 * - `server.proxy`: optional dev-only shortcut so `/predict*` can hit a remote
 *   Colab/ngrok URL without changing `VITE_API_URL`. Update the target when your
 *   tunnel changes; production builds rely on `VITE_API_URL` in the client.
 */
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
