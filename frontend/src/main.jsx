import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { GoogleOAuthProvider } from '@react-oauth/google'
import App from './App.jsx'

// Only wrap in GoogleOAuthProvider when a Client ID is actually configured,
// so the app still runs (minus the Google button) if someone hasn't set up
// Google Sign-In yet -- see GOOGLE_LOGIN_SETUP.md.
const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID

const root = (
  <StrictMode>
    <App />
  </StrictMode>
)

createRoot(document.getElementById('root')).render(
  googleClientId ? (
    <GoogleOAuthProvider clientId={googleClientId}>{root}</GoogleOAuthProvider>
  ) : (
    root
  ),
)
