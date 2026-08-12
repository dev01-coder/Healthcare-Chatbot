const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const REQUEST_TIMEOUT = 30000
const STREAM_TIMEOUT = 60000

async function fetchWithTimeout(url, options = {}, timeout = REQUEST_TIMEOUT) {
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, { ...options, signal: controller.signal })
    clearTimeout(id)
    return response
  } catch (err) {
    clearTimeout(id)
    if (err.name === 'AbortError') {
      throw new Error('Request timed out. Please try again.')
    }
    throw err
  }
}

export async function sendMessage(message, history = []) {
  const response = await fetchWithTimeout(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Failed to get response' }))
    throw new Error(err.detail || 'Failed to get response')
  }

  return response.json()
}

export async function* streamMessage(message, history = [], signal = null) {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), STREAM_TIMEOUT)

  // Link external signal to our controller
  if (signal) {
    signal.addEventListener('abort', () => controller.abort())
  }

  try {
    const response = await fetch(`${API_URL}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history, stream: true }),
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      throw new Error('Stream request failed')
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            yield data
          } catch {
            // Skip malformed chunks
          }
        }
      }
    }
  } catch (err) {
    clearTimeout(timeoutId)
    if (err.name === 'AbortError' && signal?.aborted) {
      // User cancelled — yield done signal
      yield { type: 'done' }
      return
    }
    throw err
  }
}

export async function checkHealth() {
  try {
    const res = await fetchWithTimeout(`${API_URL}/health`, {}, 5000)
    return res.json()
  } catch {
    return { status: 'error', message: 'Backend not reachable' }
  }
}

export async function fetchSuggestions(query, limit = 5) {
  try {
    const res = await fetchWithTimeout(
      `${API_URL}/api/suggest?q=${encodeURIComponent(query)}&limit=${limit}`,
      {},
      5000
    )
    if (!res.ok) return []
    const data = await res.json()
    return data.suggestions || []
  } catch {
    return []
  }
}
