import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Landing from './pages/Landing.tsx'
import InterviewsPage from './pages/Interviewspage.tsx'
import Interviewer from './pages/Interviewer.tsx'
import { ClerkProvider } from '@clerk/clerk-react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY

if (!PUBLISHABLE_KEY) {
  throw new Error('Missing Clerk Publishable Key')
}

createRoot(document.getElementById('root')!).render(

    <StrictMode>
      <BrowserRouter>
        <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignInUrl="/interviews" afterSignOutUrl="/">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/interviews" element={<InterviewsPage />} />
            <Route path="/interviewer" element={<Interviewer />} />
          </Routes>
        </ClerkProvider>
      </BrowserRouter>
    </StrictMode>
  ,
)
