import React from 'react'
import { BookOpen, Pill, Activity, Brain, AlertTriangle } from 'lucide-react'

const CATEGORY_ICONS = {
  medication: Pill,
  symptoms: Activity,
  mental_health: Brain,
  emergency: AlertTriangle,
}

const CATEGORY_COLORS = {
  general: 'bg-slate-100 text-slate-600',
  medication: 'bg-purple-100 text-purple-700',
  symptoms: 'bg-green-100 text-green-700',
  mental_health: 'bg-indigo-100 text-indigo-700',
  emergency: 'bg-red-100 text-red-700',
  prevention: 'bg-teal-100 text-teal-700',
  regional: 'bg-amber-100 text-amber-700',
}

export default function SourceBadges({ sources }) {
  if (!sources || sources.length === 0) return null

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      <span className="text-xs text-slate-400 self-center">Sources:</span>
      {sources.map((source, i) => {
        const Icon = CATEGORY_ICONS[source.category] || BookOpen
        const colorClass = CATEGORY_COLORS[source.category] || CATEGORY_COLORS.general

        return (
          <span
            key={i}
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${colorClass}`}
          >
            <Icon className="w-3 h-3" />
            {source.name}
          </span>
        )
      })}
    </div>
  )
}
