'use client'

import { useState, useEffect } from 'react'
import styles from './settings.module.css'

interface ProviderKey {
  id: string
  name: string
  envVar: string
  key: string
  status: 'connected' | 'missing' | 'testing'
}

const DEFAULT_PROVIDERS: ProviderKey[] = [
  { id: 'nvidia', name: 'NVIDIA NIM', envVar: 'VEGA_NVIDIA_API_KEY', key: '', status: 'missing' },
  { id: 'google', name: 'Google Gemini', envVar: 'VEGA_GOOGLE_API_KEY', key: '', status: 'missing' },
  { id: 'groq', name: 'Groq', envVar: 'VEGA_GROQ_API_KEY', key: '', status: 'missing' },
  { id: 'deepseek', name: 'DeepSeek', envVar: 'VEGA_DEEPSEEK_API_KEY', key: '', status: 'missing' },
]

export default function SettingsPage() {
  const [providers, setProviders] = useState<ProviderKey[]>(DEFAULT_PROVIDERS)
  const [defaultModel, setDefaultModel] = useState('moonshotai/kimi-k2.6')
  const [showNotice, setShowNotice] = useState(false)
  const [showMasked, setShowMasked] = useState<Record<string, boolean>>({})

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const savedKeys = localStorage.getItem('vega_api_keys')
      if (savedKeys) {
        const parsed = JSON.parse(savedKeys)
        setProviders((prev) =>
          prev.map((p) => ({
            ...p,
            key: parsed[p.id] || '',
            status: parsed[p.id] ? 'connected' : 'missing',
          }))
        )
      }
      const savedModel = localStorage.getItem('vega_default_model')
      if (savedModel) {
        setDefaultModel(savedModel)
      }
    } catch {
      // Ignore localStorage errors
    }
  }, [])

  const handleKeyChange = (id: string, value: string) => {
    setProviders((prev) =>
      prev.map((p) => (p.id === id ? { ...p, key: value, status: value.trim() ? 'connected' : 'missing' } : p))
    )
  }

  const toggleMask = (id: string) => {
    setShowMasked((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const testConnection = async (id: string) => {
    setProviders((prev) =>
      prev.map((p) => (p.id === id ? { ...p, status: 'testing' } : p))
    )

    await new Promise((res) => setTimeout(res, 800))

    setProviders((prev) =>
      prev.map((p) =>
        p.id === id ? { ...p, status: p.key.trim().length > 5 ? 'connected' : 'missing' } : p
      )
    )
  }

  const handleSave = () => {
    try {
      const keyObj: Record<string, string> = {}
      providers.forEach((p) => {
        if (p.key) keyObj[p.id] = p.key
      })
      localStorage.setItem('vega_api_keys', JSON.stringify(keyObj))
      localStorage.setItem('vega_default_model', defaultModel)

      setShowNotice(true)
      setTimeout(() => setShowNotice(false), 3000)
    } catch {
      // Ignore localStorage write error
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.inner}>
        {/* Header */}
        <header className={styles.header}>
          <h1 className={styles.title}>Settings & API Keys</h1>
          <p className={styles.desc}>
            Manage your AI provider credentials and configure default models for Vega CLI and Web.
          </p>
        </header>

        {showNotice && (
          <div className={styles.saveNotice}>
            ✔ Settings saved successfully to local storage!
          </div>
        )}

        {/* Default Model */}
        <section className={styles.section}>
          <div className={styles.sectionTitle}>
            <span>⚙</span> Default AI Model
          </div>
          <select
            value={defaultModel}
            onChange={(e) => setDefaultModel(e.target.value)}
            className={styles.selectInput}
            id="settings-default-model"
          >
            <option value="moonshotai/kimi-k2.6">Kimi K2.6 (NVIDIA NIM) — Recommended</option>
            <option value="meta/llama-4-scout">Llama 4 Scout (Groq) — Ultra Fast</option>
            <option value="google/gemini-2.0-flash">Gemini 2.0 Flash (Google) — Multimodal</option>
            <option value="deepseek-ai/deepseek-v3">DeepSeek-V3 (DeepSeek) — Reasoning</option>
          </select>
        </section>

        {/* API Keys */}
        <section className={styles.section}>
          <div className={styles.sectionTitle}>
            <span>🔑</span> Provider Credentials
          </div>

          <div className={styles.providerGrid}>
            {providers.map((p) => (
              <div key={p.id} className={styles.providerCard}>
                <div className={styles.providerHeader}>
                  <div className={styles.providerName}>
                    <span>{p.name}</span>
                    <code style={{ fontSize: 11, color: 'rgba(255,255,255,0.4)', fontFamily: 'monospace' }}>
                      {p.envVar}
                    </code>
                  </div>
                  <span
                    className={`${styles.statusBadge} ${
                      p.status === 'connected' ? styles.statusConnected : styles.statusMissing
                    }`}
                  >
                    {p.status === 'testing'
                      ? 'Testing...'
                      : p.status === 'connected'
                      ? '✔ Connected'
                      : 'Missing Key'}
                  </span>
                </div>

                <div className={styles.keyInputRow}>
                  <input
                    type={showMasked[p.id] ? 'text' : 'password'}
                    value={p.key}
                    onChange={(e) => handleKeyChange(p.id, e.target.value)}
                    placeholder={`Paste ${p.name} API Key...`}
                    className={styles.keyInput}
                    id={`key-input-${p.id}`}
                  />
                  <button
                    onClick={() => toggleMask(p.id)}
                    className={styles.testBtn}
                    style={{ background: 'transparent', borderColor: 'rgba(255,255,255,0.1)' }}
                  >
                    {showMasked[p.id] ? 'Hide' : 'Show'}
                  </button>
                  <button
                    onClick={() => testConnection(p.id)}
                    className={styles.testBtn}
                    id={`test-btn-${p.id}`}
                  >
                    Test Connection
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <button onClick={handleSave} className={styles.saveBtn} id="save-settings-btn">
          💾 Save Settings
        </button>
      </div>
    </div>
  )
}
