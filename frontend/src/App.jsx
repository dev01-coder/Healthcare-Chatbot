import React, { useState, useRef, useEffect, useCallback } from 'react'
import { AlertCircle } from 'lucide-react'
import { ToastProvider, useToast } from './components/Toast'
import NeuralBackground from './components/NeuralBackground'
import ChatHeader from './components/ChatHeader'
import ChatInput from './components/ChatInput'
import EmptyState from './components/EmptyState'
import MessageList from './components/MessageList'
import useDarkMode from './hooks/useDarkMode'
import { streamMessage, checkHealth } from './utils/api'

const STORAGE_KEY = 'mediassist-chat-history'

function loadHistory() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed) && parsed.length > 0) return parsed
    }
  } catch {}
  return null
}

function saveHistory(messages) {
  try {
    if (messages.length > 0) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  } catch {}
}

function ErrorFallback({ error, reset }) {
  return (
    <div className="flex items-center justify-center h-screen bg-slate-50 dark:bg-slate-900 p-8">
      <div className="text-center max-w-md glass-strong rounded-2xl p-8 shadow-xl">
        <div className="w-16 h-16 bg-red-100 dark:bg-red-900/50 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-8 h-8 text-red-500 dark:text-red-400" />
        </div>
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-2">
          Something went wrong
        </h2>
        <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
          {error?.message || 'An unexpected error occurred'}
        </p>
        <button
          onClick={reset}
          className="px-5 py-2.5 bg-medical-600 text-white rounded-xl text-sm font-medium hover:bg-medical-700 active:bg-medical-800 transition-colors shadow-sm"
        >
          Reload Page
        </button>
      </div>
    </div>
  )
}

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorFallback
          error={this.state.error}
          reset={() => window.location.reload()}
        />
      )
    }
    return this.props.children
  }
}

