import { useState, useEffect, useRef, useCallback } from 'react'
import { Send, Square } from 'lucide-react'
import { fetchSuggestions } from '../utils/api'

export default function ChatInput({ input, setInput, loading, onSend, onStop, onKeyDown, inputRef }) {
  const [suggestions, setSuggestions] = useState([])
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const debounceRef = useRef(null)
  const wrapperRef = useRef(null)

  const fetchSuggestionsDebounced = useCallback((query) => {
    clearTimeout(debounceRef.current)
    if (query.length < 2) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    debounceRef.current = setTimeout(async () => {
      const results = await fetchSuggestions(query, 5)
      setSuggestions(results)
      setShowSuggestions(results.length > 0)
      setSelectedIndex(-1)
    }, 300)
  }, [])

  useEffect(() => {
    fetchSuggestionsDebounced(input)
    return () => clearTimeout(debounceRef.current)
  }, [input, fetchSuggestionsDebounced])

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target)) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectSuggestion = (suggestion) => {
    setInput(suggestion)
    setShowSuggestions(false)
    setSelectedIndex(-1)
    inputRef.current?.focus()
  }

  const handleKeyDownInternal = (e) => {
    if (!showSuggestions || suggestions.length === 0) {
      onKeyDown(e)
      return
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setSelectedIndex(prev => (prev + 1) % suggestions.length)
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setSelectedIndex(prev => (prev - 1 + suggestions.length) % suggestions.length)
    } else if (e.key === 'Enter' && !e.shiftKey && selectedIndex >= 0) {
      e.preventDefault()
      selectSuggestion(suggestions[selectedIndex])
    } else if (e.key === 'Escape') {
      setShowSuggestions(false)
      setSelectedIndex(-1)
    } else {
      onKeyDown(e)
    }
  }

  return (
    <div className="relative" ref={wrapperRef}>
      <div className="flex gap-1.5 sm:gap-2 items-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600/50 rounded-2xl shadow-sm px-2.5 py-1.5 sm:px-3 sm:py-2 focus-within:ring-2 focus-within:ring-medical-400/50 focus-within:border-medical-400/50 dark:focus-within:ring-medical-500/50 dark:focus-within:border-medical-500/50 transition-all duration-200">
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDownInternal}
          placeholder="Ask about symptoms, medicines, diseases..."
          className="flex-1 bg-transparent text-sm text-slate-800 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none min-w-0"
          disabled={loading}
          aria-label="Message input"
          autoComplete="off"
        />

        {loading ? (
          <button
            onClick={onStop}
            className="w-8 h-8 bg-red-500 text-white rounded-xl flex items-center justify-center hover:bg-red-600 active:bg-red-700 transition-colors flex-shrink-0"
            title="Stop generating"
            aria-label="Stop generating"
          >
            <Square className="w-3.5 h-3.5" fill="currentColor" />
          </button>
        ) : (
          <button
            onClick={() => onSend()}
            disabled={!input.trim()}
            className="w-8 h-8 bg-medical-600 text-white rounded-xl flex items-center justify-center hover:bg-medical-700 active:bg-medical-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            title="Send message"
            aria-label="Send message"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-lg overflow-hidden z-50 max-h-48 overflow-y-auto">
          {suggestions.map((suggestion, i) => (
            <button
              key={i}
              onMouseDown={(e) => {
                e.preventDefault()
                selectSuggestion(suggestion)
              }}
              onMouseEnter={() => setSelectedIndex(i)}
              className={`w-full text-left px-3 sm:px-4 py-2 sm:py-2.5 text-xs sm:text-sm transition-colors ${
                i === selectedIndex
                  ? 'bg-medical-50 dark:bg-medical-900/50 text-medical-700 dark:text-medical-300'
                  : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700/50'
              }`}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
