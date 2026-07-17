import React, { useState } from 'react'
import { ThreadField, ArrowRight } from './Icons'
import { signup, oauthLoginUrl } from '../api'

export default function Signup({ onSuccess, onGoToLogin }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const submit = async () => {
    if (!email.trim() || password.length < 8 || isLoading) return
    setIsLoading(true)
    setError('')
    try {
      await signup(email.trim(), password)
      onSuccess()
    } catch (e) {
      setError(e.message || 'Signup failed')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="h-screen w-full bg-(--bg-base) text-(--text-primary) font-mono flex flex-col justify-between p-4 overflow-hidden text-xs select-none animate-fade-in">
      <header className="flex items-center justify-between border-b border-(--border-hairline) pb-2 shrink-0">
        <span className="font-bold tracking-tight text-xs">Davable</span>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center max-w-xs w-full mx-auto space-y-4 my-auto">
        <div className="w-full text-center space-y-1 relative flex flex-col items-center">
          <ThreadField className="opacity-10 w-8 h-8 mb-1 animate-pulse" />
          <h1 className="text-sm font-bold text-balance">Create an account.</h1>
        </div>

        <div className="w-full bg-(--bg-surface) border border-(--border-hairline) rounded p-2.5 space-y-2">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="you@example.com"
            autoComplete="email"
            className="w-full bg-(--bg-base) border border-(--border-hairline) rounded px-2 py-1.5 text-xs font-mono outline-none focus:border-(--accent-gold) placeholder:text-(--text-secondary) disabled:opacity-50"
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Password (min 8 characters)"
            autoComplete="new-password"
            className="w-full bg-(--bg-base) border border-(--border-hairline) rounded px-2 py-1.5 text-xs font-mono outline-none focus:border-(--accent-gold) placeholder:text-(--text-secondary) disabled:opacity-50"
          />

          {error && <p className="text-[10px] text-(--accent-gold)">{error}</p>}

          <button
            onClick={submit}
            disabled={!email.trim() || password.length < 8 || isLoading}
            className="w-full flex items-center justify-center gap-1.5 bg-(--accent-gold) disabled:opacity-20 text-[#1B1918] font-medium text-[11px] px-2.5 py-1.5 rounded transition-all active:scale-[0.98]"
          >
            <span>{isLoading ? 'Creating account' : 'Create account'}</span>
            <ArrowRight className={`w-3 h-3 stroke-[2.5] ${isLoading ? 'animate-bounce' : ''}`} />
          </button>

          <div className="flex items-center gap-2 py-0.5">
            <div className="flex-1 h-px bg-(--border-hairline)" />
            <span className="text-[9px] text-(--text-secondary) uppercase tracking-wider">or</span>
            <div className="flex-1 h-px bg-(--border-hairline)" />
          </div>

          <a
            href={oauthLoginUrl('google')}
            className="w-full flex items-center justify-center gap-1.5 border border-(--border-hairline) hover:border-(--text-secondary) text-(--text-primary) text-[11px] px-2.5 py-1.5 rounded transition-all"
          >
            Continue with Google
          </a>
          <a
            href={oauthLoginUrl('github')}
            className="w-full flex items-center justify-center gap-1.5 border border-(--border-hairline) hover:border-(--text-secondary) text-(--text-primary) text-[11px] px-2.5 py-1.5 rounded transition-all"
          >
            Continue with GitHub
          </a>
        </div>

        <button
          onClick={onGoToLogin}
          className="text-[10px] text-(--text-secondary) hover:text-(--text-primary) transition-colors"
        >
          Already have an account? <span className="text-(--accent-gold)">Sign in</span>
        </button>
      </main>

      <style>{`
        @keyframes containerReveal {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in { animation: containerReveal 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
      `}</style>
    </div>
  )
}
