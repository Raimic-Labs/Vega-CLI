export interface ProviderConfig {
  id: string
  name: string
  envVar: string
  baseUrl: string
  defaultModel: string
  models: { id: string; name: string; contextWindow: number }[]
}

export const PROVIDERS: Record<string, ProviderConfig> = {
  nvidia: {
    id: 'nvidia',
    name: 'NVIDIA NIM',
    envVar: 'VEGA_NVIDIA_API_KEY',
    baseUrl: 'https://integrate.api.nvidia.com/v1',
    defaultModel: 'moonshotai/kimi-k2.6',
    models: [
      { id: 'moonshotai/kimi-k2.6', name: 'Kimi K2.6', contextWindow: 128000 },
      { id: 'meta/llama-3.3-70b-instruct', name: 'Llama 3.3 70B', contextWindow: 128000 },
      { id: 'nvidia/llama-3.1-nemotron-70b-instruct', name: 'Nemotron 70B', contextWindow: 128000 },
    ],
  },
  google: {
    id: 'google',
    name: 'Google Gemini',
    envVar: 'VEGA_GOOGLE_API_KEY',
    baseUrl: 'https://generativelanguage.googleapis.com/v1beta',
    defaultModel: 'gemini-2.0-flash',
    models: [
      { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', contextWindow: 1048576 },
      { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', contextWindow: 2097152 },
    ],
  },
  groq: {
    id: 'groq',
    name: 'Groq',
    envVar: 'VEGA_GROQ_API_KEY',
    baseUrl: 'https://api.groq.com/openai/v1',
    defaultModel: 'llama-3.3-70b-versatile',
    models: [
      { id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile', contextWindow: 128000 },
      { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B', contextWindow: 32768 },
    ],
  },
  deepseek: {
    id: 'deepseek',
    name: 'DeepSeek',
    envVar: 'VEGA_DEEPSEEK_API_KEY',
    baseUrl: 'https://api.deepseek.com/v1',
    defaultModel: 'deepseek-chat',
    models: [
      { id: 'deepseek-chat', name: 'DeepSeek-V3', contextWindow: 64000 },
      { id: 'deepseek-reasoner', name: 'DeepSeek-R1', contextWindow: 64000 },
    ],
  },
}

const STORAGE_KEY = 'vega_api_keys'

export function getSavedKeys(): Record<string, string> {
  if (typeof window === 'undefined') return {}
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch {
    return {}
  }
}

export function getApiKey(providerId: string): string {
  const keys = getSavedKeys()
  return keys[providerId] || ''
}

export function setApiKey(providerId: string, apiKey: string): void {
  if (typeof window === 'undefined') return
  try {
    const keys = getSavedKeys()
    if (apiKey.trim()) {
      keys[providerId] = apiKey.trim()
    } else {
      delete keys[providerId]
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(keys))
  } catch (err) {
    console.error('Failed to save API key:', err)
  }
}
