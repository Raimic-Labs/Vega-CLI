'use client'

import { motion } from 'framer-motion'
import CopyButton from '@/components/CopyButton'

const PRODUCTS_LIST = [
  {
    id: 'vega-cli',
    name: 'Vega CLI',
    tagline: 'Code at the speed of stars',
    badge: 'LIVE NOW',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-500/30',
    description:
      'Vega CLI is an AI-powered command-line interface that builds full-stack projects, writes scripts, and debugs errors directly in your terminal.',
    features: [
      'Multi-Agent System (CodeAgent, DebugAgent, PlannerAgent, ReviewAgent, ImageAgent, FastAgent)',
      'Supports 4 AI Providers: NVIDIA NIM, Google Gemini, Groq, DeepSeek',
      'Autonomous ProjectBuilder generates multi-file projects on disk',
      'Zero heavy runtime dependencies — pure Python CLI',
    ],
    installCmd: 'pip install vega-raimic',
    docsUrl: 'https://github.com/Raimic-Labs/Vega-CLI',
    isLive: true,
  },
  {
    id: 'vega-web',
    name: 'Vega Web',
    tagline: 'AI Chat & Project Builder Workspace',
    badge: 'COMING SOON',
    badgeColor: 'bg-[#00FFFF]/10 text-[#00FFFF] border-[#00FFFF]/30',
    description:
      'A browser-based workspace for Vega CLI featuring real-time SSE streaming, live iframe previewing, code editing, and visual asset creation.',
    features: [
      'Real-time token streaming chat interface',
      'Visual Project Builder GUI with live HTML/CSS/JS preview',
      'AI Image Studio powered by Google Gemini',
      'JSZip integration for 1-click project downloads',
    ],
    installCmd: 'Web Cloud App',
    docsUrl: '#',
    isLive: false,
  },
  {
    id: 'vega-desktop',
    name: 'Vega Desktop',
    tagline: 'Native High-Speed Desktop App',
    badge: 'COMING SOON',
    badgeColor: 'bg-[#6C63FF]/20 text-[#6C63FF] border-[#6C63FF]/30',
    description:
      'Native desktop application engineered for ultra-fast local LLM execution, offline development, and deep IDE integration.',
    features: [
      'Native macOS, Windows, & Linux desktop support',
      'Local model execution & Ollama integration',
      'File system watcher & auto-sync',
      'Low latency native UI',
    ],
    installCmd: 'macOS · Windows · Linux',
    docsUrl: '#',
    isLive: false,
  },
  {
    id: 'vega-mobile',
    name: 'Vega Mobile',
    tagline: 'Pocket AI Build Assistant',
    badge: 'COMING SOON',
    badgeColor: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    description:
      'Manage, monitor, and trigger build pipelines on the go directly from your mobile device.',
    features: [
      'Push notifications for build completions',
      'Mobile chat workspace with voice prompt support',
      'Remote CLI task monitoring',
      'iOS & Android native apps',
    ],
    installCmd: 'iOS · Android',
    docsUrl: '#',
    isLive: false,
  },
]

export default function ProductsPage() {
  return (
    <div className="w-full max-w-7xl mx-auto px-6 pt-32 pb-24 flex flex-col items-center">
      {/* Header */}
      <div className="text-center max-w-2xl mx-auto mb-16">
        <span className="font-mono text-xs text-[#00FFFF] uppercase tracking-widest">RAIMIC LABS</span>
        <h1 className="font-display text-4xl sm:text-6xl font-extrabold text-white mt-2 mb-4">
          All Products
        </h1>
        <p className="text-gray-400 text-base leading-relaxed">
          Explore our suite of developer tools designed for maximum velocity, accessibility, and open-source power.
        </p>
      </div>

      {/* Product List */}
      <div className="flex flex-col gap-12 w-full max-w-5xl">
        {PRODUCTS_LIST.map((prod, index) => (
          <motion.div
            key={prod.id}
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="bg-[#111118] border border-white/10 rounded-2xl p-8 sm:p-10 flex flex-col gap-6 shadow-xl hover:border-[#00FFFF]/30 transition-all"
          >
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="font-display text-2xl sm:text-3xl font-extrabold text-white">
                    {prod.name}
                  </h2>
                  <span className={`text-[10px] font-mono font-bold px-3 py-1 rounded-full border ${prod.badgeColor}`}>
                    {prod.badge}
                  </span>
                </div>
                <p className="text-[#00FFFF] text-sm font-medium mt-1">{prod.tagline}</p>
              </div>

              {prod.isLive ? (
                <div className="flex items-center gap-2 bg-[#0A0A0F] px-4 py-2.5 rounded-xl border border-[#00FFFF]/30 self-start sm:self-auto">
                  <span className="text-xs font-mono text-[#00FFFF]">$</span>
                  <code className="text-xs font-mono text-gray-200">{prod.installCmd}</code>
                  <CopyButton text={prod.installCmd} />
                </div>
              ) : (
                <span className="text-xs font-mono text-gray-500 bg-[#0A0A0F] px-4 py-2 rounded-xl border border-white/5 self-start sm:self-auto">
                  {prod.installCmd}
                </span>
              )}
            </div>

            <p className="text-gray-300 text-sm sm:text-base leading-relaxed">
              {prod.description}
            </p>

            <div className="bg-[#0A0A0F]/60 rounded-xl p-5 border border-white/5">
              <h3 className="text-xs font-mono text-gray-400 uppercase tracking-wider mb-3">Key Features</h3>
              <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-sm text-gray-300">
                {prod.features.map((feat, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-[#00FFFF] font-bold">✓</span>
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
