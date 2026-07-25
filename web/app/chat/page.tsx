
'use client'

import { useState, useRef, useEffect, useCallback, ChangeEvent, KeyboardEvent } from 'react'
import Link from 'next/link'
import CopyButton from '@/components/ui/CopyButton'
import styles from './chat.module.css'

/* ─────────────────────────────────────────────
   Types & Interfaces
───────────────────────────────────────────── */
interface AgentInfo {
  name: string
  model: string
  provider: string
  badge: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentInfo?: AgentInfo
  timestamp: string
}

interface ChatSession {
  id: string
  title: string
  messages: Message[]
}

const AVAILABLE_MODELS = [
  { id: 'moonshotai/kimi-k2.6', name: 'Kimi K2.6', provider: 'NVIDIA' },
  { id: 'meta/llama-4-scout', name: 'Llama 4 Scout', provider: 'Groq' },
  { id: 'google/gemini-2.0-flash', name: 'Gemini 2.0 Flash', provider: 'Google' },
  { id: 'deepseek-ai/deepseek-v3', name: 'DeepSeek-V3', provider: 'DeepSeek' },
]

/* ─────────────────────────────────────────────
   Helper: Detect Agent
───────────────────────────────────────────── */
function detectAgent(prompt: string, modelId: string): AgentInfo {
  const lower = prompt.toLowerCase()
  const modelObj = AVAILABLE_MODELS.find((m) => m.id === modelId) || AVAILABLE_MODELS[0]

  if (/\b(build|create|make|scaffold|app|website)\b/.test(lower)) {
    return { name: 'CodeAgent', model: modelObj.name, provider: modelObj.provider, badge: '⟡' }
  }
  if (/\b(fix|bug|error|debug|issue|crash)\b/.test(lower)) {
    return { name: 'DebugAgent', model: modelObj.name, provider: modelObj.provider, badge: '🐞' }
  }
  if (/\b(plan|design|architecture|schema)\b/.test(lower)) {
    return { name: 'PlannerAgent', model: 'DeepSeek-V3', provider: 'DeepSeek', badge: '🗺' }
  }
  if (/\b(review|refactor|improve|optimize)\b/.test(lower)) {
    return { name: 'ReviewAgent', model: 'DeepSeek-V3', provider: 'DeepSeek', badge: '🔍' }
  }
  if (/\b(draw|image|picture|logo|photo)\b/.test(lower)) {
    return { name: 'ImageAgent', model: 'Gemini 2.0 Flash', provider: 'Google', badge: '🎨' }
  }
  if (/\b(what|explain|how|why|summary)\b/.test(lower)) {
    return { name: 'FastAgent', model: 'Llama 4 Scout', provider: 'Groq', badge: '⚡' }
  }

  return { name: 'CodeAgent', model: modelObj.name, provider: modelObj.provider, badge: '⟡' }
}

/* ─────────────────────────────────────────────
   Markdown Content Renderer (Code & File Trees)
───────────────────────────────────────────── */
function MarkdownRenderer({ content }: { content: string }) {
  // Regex to split code blocks
  const parts = content.split(/(```[\s\S]*?```)/g)

  return (
    <div>
      {parts.map((part, index) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const lines = part.slice(3, -3).trim().split('\n')
          const firstLine = lines[0].trim()
          const isLang = /^[a-zA-Z0-9_+#-]+$/.test(firstLine)
          const lang = isLang ? firstLine : 'text'
          const code = isLang ? lines.slice(1).join('\n') : lines.join('\n')

          return (
            <div key={index} className={styles.codeBlock}>
              <div className={styles.codeHeader}>
                <span>{lang.toUpperCase()}</span>
                <CopyButton text={code} />
              </div>
              <pre className={styles.codePre}>
                <code>{code}</code>
              </pre>
            </div>
          )
        }

        // Render plain text and paragraph sections
        return (
          <div key={index} style={{ whiteSpace: 'pre-wrap' }}>
            {part}
          </div>
        )
      })}
    </div>
  )
}

