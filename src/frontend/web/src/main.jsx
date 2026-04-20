/**
 * Vite + React entry point.
 *
 * Mounts `App` into `#root` from `index.html`. Global styles load here (Tailwind
 * build + museum-specific overrides) so every route/phase shares the same
 * design tokens. `StrictMode` runs extra checks in development only; it does
 * not change production behavior.
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/tailwind.css'
import './styles/app-overrides.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
