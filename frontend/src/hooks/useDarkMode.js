import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'mediassist-dark-mode'

function getInitialDark() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored !== null) return stored === 'true'
  } catch {}
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

export default function useDarkMode() {
  const [isDark, setIsDark] = useState(getInitialDark)

  useEffect(() => {
    const root = document.documentElement
    if (isDark) {
      root.classList.add('dark')
    } else {
      root.classList.remove('dark')
    }
    try {
      localStorage.setItem(STORAGE_KEY, String(isDark))
    } catch {}
  }, [isDark])

  const toggle = useCallback(() => setIsDark(prev => !prev), [])

  return [isDark, toggle]
}
