'use client'

import { useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import {
  motion,
  useInView,
  useScroll,
  useTransform,
  AnimatePresence,
} from 'framer-motion'
import dynamic from 'next/dynamic'
import CopyButton from '@/components/ui/CopyButton'
import TerminalMockup from '@/components/ui/TerminalMockup'
import styles from './page.module.css'

const StarField = dynamic(() => import('@/components/ui/StarField'), { ssr: false })

/* ─────────────────────────────────────────────
   Animation variants
───────────────────────────────────────────── */
const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] as [number,number,number,number] } },
}

const stagger = (delayChildren = 0.1) => ({
  hidden: {},
  show:   { transition: { staggerChildren: delayChildren, delayChildren: 0.1 } },
})

/* ─────────────────────────────────────────────
   Data
───────────────────────────────────────────── */
const CYCLING_WORDS = ['websites', 'APIs', 'games', 'apps', 'tools', 'bots']

const STATS = [
  { value: '15+',    label: 'AI Models'      },
  { value: '100%',   label: 'Free to Start'  },
  { value: '<1s',    label: 'Time to Output' },
  { value: 'Open',   label: 'Source'         },
]

const FEATURES = [
  {
    icon:  '⟡',
    title: 'Multi-Agent AI',
    desc:  'Auto-routes every prompt to the best specialized agent — code, debug, plan, review, and more.',
    color: '#00FFFF',
  },
  {
    icon:  '⚡',
    title: 'Blazing Fast',
    desc:  'Powered by Groq + Llama 4 Scout for sub-second responses on quick Q&A and explanations.',
    color: '#FEBC2E',
  },
  {
    icon:  '🎨',
    title: 'Image Generation',
    desc:  'Ask Vega to draw, design, or describe anything visual — routed to Google Gemini Flash.',
    color: '#FF79C6',
  },
  {
    icon:  '📁',
    title: 'Project Builder',
    desc:  'One prompt → complete project on disk. Plans, generates, writes all files, opens your browser.',
    color: '#50FA7B',
  },
  {
    icon:  '🔌',
    title: 'Any API Key',
    desc:  'Bring keys from NVIDIA, Google, Groq, or DeepSeek — all free tiers supported out of the box.',
    color: '#BD93F9',
  },
  {
    icon:  '🖥️',
    title: 'Works Everywhere',
    desc:  'Use Vega in your terminal, CI pipeline, or embedded in any app. Pure Python, zero dependencies.',
    color: '#FF5555',
  },
]

const STEPS = [
  {
    num:   '01',
    title: 'Install Vega',
    desc:  'One pip command. Works on macOS, Linux, and Windows. No Docker, no config files.',
    code:  'pip install vega-raimic',
  },
  {
    num:   '02',
    title: 'Connect a free API key',
    desc:  'Run /connect and paste your NVIDIA NIM or Google key — both have generous free tiers.',
    code:  '/connect',
  },
  {
    num:   '03',
    title: 'Build something',
    desc:  'Describe what you want in plain English. Vega writes the files, you ship the product.',
    code:  '✦ › build me a SaaS dashboard',
  },
]

const MODELS = [
  { name: 'Kimi K2',      provider: 'NVIDIA NIM',  badge: '⟡',  color: '#76B900', free: true  },
  { name: 'Llama 4 Scout','provider': 'Groq',      badge: '⚡', color: '#F55036', free: true  },
  { name: 'Gemini Flash',  provider: 'Google',     badge: '🎨', color: '#4285F4', free: true  },
  { name: 'DeepSeek-V3',  provider: 'DeepSeek',   badge: '🗺',  color: '#00C4CC', free: true  },
]

/* ─────────────────────────────────────────────
   Cycling Subtitle Hook
───────────────────────────────────────────── */
function useCyclingWord(words: string[], interval = 2200) {
  const [idx, setIdx] = useState(0)
  useEffect(() => {
    const id = setInterval(() => setIdx(i => (i + 1) % words.length), interval)
    return () => clearInterval(id)
  }, [words, interval])
  return words[idx]
}

