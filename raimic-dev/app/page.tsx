'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import CopyButton from '@/components/CopyButton'

const PRODUCTS = [
  {
    name: 'Vega CLI',
    badge: 'LIVE NOW',
    badgeColor: 'bg-green-500/20 text-green-400 border-green-500/30',
    desc: 'An AI-powered CLI that builds full-stack projects, scripts, and APIs right in your terminal.',
    install: 'pip install vega-raimic',
    link: '/products',
    isLive: true,
  },
  {
    name: 'Vega Web',
    badge: 'COMING SOON',
    badgeColor: 'bg-[#00FFFF]/10 text-[#00FFFF] border-[#00FFFF]/30',
    desc: 'Browser-based AI chat workspace, project builder GUI, and visual asset generator.',
    install: 'Web Cloud Workspace',
    link: '/products',
    isLive: false,
  },
  {
    name: 'Vega Desktop',
    badge: 'COMING SOON',
    badgeColor: 'bg-[#6C63FF]/20 text-[#6C63FF] border-[#6C63FF]/30',
    desc: 'Native desktop application with offline support and high-speed local model execution.',
    install: 'macOS · Windows · Linux',
    link: '/products',
    isLive: false,
  },
  {
    name: 'Vega Mobile',
    badge: 'COMING SOON',
    badgeColor: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    desc: 'Pocket AI assistant to manage, monitor, and trigger build pipelines on the go.',
    install: 'iOS · Android',
    link: '/products',
    isLive: false,
  },
]

