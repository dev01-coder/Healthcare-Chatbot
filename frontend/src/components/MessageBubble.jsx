import React, { useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import { User, Stethoscope, Clock } from 'lucide-react'
import EmergencyAlert from './EmergencyAlert'
import SourceBadges from './SourceBadges'
import MessageActions from './MessageActions'

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now - date
  const diffSec = Math.floor(diffMs / 1000)
  const diffMin = Math.floor(diffSec / 60)

  if (diffSec < 10) return 'just now'
  if (diffSec < 60) return `${diffSec}s ago`
  if (diffMin < 60) return `${diffMin}m ago`
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function MessageBubble({ message, onRegenerate }) {
  const isUser = message.role === 'user'
  const isStreaming = message.streaming
  const timeStr = useMemo(() => formatTime(message.timestamp), [message.timestamp])

  if (isUser) {
    return (
      <div className="flex justify-end mb-4 animate-slide-up">
        <div className="flex items-end gap-2 max-w-[85%] sm:max-w-[75%]">
          <div className="bg-medical-600/90 text-white px-4 py-3 rounded-2xl rounded-br-md shadow-sm backdrop-blur-sm">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
          </div>
          <div className="w-8 h-8 rounded-full bg-medical-600 dark:bg-medical-500 flex items-center justify-center flex-shrink-0 mb-0.5 shadow-sm">
            <User className="w-4 h-4 text-white" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex justify-start mb-4 animate-slide-up group">
      <div className="flex items-end gap-2 max-w-[90%] sm:max-w-[85%]">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-medical-600 flex items-center justify-center flex-shrink-0 mb-0.5 shadow-sm">
          <Stethoscope className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          {message.emergency && (
            <EmergencyAlert emergency={message.emergency} />
          )}

          <div className="glass px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
            {message.content ? (
              <div className={`prose prose-sm max-w-none ${isStreaming ? 'typing-cursor' : ''}`}>
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            ) : (
              <div className="flex items-center gap-2.5 text-slate-400 dark:text-slate-500 text-sm py-1">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-teal-400 rounded-full animate-pulse-dot" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-teal-400 rounded-full animate-pulse-dot" style={{ animationDelay: '200ms' }} />
                  <span className="w-2 h-2 bg-teal-400 rounded-full animate-pulse-dot" style={{ animationDelay: '400ms' }} />
                </div>
                <span className="font-medium">MediAssist is thinking...</span>
              </div>
            )}
          </div>

          {!isStreaming && (
            <div className="flex items-center justify-between mt-1 px-1">
              <div className="flex items-center gap-1 text-xs text-slate-400 dark:text-slate-500">
                <Clock className="w-3 h-3" />
                <span>{timeStr}</span>
              </div>
              <MessageActions
                content={message.content}
                onRegenerate={onRegenerate}
                disabled={isStreaming}
              />
            </div>
          )}

          {!isStreaming && message.sources && message.sources.length > 0 && (
            <SourceBadges sources={message.sources} />
          )}
        </div>
      </div>
    </div>
  )
}
