import React, { useEffect, useState } from 'react'
import Home from './pages/Home'
import Conversation from './pages/Conversation'
import Login from './pages/Login'
import Signup from './pages/Signup'
import { consumeOAuthTokensFromUrl, isLoggedIn, logout } from './api'



function GlobalStyles() {
  return (
    <style>{`
      @import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,500;0,9..144,600;1,9..144,500&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

      :root {
        --bg-base: #1B1918;
        --bg-surface: #242220;
        --bg-surface-2: #2D2A27;
        --border-hairline: #3A3633;
        --text-primary: #F3EDE3;
        --text-secondary: #A89E92;
        --accent-gold: #E3A33C;
        --accent-teal: #5B9C8A;
      }

      .font-display { font-family: 'Fraunces', serif; }
      .font-body { font-family: 'Inter', sans-serif; }
      .font-mono { font-family: 'JetBrains Mono', monospace; }

      @keyframes thread-drift {
        0%, 100% { transform: translateX(0); }
        50% { transform: translateX(14px); }
      }
      @keyframes weave-pulse {
        0%, 100% { opacity: .3; }
        50% { opacity: .9; }
      }
      @keyframes step-reveal {
        from { opacity: 0; transform: translateY(4px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .animate-thread { animation: thread-drift 9s ease-in-out infinite; }
      .animate-weave-pulse { animation: weave-pulse 1.6s ease-in-out infinite; }
      .animate-step-reveal { animation: step-reveal .35s ease-out forwards; }

      @media (prefers-reduced-motion: reduce) {
        .animate-thread, .animate-weave-pulse, .animate-step-reveal { animation: none !important; }
      }

      ::selection { background: var(--accent-gold); color: #1B1918; }

      .thin-scroll::-webkit-scrollbar { width: 6px; height: 6px; }
      .thin-scroll::-webkit-scrollbar-track { background: transparent; }
      .thin-scroll::-webkit-scrollbar-thumb { background: var(--border-hairline); border-radius: 4px; }
    `}</style>
  )
}

function App() {
  // OAuth redirects land here with ?access=&refresh= on the URL - resolve
  // that synchronously on first render, before deciding which page to show.
  const [oauthResult] = useState(() => consumeOAuthTokensFromUrl())
  const [page, setPage] = useState(() => (isLoggedIn() ? 'home' : 'login'))
  const [initialPrompt, setInitialPrompt] = useState('')
  const [resumeConversationId, setResumeConversationId] = useState(null)

  useEffect(() => {
    if (oauthResult.success) setPage('home')
  }, [oauthResult])

  const startWeaving = (prompt) => {
    setInitialPrompt(prompt)
    setResumeConversationId(null)
    setPage('conversation')
  }

  const resumeSession = (conversationId) => {
    setInitialPrompt('')
    setResumeConversationId(conversationId)
    setPage('conversation')
  }

  const goHome = () => {
    setPage('home')
    setInitialPrompt('')
    setResumeConversationId(null)
  }

  const handleLogout = () => {
    logout()
    setPage('login')
  }

  // Passed down to Conversation so an expired/invalid token bounces back
  // to login instead of the chat silently failing forever.
  const handleAuthError = () => {
    logout()
    setPage('login')
  }

  return (
    <>
      <GlobalStyles />
      {page === 'login' && (
        <Login onSuccess={() => setPage('home')} onGoToSignup={() => setPage('signup')} />
      )}
      {page === 'signup' && (
        <Signup onSuccess={() => setPage('home')} onGoToLogin={() => setPage('login')} />
      )}
      {page === 'home' && <Home onStart={startWeaving} onResume={resumeSession} onLogout={handleLogout} />}
      {page === 'conversation' && (
        <Conversation
          initialPrompt={initialPrompt}
          resumeConversationId={resumeConversationId}
          onBack={goHome}
          onAuthError={handleAuthError}
        />
      )}
    </>
  )
}

export default App