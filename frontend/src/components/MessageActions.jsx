import React, { useState } from 'react'
import { Copy, Check, RefreshCw } from 'lucide-react'
import { useToast } from './Toast'

export default function MessageActions({ content, onRegenerate, disabled }) {
  const [copied, setCopied] = useState(false)
  const toast = useToast()

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      toast.success('Copied to clipboard')
      setTimeout(() => setCopied(false), 2000)
    } catch {
      toast.error('Failed to copy')
    }
  }

  return (
    <div className="message-actions flex items-center gap-1 mt-1.5">
      <button
        onClick={handleCopy}
        className="flex items-center gap-1 px-2 py-1 text-xs rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-700 transition-colors"
        title="Copy message"
        aria-label="Copy message"
      >
        {copied ? (
          <Check className="w-3 h-3 text-emerald-500" />
        ) : (
          <Copy className="w-3 h-3" />
        )}
        <span>{copied ? 'Copied' : 'Copy'}</span>
      </button>

      {onRegenerate && (
        <button
          onClick={onRegenerate}
          disabled={disabled}
          className="flex items-center gap-1 px-2 py-1 text-xs rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:text-slate-300 dark:hover:bg-slate-700 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          title="Regenerate response"
          aria-label="Regenerate response"
        >
          <RefreshCw className="w-3 h-3" />
          <span>Regenerate</span>
        </button>
      )}
    </div>
  )
}