/* ─────────────────────────────────────────────
   Section Wrapper (scroll-reveal)
───────────────────────────────────────────── */
function Section({
  id,
  className,
  children,
}: {
  id?: string
  className?: string
  children: React.ReactNode
}) {
  const ref = useRef<HTMLElement>(null)
  const inView = useInView(ref, { once: true, margin: '-10% 0px' })

  return (
    <motion.section
      id={id}
      ref={ref}
      variants={stagger(0.08)}
      initial="hidden"
      animate={inView ? 'show' : 'hidden'}
      className={className}
    >
      {children}
    </motion.section>
  )
}

/* ─────────────────────────────────────────────
   PAGE
───────────────────────────────────────────── */
export default function Home() {
  const word = useCyclingWord(CYCLING_WORDS)

  /* Parallax for hero terminal */
  const heroRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] })
  const terminalY = useTransform(scrollYProgress, [0, 1], [0, 60])

  return (
    <>
      {/* ══════════════════════════════════════
          1. HERO
      ══════════════════════════════════════ */}
      <div ref={heroRef} className={styles.heroWrapper}>
        {/* Stars canvas */}
        <StarField />

        {/* Aurora orbs */}
        <div className={styles.heroAurora} aria-hidden="true">
          <div className={styles.orb1} />
          <div className={styles.orb2} />
          <div className={styles.orb3} />
        </div>

        <div className={styles.heroInner}>
          {/* Left: text */}
          <motion.div
            className={styles.heroText}
            variants={stagger(0.1)}
            initial="hidden"
            animate="show"
          >
            {/* Badge */}
            <motion.div variants={fadeUp} className={styles.heroBadge}>
              <span className={styles.heroBadgeDot} aria-hidden="true" />
              v0.1.0 is live — open source
            </motion.div>

            {/* Headline */}
            <motion.h1 variants={fadeUp} className={styles.heroHeadline}>
              Build anything
              <br />
              <span className={styles.heroHeadlineAccent}>with AI</span>
            </motion.h1>

            {/* Cycling subtitle */}
            <motion.div variants={fadeUp} className={styles.heroSubtitle}>
              <span>Generate&nbsp;</span>
              <span className={styles.heroSubtitleWrapper}>
                <AnimatePresence mode="wait">
                  <motion.span
                    key={word}
                    className={styles.heroWord}
                    initial={{ y: 24, opacity: 0, filter: 'blur(8px)' }}
                    animate={{ y: 0,  opacity: 1, filter: 'blur(0px)' }}
                    exit={{   y: -24, opacity: 0, filter: 'blur(8px)' }}
                    transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                  >
                    {word}
                  </motion.span>
                </AnimatePresence>
              </span>
              <span>&nbsp;in seconds</span>
            </motion.div>

            {/* Description */}
            <motion.p variants={fadeUp} className={styles.heroDesc}>
              Vega is an AI-powered CLI that routes your prompt to the best
              model, generates complete projects, and writes every file —
              all from your terminal.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div variants={fadeUp} className={styles.heroCtas}>
              <Link href="/install" className={styles.ctaPrimary} id="hero-start">
                <motion.span
                  className={styles.ctaGlow}
                  aria-hidden="true"
                  animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
                  transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                />
                ⟡&nbsp; Start Building Free
              </Link>

              <a
                href="https://github.com/Raimic-Labs/Vega-CLI"
                target="_blank"
                rel="noopener noreferrer"
                className={styles.ctaSecondary}
                id="hero-github"
              >
                <GithubIcon /> View on GitHub
              </a>
            </motion.div>

            {/* Social proof */}
            <motion.p variants={fadeUp} className={styles.heroHint}>
              Free forever · No credit card · 4 providers supported
            </motion.p>
          </motion.div>

          {/* Right: Terminal */}
          <motion.div
            className={styles.heroTerminal}
            style={{ y: terminalY }}
            initial={{ opacity: 0, x: 60, scale: 0.94 }}
            animate={{ opacity: 1, x: 0,  scale: 1    }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
          >
            <TerminalMockup />
          </motion.div>
        </div>
      </div>

      {/* ══════════════════════════════════════
          2. STATS BAR
      ══════════════════════════════════════ */}
      <Section className={styles.statsBar}>
        {STATS.map((s, i) => (
          <motion.div key={i} variants={fadeUp} className={styles.statItem}>
            <span className={styles.statValue}>{s.value}</span>
            <span className={styles.statLabel}>{s.label}</span>
            {i < STATS.length - 1 && (
              <span className={styles.statDivider} aria-hidden="true" />
            )}
          </motion.div>
        ))}
      </Section>

      {/* ══════════════════════════════════════
          3. FEATURES
      ══════════════════════════════════════ */}
      <Section id="features" className={styles.section}>
        <div className={styles.sectionInner}>
          <motion.div variants={fadeUp} className={styles.sectionLabel}>Features</motion.div>
          <motion.h2 variants={fadeUp} className={styles.sectionTitle}>
            Everything you need to ship faster
          </motion.h2>
          <motion.p variants={fadeUp} className={styles.sectionDesc}>
            Six specialized agents, fifteen models, four providers — all behind a single prompt.
          </motion.p>

          <motion.div variants={stagger(0.06)} className={styles.featureGrid}>
            {FEATURES.map((f, i) => (
              <FeatureCard key={i} {...f} />
            ))}
          </motion.div>
        </div>
      </Section>

      {/* ══════════════════════════════════════
          4. HOW IT WORKS
      ══════════════════════════════════════ */}
      <Section id="how-it-works" className={`${styles.section} ${styles.sectionAlt}`}>
        <div className={styles.sectionInner}>
          <motion.div variants={fadeUp} className={styles.sectionLabel}>How it works</motion.div>
          <motion.h2 variants={fadeUp} className={styles.sectionTitle}>
            From idea to code in 3 steps
          </motion.h2>

          <div className={styles.stepsRow}>
            {STEPS.map((step, i) => (
              <StepCard key={i} step={step} index={i} total={STEPS.length} />
            ))}
          </div>
        </div>
      </Section>

      {/* ══════════════════════════════════════
          5. MODELS SHOWCASE
      ══════════════════════════════════════ */}
      <Section id="models" className={styles.section}>
        <div className={styles.sectionInner}>
          <motion.div variants={fadeUp} className={styles.sectionLabel}>Powered by</motion.div>
          <motion.h2 variants={fadeUp} className={styles.sectionTitle}>
            The best free AI models in one CLI
          </motion.h2>
          <motion.p variants={fadeUp} className={styles.sectionDesc}>
            Every provider offers a generous free tier. No credit card required.
          </motion.p>

          <motion.div variants={stagger(0.08)} className={styles.modelGrid}>
            {MODELS.map((m, i) => (
              <ModelCard key={i} {...m} />
            ))}
          </motion.div>
        </div>
      </Section>

      {/* ══════════════════════════════════════
          6. CTA SECTION
      ══════════════════════════════════════ */}
      <Section id="install" className={styles.ctaSection}>
        {/* Glow orbs */}
        <div className={styles.ctaOrb1} aria-hidden="true" />
        <div className={styles.ctaOrb2} aria-hidden="true" />

        <div className={styles.ctaInner}>
          <motion.div variants={fadeUp} className={styles.sectionLabel}>Get started</motion.div>
          <motion.h2 variants={fadeUp} className={styles.ctaTitle}>
            Start building for free
          </motion.h2>
          <motion.p variants={fadeUp} className={styles.ctaDesc}>
            One command. No accounts. No subscriptions. Runs anywhere Python runs.
          </motion.p>

          {/* Install block */}
          <motion.div variants={fadeUp} className={styles.ctaInstallBlock}>
            <div className={styles.ctaInstallHeader}>
              <span className={styles.installDot} style={{ background: '#FF5F57' }} />
              <span className={styles.installDot} style={{ background: '#FEBC2E' }} />
              <span className={styles.installDot} style={{ background: '#28C840' }} />
              <span className={styles.installTermLabel}>terminal</span>
            </div>
            <div className={styles.ctaInstallBody}>
              <div className={styles.ctaInstallRow}>
                <span className={styles.installPs}>$</span>
                <code className={styles.installCmd}>pip install vega-raimic</code>
                <CopyButton text="pip install vega-raimic" />
              </div>
              <div className={styles.ctaInstallRow} style={{ marginTop: 8 }}>
                <span className={styles.installPs}>$</span>
                <code className={styles.installCmd}>vega</code>
              </div>
            </div>
          </motion.div>

          {/* CTA buttons */}
          <motion.div variants={fadeUp} className={styles.ctaButtons}>
            <Link href="/install" className={styles.ctaPrimary} id="cta-install">
              <span className={styles.ctaGlow} aria-hidden="true" />
              ⟡&nbsp; Get Started Free
            </Link>
            <a
              href="https://github.com/Raimic-Labs/Vega-CLI/tree/main/vega-docs"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.ctaSecondary}
              id="cta-docs"
            >
              Read the Docs →
            </a>
          </motion.div>

          <motion.p variants={fadeUp} className={styles.ctaNote}>
            Python 3.10+ · macOS · Linux · Windows
          </motion.p>
        </div>
      </Section>
    </>
  )
}

