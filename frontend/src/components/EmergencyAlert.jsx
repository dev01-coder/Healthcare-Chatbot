import React from 'react'
import { AlertTriangle, Phone, Heart } from 'lucide-react'

export default function EmergencyAlert({ emergency }) {
  if (!emergency) return null

  const isSuicide = emergency.type === 'suicide'

  return (
    <div
      className={`border-2 rounded-xl p-4 mb-3 emergency-pulse ${
        isSuicide
          ? 'bg-blue-50 border-blue-400 dark:bg-blue-950 dark:border-blue-600'
          : 'bg-red-50 border-red-500 dark:bg-red-950 dark:border-red-600'
      }`}
      role="alert"
      aria-live="assertive"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-2">
        {isSuicide ? (
          <Heart className="w-5 h-5 text-blue-500 dark:text-blue-400" />
        ) : (
          <AlertTriangle className="w-5 h-5 text-red-500 dark:text-red-400" />
        )}
        <span className={`font-bold text-base ${
          isSuicide
            ? 'text-blue-800 dark:text-blue-200'
            : 'text-red-800 dark:text-red-200'
        }`}>
          {emergency.title}
        </span>
      </div>

      {/* Message */}
      <p className={`text-sm mb-3 leading-relaxed ${
        isSuicide
          ? 'text-blue-700 dark:text-blue-300'
          : 'text-red-700 dark:text-red-300'
      }`}>
        {emergency.message}
      </p>

      {/* Action steps */}
      <div className="space-y-1.5">
        {emergency.actions.map((action, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold flex-shrink-0 mt-0.5 ${
              isSuicide
                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300'
                : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300'
            }`}>
              {i + 1}
            </span>
            <span className={`text-sm leading-snug ${
              isSuicide
                ? 'text-blue-700 dark:text-blue-300'
                : 'text-red-700 dark:text-red-300'
            }`}>
              {action}
            </span>
          </div>
        ))}
      </div>

      {/* Call buttons */}
      <div className="mt-4 flex flex-wrap gap-2">
        <a
          href="tel:112"
          className="flex items-center gap-1.5 bg-red-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-red-700 active:bg-red-800 transition-colors shadow-sm"
        >
          <Phone className="w-3.5 h-3.5" />
          Call Emergency (112)
        </a>
      </div>
    </div>
  )
}
