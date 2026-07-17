import React, { useEffect, useRef, useState } from 'react'
import { ThreadField, ArrowRight } from './Icons'
import { listConversations } from '../api'

function timeAgo(isoString) {
  const seconds = Math.floor((Date.now() - new Date(isoString).getTime()) / 1000)
  if (seconds < 60) return 'just now'
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export default function Home({ onStart, onResume, onLogout }) {
  const [prompt, setPrompt] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [sessions, setSessions] = useState([])
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const textareaRef = useRef(null)

  useEffect(() => {
    listConversations()
      .then(setSessions)
      .catch(() => setSessions([]))
      .finally(() => setSessionsLoading(false))
  }, [])

  const submit = () => {
    const value = prompt.trim()
    if (!value || isLoading) return
    setIsLoading(true)
    onStart(value)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  const useStarter = (text) => {
    setPrompt(text)
    textareaRef.current?.focus()
  }

  return (
    <div className="h-screen w-full bg-(--bg-base) text-(--text-primary) font-mono flex flex-col justify-between p-4 overflow-hidden text-xs select-none animate-fade-in">
      <header className="flex items-center justify-between border-b border-(--border-hairline) pb-2 shrink-0">
        <span className="font-bold tracking-tight text-xs">Davable</span>
        {onLogout && (
          <button
            onClick={onLogout}
            className="text-(--text-secondary) hover:text-(--text-primary) transition-colors text-[10px] uppercase tracking-wider"
          >
            Log out
          </button>
        )}
      </header>

      <main className="flex-1 flex flex-col items-center justify-center max-w-md w-full mx-auto space-y-4 my-auto overflow-hidden">
        <div className="w-full text-center space-y-1 relative flex flex-col items-center shrink-0">
          <ThreadField className="opacity-10 w-8 h-8 mb-1 animate-pulse" />
          <h1 className="text-sm font-bold text-balance">
            Describe app to weave systems.
          </h1>
        </div>

        <div className="w-full bg-(--bg-surface) border border-(--border-hairline) rounded p-2 transition-all duration-200 focus-within:border-(--accent-gold) shrink-0">
          <textarea
            ref={textareaRef}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={2}
            disabled={isLoading}
            placeholder="Describe your idea..."
            className="w-full bg-transparent resize-none outline-none placeholder:text-(--text-secondary) text-xs p-1 disabled:opacity-50 min-h-10"
          />
          <div className="flex items-center justify-between pt-1.5 border-t border-(--border-hairline)/40 mt-1">
            <span className="text-[10px] text-(--text-secondary) px-1">
              {isLoading ? 'Compiling framework' : 'Ready'}
            </span>
            <button
              onClick={submit}
              disabled={!prompt.trim() || isLoading}
              className="flex items-center gap-1.5 bg-(--accent-gold) disabled:opacity-20 text-[#1B1918] font-medium text-[11px] px-2.5 py-1 rounded transition-all active:scale-[0.98]"
            >
              <span>{isLoading ? 'Weaving' : 'Execute'}</span>
              <ArrowRight className={`w-3 h-3 stroke-[2.5] ${isLoading ? 'animate-bounce' : ''}`} />
            </button>
          </div>
        </div>

        {!sessionsLoading && sessions.length > 0 && (
          <div className="w-full flex flex-col min-h-0">
            <span className="text-[10px] text-(--text-secondary) uppercase tracking-wider px-0.5 mb-1 shrink-0">
              Past sessions
            </span>
            <div className="overflow-y-auto space-y-1 thin-scroll pr-0.5">
              {sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => onResume(s.id)}
                  className="w-full text-left bg-(--bg-surface) border border-(--border-hairline) hover:border-(--accent-gold)/60 rounded px-2 py-1.5 transition-colors flex items-center gap-2"
                >
                  <span
                    className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                      s.status === 'complete' ? 'bg-(--accent-teal)' : 'bg-(--accent-gold)'
                    }`}
                  />
                  <span className="flex-1 truncate text-[11px] text-(--text-primary)">{s.original_prompt}</span>
                  <span className="text-[9px] text-(--text-secondary) shrink-0">{timeAgo(s.created_at)}</span>
                </button>
              ))}
            </div>
          </div>
        )}
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