/* ─────────────────────────────────────────────
   Main Component: ChatPage
───────────────────────────────────────────── */
export default function ChatPage() {
  const [selectedModel, setSelectedModel] = useState('moonshotai/kimi-k2.6')
  const [input, setInput] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)

  // Chat sessions history
  const [sessions, setSessions] = useState<ChatSession[]>([
    {
      id: 'default-session',
      title: 'New Conversation',
      messages: [],
    },
  ])
  const [activeSessionId, setActiveSessionId] = useState('default-session')

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Current active session
  const activeSession = sessions.find((s) => s.id === activeSessionId) || sessions[0]
  const messages = activeSession?.messages || []

  // Auto scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages, isStreaming])

  // Auto resize textarea
  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`
    }
  }

  // Create new session
  const createNewChat = () => {
    const newId = `session-${Date.now()}`
    const newSession: ChatSession = {
      id: newId,
      title: 'New Conversation',
      messages: [],
    }
    setSessions((prev) => [newSession, ...prev])
    setActiveSessionId(newId)
  }

  // Delete session
  const deleteSession = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    if (sessions.length === 1) {
      setSessions([
        { id: `session-${Date.now()}`, title: 'New Conversation', messages: [] },
      ])
      return
    }
    const filtered = sessions.filter((s) => s.id !== id)
    setSessions(filtered)
    if (activeSessionId === id) {
      setActiveSessionId(filtered[0].id)
    }
  }

  // Send message & stream response
  const sendMessage = useCallback(
    async (textToSend?: string) => {
      const prompt = textToSend || input
      if (!prompt.trim() || isStreaming) return

      const userMsgId = `msg-${Date.now()}`
      const userMsg: Message = {
        id: userMsgId,
        role: 'user',
        content: prompt.trim(),
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      const agentInfo = detectAgent(prompt, selectedModel)
      const assistantMsgId = `msg-${Date.now() + 1}`
      const assistantMsg: Message = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        agentInfo,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      }

      // Update session title if first message
      setSessions((prev) =>
        prev.map((session) => {
          if (session.id === activeSessionId) {
            const isFirst = session.messages.length === 0
            const newTitle = isFirst ? prompt.slice(0, 24) + (prompt.length > 24 ? '...' : '') : session.title
            return {
              ...session,
              title: newTitle,
              messages: [...session.messages, userMsg, assistantMsg],
            }
          }
          return session
        })
      )

      setInput('')
      if (textareaRef.current) textareaRef.current.style.height = 'auto'
      setIsStreaming(true)

      try {
        const response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: [{ role: 'user', content: prompt }],
            model: selectedModel,
          }),
        })

        if (!response.ok || !response.body) {
          throw new Error('Failed to connect to API')
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let accumulatedContent = ''

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
                accumulatedContent += delta

                // Functional update to append streaming text
                setSessions((prev) =>
                  prev.map((s) => {
                    if (s.id === activeSessionId) {
                      return {
                        ...s,
                        messages: s.messages.map((m) =>
                          m.id === assistantMsgId ? { ...m, content: accumulatedContent } : m
                        ),
                      }
                    }
                    return s
                  })
                )
              } catch {
                // Ignore parse errors for partial chunks
              }
            }
          }
        }
      } catch (err) {
        console.error('Error streaming response:', err)
        setSessions((prev) =>
          prev.map((s) => {
            if (s.id === activeSessionId) {
              return {
                ...s,
                messages: s.messages.map((m) =>
                  m.id === assistantMsgId
                    ? { ...m, content: '✦ An error occurred while generating the response. Please check your network or try again.' }
                    : m
                ),
              }
            }
            return s
          })
        )
      } finally {
        setIsStreaming(false)
      }
    },
    [input, isStreaming, selectedModel, activeSessionId]
  )

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const clearCurrentChat = () => {
    setSessions((prev) =>
      prev.map((s) => (s.id === activeSessionId ? { ...s, messages: [] } : s))
    )
  }

  return (
    <div className={styles.container}>
      {/* ─────────────────────────────────────────────
          LEFT SIDEBAR (260px)
      ───────────────────────────────────────────── */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <Link href="/" className={styles.logo}>
            <span className={styles.logoIcon}>⟡</span>
            <span>Vega</span>
          </Link>
        </div>

        <button onClick={createNewChat} className={styles.newChatBtn} id="new-chat-btn">
          <span>+</span> New Chat
        </button>

        <div className={styles.historySection}>
          <div className={styles.historyTitle}>Recent Chats</div>
          {sessions.map((s) => (
            <div
              key={s.id}
              onClick={() => setActiveSessionId(s.id)}
              className={`${styles.historyItem} ${s.id === activeSessionId ? styles.historyItemActive : ''}`}
            >
              <span className={styles.historyText}>{s.title}</span>
              <button
                onClick={(e) => deleteSession(s.id, e)}
                className={styles.deleteItemBtn}
                title="Delete chat"
              >
                ✕
              </button>
            </div>
          ))}
        </div>

        <div className={styles.sidebarFooter}>
          <div className={styles.modelSelectLabel}>Default Model</div>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className={styles.modelDropdown}
            id="model-dropdown"
          >
            {AVAILABLE_MODELS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.provider})
              </option>
            ))}
          </select>

          <Link href="https://github.com/Raimic-Labs/Vega-CLI" target="_blank" className={styles.settingsLink}>
            <span>⚙</span> Settings & Docs
          </Link>
        </div>
      </aside>

      {/* ─────────────────────────────────────────────
          MAIN CHAT AREA
      ───────────────────────────────────────────── */}
      <main className={styles.mainChat}>
        {/* Header Bar */}
        <header className={styles.chatHeader}>
          <div className={styles.headerTitle}>
            <span>Vega AI Workspace</span>
            <span className={styles.activeBadge}>
              {AVAILABLE_MODELS.find((m) => m.id === selectedModel)?.name}
            </span>
          </div>

          <button onClick={clearCurrentChat} className={styles.clearBtn} id="clear-chat-btn">
            Clear Chat
          </button>
        </header>

        {/* Messages List */}
        <div className={styles.messagesContainer}>
          {messages.length === 0 ? (
            <div className={styles.emptyState}>
              <div className={styles.emptyLogo}>⟡</div>
              <div className={styles.emptyTitle}>What will you build today?</div>
              <div className={styles.emptyDesc}>
                Ask Vega to code a full project, debug errors, plan architecture, or generate visual elements.
              </div>

              <div className={styles.suggestionGrid}>
                <div
                  className={styles.suggestionCard}
                  onClick={() => sendMessage('build me a REST API in Python with FastAPI')}
                >
                  🚀 Build a REST API with FastAPI
                </div>
                <div
                  className={styles.suggestionCard}
                  onClick={() => sendMessage('create a SaaS landing page with responsive design')}
                >
                  🌐 Create a modern SaaS landing page
                </div>
                <div
                  className={styles.suggestionCard}
                  onClick={() => sendMessage('debug an async/await deadlock error in JavaScript')}
                >
                  🐞 Debug an async/await deadlock
                </div>
                <div
                  className={styles.suggestionCard}
                  onClick={() => sendMessage('plan the database architecture for an e-commerce platform')}
                >
                  🗺 Plan database architecture
                </div>
              </div>
            </div>
          ) : (
            messages.map((msg) =>
              msg.role === 'user' ? (
                <div key={msg.id} className={styles.userRow}>
                  <div className={styles.userBubble}>{msg.content}</div>
                </div>
              ) : (
                <div key={msg.id} className={styles.aiRow}>
                  {msg.agentInfo && (
                    <div className={styles.agentBadge}>
                      <span>{msg.agentInfo.badge}</span>
                      <span>
                        {msg.agentInfo.name} · {msg.agentInfo.model} · {msg.agentInfo.provider}
                      </span>
                    </div>
                  )}
                  <div className={styles.aiPanel}>
                    <MarkdownRenderer content={msg.content} />
                    {isStreaming && msg.id === messages[messages.length - 1]?.id && (
                      <span className={styles.typingCursor} />
                    )}
                  </div>
                  <div className={styles.msgActions}>
                    <CopyButton text={msg.content} />
                  </div>
                </div>
              )
            )
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* ─────────────────────────────────────────────
            BOTTOM INPUT BOX
        ───────────────────────────────────────────── */}
        <div className={styles.inputContainer}>
          <div className={styles.inputBox}>
            <textarea
              ref={textareaRef}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Ask Vega to build, debug, or generate code..."
              className={styles.textarea}
              rows={1}
              id="chat-input-textarea"
            />

            <div className={styles.inputControls}>
              <div className={styles.inputLeft}>
                <button className={styles.attachBtn} title="Attach file (coming soon)">
                  📎
                </button>
                <span className={styles.modelBadgeFooter}>
                  {AVAILABLE_MODELS.find((m) => m.id === selectedModel)?.provider} ·{' '}
                  {AVAILABLE_MODELS.find((m) => m.id === selectedModel)?.name}
                </span>
              </div>

              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || isStreaming}
                className={styles.sendBtn}
                id="send-msg-btn"
                title="Send message"
              >
                ➔
              </button>
            </div>
          </div>

          <div className={styles.inputFooterText}>
            Vega AI can make mistakes. Verify output. Powered by Raimic Labs.
          </div>
        </div>
      </main>
    </div>
  )
}