export default function Home() {
  return (
    <div className="flex flex-col items-center w-full">
      {/* ─────────────────────────────────────────────
          1. HERO SECTION
      ───────────────────────────────────────────── */}
      <section className="relative min-h-[90vh] w-full max-w-7xl mx-auto px-6 flex flex-col items-center justify-center text-center pt-24 pb-16 overflow-hidden">
        {/* Glow Orbs */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-tr from-[#00FFFF]/15 to-[#6C63FF]/15 rounded-full blur-[120px] pointer-events-none" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#6C63FF]/10 border border-[#6C63FF]/30 text-xs font-mono text-[#6C63FF] mb-6"
        >
          <span className="w-2 h-2 rounded-full bg-[#6C63FF] animate-pulse" />
          Raimic Labs Ecosystem
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="font-display font-extrabold text-5xl sm:text-7xl lg:text-8xl tracking-tight text-white mb-6"
        >
          Raimic <span className="text-[#00FFFF] drop-shadow-[0_0_30px_rgba(0,255,255,0.4)]">Labs</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="text-xl sm:text-2xl text-gray-300 max-w-2xl font-medium leading-relaxed mb-10"
        >
          Building developer tools <br className="hidden sm:inline" />
          <span className="text-[#00FFFF]">from the cosmos</span>
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center gap-4"
        >
          <Link
            href="/products"
            className="w-full sm:w-auto px-8 py-4 rounded-full bg-[#00FFFF] text-[#0A0A0F] font-bold text-sm tracking-wide uppercase shadow-[0_0_24px_rgba(0,255,255,0.4)] hover:shadow-[0_0_36px_rgba(0,255,255,0.6)] hover:scale-105 transition-all"
          >
            Explore Products ➔
          </Link>
          <a
            href="https://github.com/Raimic-Labs"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto px-8 py-4 rounded-full bg-white/5 border border-white/10 text-gray-200 font-semibold text-sm hover:bg-white/10 hover:border-white/20 transition-all"
          >
            View on GitHub
          </a>
        </motion.div>
      </section>

      {/* ─────────────────────────────────────────────
          2. PRODUCTS SECTION
      ───────────────────────────────────────────── */}
      <section id="products" className="w-full py-24 bg-[#0D0D14]/60 border-y border-white/5 relative z-10">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-xl mx-auto mb-16">
            <span className="font-mono text-xs text-[#00FFFF] uppercase tracking-widest">ECOSYSTEM</span>
            <h2 className="font-display text-3xl sm:text-5xl font-extrabold text-white mt-2">
              Our Products
            </h2>
            <p className="text-gray-400 text-sm mt-3">
              A suite of developer tools designed for maximum velocity and zero friction.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {PRODUCTS.map((prod, index) => (
              <motion.div
                key={prod.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="group relative bg-[#111118] border border-white/10 rounded-2xl p-8 flex flex-col justify-between hover:border-[#00FFFF]/40 transition-all duration-300 shadow-lg hover:shadow-[0_0_30px_rgba(0,255,255,0.1)]"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-display text-2xl font-bold text-white group-hover:text-[#00FFFF] transition-colors">
                      {prod.name}
                    </h3>
                    <span className={`text-[10px] font-mono font-bold px-3 py-1 rounded-full border ${prod.badgeColor}`}>
                      {prod.badge}
                    </span>
                  </div>
                  <p className="text-gray-300 text-sm leading-relaxed mb-6">
                    {prod.desc}
                  </p>
                </div>

                <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
                  {prod.isLive ? (
                    <div className="flex items-center gap-2 bg-[#0A0A0F] px-4 py-2 rounded-xl border border-[#00FFFF]/20">
                      <span className="text-xs font-mono text-[#00FFFF]">$</span>
                      <code className="text-xs font-mono text-gray-200">{prod.install}</code>
                      <CopyButton text={prod.install} />
                    </div>
                  ) : (
                    <span className="text-xs font-mono text-gray-500">{prod.install}</span>
                  )}
                  <Link
                    href={prod.link}
                    className="text-xs font-bold text-[#00FFFF] hover:underline"
                  >
                    Learn more →
                  </Link>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────
          3. ABOUT SECTION
      ───────────────────────────────────────────── */}
      <section id="about" className="w-full py-24 relative z-10">
        <div className="max-w-5xl mx-auto px-6 text-center">
          <span className="font-mono text-xs text-[#00FFFF] uppercase tracking-widest">MISSION</span>
          <h2 className="font-display text-3xl sm:text-5xl font-extrabold text-white mt-2 mb-6">
            We are Raimic Labs
          </h2>

          <p className="text-xl sm:text-2xl text-gray-300 font-medium leading-relaxed max-w-3xl mx-auto mb-12">
            “Building powerful AI tools that are free and accessible to everyone.”
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            <div className="bg-[#111118] border border-white/10 rounded-2xl p-6">
              <div className="text-2xl mb-3">✦</div>
              <h3 className="font-bold text-lg text-white mb-2">Open Source First</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                We believe core developer tools should be open, transparent, and driven by community feedback.
              </p>
            </div>
            <div className="bg-[#111118] border border-white/10 rounded-2xl p-6">
              <div className="text-2xl mb-3">⚡</div>
              <h3 className="font-bold text-lg text-white mb-2">Zero Gatekeeping</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Start for free with generous daily limits or bring your own keys from NVIDIA, Google, Groq, or DeepSeek.
              </p>
            </div>
            <div className="bg-[#111118] border border-white/10 rounded-2xl p-6">
              <div className="text-2xl mb-3">🤖</div>
              <h3 className="font-bold text-lg text-white mb-2">Multi-Agent AI</h3>
              <p className="text-gray-400 text-sm leading-relaxed">
                Autonomous agent routing automatically selects the best specialized model for every single prompt.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────────────────────────────────────
          4. CTA TEASER
      ───────────────────────────────────────────── */}
      <section className="w-full py-20 bg-gradient-to-b from-[#0D0D14] to-[#0A0A0F] border-t border-white/10 relative z-10 text-center">
        <div className="max-w-4xl mx-auto px-6 flex flex-col items-center gap-6">
          <h2 className="font-display text-3xl sm:text-4xl font-extrabold text-white">
            Ready to build at the speed of stars?
          </h2>
          <p className="text-gray-400 text-base max-w-md">
            Get started in under 30 seconds with a single terminal command.
          </p>
          <div className="flex items-center gap-4 mt-2">
            <Link
              href="/products"
              className="px-8 py-3.5 rounded-full bg-[#00FFFF] text-[#0A0A0F] font-bold text-sm uppercase shadow-[0_0_20px_rgba(0,255,255,0.4)] hover:scale-105 transition-all"
            >
              Get Vega CLI
            </Link>
            <Link
              href="/contact"
              className="px-8 py-3.5 rounded-full bg-white/5 border border-white/10 text-white font-semibold text-sm hover:bg-white/10 transition-all"
            >
              Contact Us
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}
