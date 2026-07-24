import { PROVIDERS, getApiKey } from './providers'
import { routeToAgent } from './agents'

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export interface StreamOptions {
  messages: ChatMessage[]
  model?: string
  apiKey?: string
  onToken?: (token: string) => void
}

/**
 * Unified streaming handler supporting SSE streams from API endpoints.
 */
export async function streamResponse(options: StreamOptions): Promise<string> {
  const { messages, model, apiKey, onToken } = options
  const lastUserPrompt = messages[messages.length - 1]?.content || ''
  const route = routeToAgent(lastUserPrompt, model)

  const effectiveKey = apiKey || getApiKey(route.provider.id)

  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      messages,
      model: route.modelId,
      provider: route.provider.id,
      apiKey: effectiveKey,
    }),
  })

  if (!res.ok || !res.body) {
    throw new Error(`API error: ${res.statusText}`)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let fullText = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split('\n')

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const dataStr = line.replace('data: ', '').trim()
        if (dataStr === '[DONE]') break
        try {
          const parsed = JSON.parse(dataStr)
          const delta = parsed.choices?.[0]?.delta?.content || ''
          if (delta) {
            fullText += delta
            onToken?.(delta)
          }
        } catch {
          // Ignore partial JSON parse errors
        }
      }
    }
  }

  return fullText
}

/**
 * Call NVIDIA NIM API directly or via proxy.
 */
export async function callNvidia(messages: ChatMessage[], apiKey?: string, model = 'moonshotai/kimi-k2.6'): Promise<string> {
  const key = apiKey || getApiKey('nvidia')
  const res = await fetch(`${PROVIDERS.nvidia.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify({ model, messages, stream: false }),
  })
  const data = await res.json()
  return data.choices?.[0]?.message?.content || ''
}

/**
 * Call Google Gemini API directly.
 */
export async function callGemini(messages: ChatMessage[], apiKey?: string, model = 'gemini-2.0-flash'): Promise<string> {
  const key = apiKey || getApiKey('google')
  const contents = messages.map((m) => ({
    role: m.role === 'user' ? 'user' : 'model',
    parts: [{ text: m.content }],
  }))

  const res = await fetch(
    `${PROVIDERS.google.baseUrl}/models/${model}:generateContent?key=${key}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ contents }),
    }
  )
  const data = await res.json()
  return data.candidates?.[0]?.content?.parts?.[0]?.text || ''
}

/**
 * Call Groq API directly.
 */
export async function callGroq(messages: ChatMessage[], apiKey?: string, model = 'llama-3.3-70b-versatile'): Promise<string> {
  const key = apiKey || getApiKey('groq')
  const res = await fetch(`${PROVIDERS.groq.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify({ model, messages, stream: false }),
  })
  const data = await res.json()
  return data.choices?.[0]?.message?.content || ''
}

/**
 * Call DeepSeek API directly.
 */
export async function callDeepseek(messages: ChatMessage[], apiKey?: string, model = 'deepseek-chat'): Promise<string> {
  const key = apiKey || getApiKey('deepseek')
  const res = await fetch(`${PROVIDERS.deepseek.baseUrl}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify({ model, messages, stream: false }),
  })
  const data = await res.json()
  return data.choices?.[0]?.message?.content || ''
}
