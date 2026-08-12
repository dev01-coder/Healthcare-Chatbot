import { Stethoscope, Sparkles } from 'lucide-react'

export default function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-12 sm:py-20 px-4 animate-fade-in">
      <div className="relative mb-6 sm:mb-8 animate-float">
        <div className="w-16 h-16 sm:w-24 sm:h-24 bg-gradient-to-br from-teal-400 to-medical-600 rounded-2xl sm:rounded-3xl flex items-center justify-center shadow-xl animate-electric-glow">
          <Stethoscope className="w-8 h-8 sm:w-12 sm:h-12 text-white" />
        </div>
        <div className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
      </div>

      <h1 className="text-2xl sm:text-3xl font-bold text-slate-800 dark:text-slate-100 mb-3">
        MediAssist
      </h1>
      <p className="text-sm sm:text-base text-slate-500 dark:text-slate-400 text-center max-w-md mb-1">
        Your AI-powered healthcare assistant
      </p>
      <p className="text-xs sm:text-sm text-slate-400 dark:text-slate-500 text-center max-w-sm">
        Ask about symptoms, medicines, diseases, or health advice.
      </p>
    </div>
  )
}
