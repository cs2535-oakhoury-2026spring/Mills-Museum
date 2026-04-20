/**
 * Vite configuration for the React frontend.
 *
 * Vite is the development server and build tool for the browser app.
 * This file explains:
 * - which plugins to use
 * - which extra folders the dev server is allowed to read from
 * - where `/predict` requests should be proxied during local development
 */
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// Recreate `__dirname` because ESM modules do not provide it automatically.
const __dirname = path.dirname(fileURLToPath(import.meta.url))
// Allow the frontend to reference files from the wider repository when needed.
const repoRoot = path.resolve(__dirname, '../../..')

export default defineConfig({
  // React handles JSX; Tailwind handles CSS utility generation.
  plugins: [tailwindcss(), react()],
  server: {
    // Permit the dev server to read files from the repository root as well.
    fs: { allow: [repoRoot] },
    proxy: {
      // During local development, browser calls to `/predict` are forwarded
      // to the currently configured backend endpoint so the frontend can act
      // as if the API were hosted on the same origin.
      '/predict': 'https://stilliform-celine-plaintively.ngrok-free.dev',
    },
  },
})
