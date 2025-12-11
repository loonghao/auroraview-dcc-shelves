/**
 * Settings window entry point.
 * This is a separate entry for the settings window that can be opened independently.
 */
import React from 'react'
import ReactDOM from 'react-dom/client'
import { SettingsWindow } from './windows/SettingsWindow'
import './i18n'
import './style.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <SettingsWindow />
  </React.StrictMode>
)
