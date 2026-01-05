import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { SpeedInsights } from '@vercel/speed-insights/react'
import './index.css'
import App from './App.jsx'
import PublicProfile from './components/PublicProfile.jsx'
import InsightsPage from './components/InsightsPage.jsx'
import ProfilePage from './components/ProfilePage.jsx'
import { AuthProvider } from './contexts/AuthContext'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<App />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/u/:username" element={<PublicProfile />} />
          <Route path="/insights/:archetypeId" element={<InsightsPage />} />
        </Routes>
        <SpeedInsights />
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
