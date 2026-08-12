import { CheckCircle2, AlertCircle, Info, Moon, Sun, Trash2 } from 'lucide-react'
import { checkHealth } from '../utils/api'

export default function ChatHeader({ isDark, toggleDark, isHealthy, health, setHealth, showInfo, setShowInfo, clearChat }) {
  return (
    <header className="glass-strong px-4 py-3 flex items-center justify-between shadow-sm relative z-10">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 bg-gradient-to-br from-teal-500 to-medical-600 rounded-xl flex items-center justify-center shadow-sm animate-electric-glow">
          <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3" />
            <path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4" />
            <circle cx="20" cy="10" r="2" />
          </svg>
        </div>
        <div>
          <h1 className="font-bold text-slate-800 dark:text-slate-100 text-base leading-tight">
            MediAssist
          </h1>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            Healthcare AI Assistant
          </p>
        </div>
      </div>

      <div className="flex items-center gap-1">
        <button
          onClick={() => checkHealth().then(setHealth)}
          className={`flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-xs transition-colors ${
            isHealthy
              ? 'text-green-600 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-950'
              : 'text-amber-600 dark:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-950'
          }`}
          title={isHealthy ? `${health?.total_documents} docs indexed` : 'Backend status'}
        >
          {isHealthy ? (
            <CheckCircle2 className="w-4 h-4" />
          ) : (
            <AlertCircle className="w-4 h-4" />
          )}
          <span className="hidden sm:inline">
            {isHealthy ? 'Online' : 'Connecting...'}
          </span>
        </button>

        <button
          onClick={toggleDark}
          className="p-2 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
          title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>

        <button
          onClick={() => setShowInfo(!showInfo)}
          className="p-2 text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
          title="Medical disclaimer"
          aria-label="Toggle medical disclaimer"
        >
          <Info className="w-4 h-4" />
        </button>

        <button
          onClick={clearChat}
          className="p-2 text-slate-400 dark:text-slate-500 hover:text-red-500 dark:hover:text-red-400 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors"
          title="Clear chat (Ctrl+L)"
          aria-label="Clear chat"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </header>
  )
}