function AppContent() {
  const [messages, setMessages] = useState(() => loadHistory() || [])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [health, setHealth] = useState(null)
  const [showInfo, setShowInfo] = useState(false)
  const [isDark, toggleDark] = useDarkMode()
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)
  const abortRef = useRef(null)
  const toast = useToast()

  useEffect(() => {
    saveHistory(messages)
  }, [messages])

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  useEffect(() => {
    checkHealth().then(setHealth)
  }, [])

  const getHistory = () =>
    messages
      .map(m => ({ role: m.role, content: m.content }))
      .slice(-10)

  const handleSend = useCallback(async (text = null) => {
    const messageText = (text || input).trim()
    if (!messageText || loading) return

    setInput('')
    setLoading(true)

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, userMsg])

    const assistantPlaceholder = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      streaming: true,
      sources: [],
      emergency: null,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, assistantPlaceholder])

    const controller = new AbortController()
    abortRef.current = controller

    try {
      let fullText = ''
      let sources = []
      let emergency = null
      const history = getHistory()

      for await (const chunk of streamMessage(messageText, history, controller.signal)) {
        if (chunk.type === 'emergency') {
          emergency = chunk.data
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { ...updated[updated.length - 1], emergency }
            return updated
          })
        } else if (chunk.type === 'sources') {
          sources = chunk.data
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { ...updated[updated.length - 1], sources }
            return updated
          })
        } else if (chunk.type === 'text') {
          fullText += chunk.data
          const currentText = fullText
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: currentText,
              streaming: true,
            }
            return updated
          })
        } else if (chunk.type === 'done') {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              streaming: false,
            }
            return updated
          })
        }
      }
    } catch (err) {
      if (controller.signal.aborted) {
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: updated[updated.length - 1].content || '*Response cancelled*',
            streaming: false,
          }
          return updated
        })
      } else {
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            role: 'assistant',
            content: `Sorry, I encountered an error: ${err.message}\n\nPlease make sure the backend server is running.\n\n**To start:** \`uvicorn backend.api.main:app --reload\``,
            streaming: false,
            sources: [],
            emergency: null,
            timestamp: Date.now(),
          }
          return updated
        })
        toast.error(err.message)
      }
    } finally {
      setLoading(false)
      abortRef.current = null
      inputRef.current?.focus()
    }
  }, [input, loading, messages, toast])

  const handleRegenerate = useCallback(async () => {
    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user')
    if (!lastUserMsg || loading) return

    setMessages(prev => prev.slice(0, -1))
    setLoading(true)

    const assistantPlaceholder = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      streaming: true,
      sources: [],
      emergency: null,
      timestamp: Date.now(),
    }
    setMessages(prev => [...prev, assistantPlaceholder])

    const controller = new AbortController()
    abortRef.current = controller

    try {
      let fullText = ''
      let sources = []
      let emergency = null
      const history = messages
        .slice(0, -1)
        .map(m => ({ role: m.role, content: m.content }))
        .slice(-10)

      for await (const chunk of streamMessage(lastUserMsg.content, history, controller.signal)) {
        if (chunk.type === 'emergency') {
          emergency = chunk.data
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { ...updated[updated.length - 1], emergency }
            return updated
          })
        } else if (chunk.type === 'sources') {
          sources = chunk.data
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = { ...updated[updated.length - 1], sources }
            return updated
          })
        } else if (chunk.type === 'text') {
          fullText += chunk.data
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              content: fullText,
              streaming: true,
            }
            return updated
          })
        } else if (chunk.type === 'done') {
          setMessages(prev => {
            const updated = [...prev]
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              streaming: false,
            }
            return updated
          })
        }
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        toast.error('Failed to regenerate response')
        setMessages(prev => {
          const updated = [...prev]
          updated[updated.length - 1] = {
            ...updated[updated.length - 1],
            content: 'Failed to regenerate. Please try again.',
            streaming: false,
          }
          return updated
        })
      }
    } finally {
      setLoading(false)
      abortRef.current = null
    }
  }, [messages, loading, toast])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = useCallback(() => {
    if (loading && abortRef.current) {
      abortRef.current.abort()
    }
    setMessages([])
    localStorage.removeItem(STORAGE_KEY)
    toast.info('Chat cleared')
  }, [loading])

  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
        e.preventDefault()
        clearChat()
      }
      if (e.key === 'Escape' && loading && abortRef.current) {
        abortRef.current.abort()
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [loading, clearChat])

  const isHealthy = health?.status === 'healthy'

  return (
    <div className="flex flex-col h-screen transition-colors duration-200">
      <NeuralBackground />

      <div className="flex flex-col h-screen relative z-10">
        <ChatHeader
          isDark={isDark}
          toggleDark={toggleDark}
          isHealthy={isHealthy}
          health={health}
          setHealth={setHealth}
          showInfo={showInfo}
          setShowInfo={setShowInfo}
          clearChat={clearChat}
        />

        {showInfo && (
          <div className="glass border-b border-medical-200/50 dark:border-medical-800/50 px-4 py-2.5 text-xs text-medical-700 dark:text-medical-300 animate-slide-down relative z-10">
            <strong>Medical Disclaimer:</strong> MediAssist provides health information for educational purposes only.
            It is NOT a substitute for professional medical advice. In emergencies, call your local emergency number.
            <button
              onClick={() => setShowInfo(false)}
              className="ml-2 underline underline-offset-2 hover:text-medical-800 dark:hover:text-medical-200 transition-colors"
            >
              Dismiss
            </button>
          </div>
        )}

        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center">
            <EmptyState />
            <div className="w-full max-w-full sm:max-w-xl px-4 pb-4">
              <ChatInput
                input={input}
                setInput={setInput}
                loading={loading}
                onSend={handleSend}
                onStop={() => abortRef.current?.abort()}
                onKeyDown={handleKeyDown}
                inputRef={inputRef}
              />
            </div>
          </div>
        )}

        {messages.length > 0 && (
          <>
            <MessageList
              messages={messages}
              handleRegenerate={handleRegenerate}
              messagesEndRef={messagesEndRef}
            />

            <div className="px-4 pt-2 pb-2 relative z-10">
              <div className="max-w-full sm:max-w-xl mx-auto">
                <ChatInput
                  input={input}
                  setInput={setInput}
                  loading={loading}
                  onSend={handleSend}
                  onStop={() => abortRef.current?.abort()}
                  onKeyDown={handleKeyDown}
                  inputRef={inputRef}
                />
              </div>
            </div>
          </>
        )}

        <div className="text-center py-1.5 px-4 text-xs text-slate-400 dark:text-slate-500 relative z-10">
          © Developed by Ozair Ilyas · All rights reserved
        </div>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <AppContent />
      </ToastProvider>
    </ErrorBoundary>
  )
}