/* ─────────────────────────────────────────────
   Feature Card
───────────────────────────────────────────── */
function FeatureCard({
  icon, title, desc, color,
}: { icon: string; title: string; desc: string; color: string }) {
  const [hovered, setHovered] = useState(false)
  return (
    <motion.article
      variants={fadeUp}
      className={styles.featureCard}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      whileHover={{ y: -4, transition: { duration: 0.2, ease: 'easeOut' } }}
    >
      {/* Glow on hover */}
      <motion.div
        className={styles.featureCardGlow}
        style={{ background: `radial-gradient(60% 60% at 50% 120%, ${color}22 0%, transparent 100%)` }}
        animate={{ opacity: hovered ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />
      <span className={styles.featureIcon} style={{ color }}>{icon}</span>
      <h3 className={styles.featureTitle}>{title}</h3>
      <p className={styles.featureDesc}>{desc}</p>
    </motion.article>
  )
}

/* ─────────────────────────────────────────────
   Step Card
───────────────────────────────────────────── */
function StepCard({
  step, index, total,
}: { step: (typeof STEPS)[number]; index: number; total: number }) {
  const ref = useRef<HTMLDivElement>(null)
  const inView = useInView(ref, { once: true, margin: '-15% 0px' })

  return (
    <div className={styles.stepWrapper} ref={ref}>
      <motion.div
        className={styles.stepCard}
        initial={{ opacity: 0, y: 40 }}
        animate={inView ? { opacity: 1, y: 0 } : {}}
        transition={{ duration: 0.6, delay: index * 0.15, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className={styles.stepNum}>{step.num}</div>
        <h3 className={styles.stepTitle}>{step.title}</h3>
        <p className={styles.stepDesc}>{step.desc}</p>
        <div className={styles.stepCode}>
          <span className={styles.stepPs}>$</span>
          <code>{step.code}</code>
        </div>
      </motion.div>

      {/* Connector line */}
      {index < total - 1 && (
        <motion.div
          className={styles.stepConnector}
          initial={{ scaleX: 0 }}
          animate={inView ? { scaleX: 1 } : {}}
          transition={{ duration: 0.5, delay: index * 0.15 + 0.4, ease: 'easeOut' }}
          aria-hidden="true"
        />
      )}
    </div>
  )
}

/* ─────────────────────────────────────────────
   Model Card
───────────────────────────────────────────── */
function ModelCard({
  name, provider, badge, color, free,
}: { name: string; provider: string; badge: string; color: string; free: boolean }) {
  return (
    <motion.div
      variants={fadeUp}
      className={styles.modelCard}
      whileHover={{ y: -6, scale: 1.02, transition: { duration: 0.2 } }}
    >
      <div className={styles.modelBadge} style={{ background: `${color}22`, color }}>
        {badge}
      </div>
      <div className={styles.modelInfo}>
        <span className={styles.modelName}>{name}</span>
        <span className={styles.modelProvider}>{provider}</span>
      </div>
      {free && (
        <span className={styles.modelFreeBadge}>Free</span>
      )}
    </motion.div>
  )
}

/* ─────────────────────────────────────────────
   GitHub Icon
───────────────────────────────────────────── */
function GithubIcon() {
  return (
    <svg
      width="16" height="16" viewBox="0 0 24 24" fill="currentColor"
      aria-hidden="true" style={{ flexShrink: 0 }}
    >
      <path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/>
    </svg>
  )
}
