/**
 * Browser entrypoint for the React application.
 *
 * This file does only three things:
 * 1. Load the root React component.
 * 2. Load the global CSS files the app depends on.
 * 3. Mount the app into the `<div id="root">` created in `index.html`.
 *
 * `React.StrictMode` is a development helper from React. It does not change
 * the visible UI, but it helps catch mistakes while building the app.
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/tailwind.css'
import './styles/theme.css'
import './styles/app-overrides.css'

// Find the one HTML element that will hold the entire React application.
ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
