'use client'

import { useState } from 'react'
import Link from 'next/link'
import styles from './pricing.module.css'

const FAQS = [
  {
    q: 'Is Vega CLI really 100% free to start?',
    a: 'Yes! The Free plan gives you 50 requests per day with Kimi K2.6 powered by NVIDIA NIM, completely free of charge without requiring a credit card.',
  },
  {
    q: 'Can I bring my own API keys?',
    a: 'Absolutely. You can connect your free API keys from NVIDIA NIM, Google Gemini, Groq, or DeepSeek in your settings or via the CLI /connect command.',
  },
  {
    q: 'What is the difference between CLI and Web?',
    a: 'Vega CLI runs directly inside your local terminal and generates actual files on your hard drive. Vega Web provides a browser-based chat & project builder workspace.',
  },
  {
    q: 'How does auto agent routing work?',
    a: 'Vega analyzes your prompt keywords and intent to automatically pick the specialized agent (CodeAgent, DebugAgent, PlannerAgent, ImageAgent, etc.) best suited for the task.',
  },
]

export default function PricingPage() {
  const [isYearly, setIsYearly] = useState(true)

  const freePrice = '$0'
  const proPrice = isYearly ? '$7' : '$9'
  const teamPrice = isYearly ? '$23' : '$29'

  return (
    <div className={styles.container}>
      <div className={styles.inner}>
        {/* Header */}
        <header className={styles.header}>
          <span className={styles.badge}>✦ Simple & Transparent</span>
          <h1 className={styles.title}>Build more. Pay less.</h1>
          <p className={styles.desc}>
            Start for free with generous daily limits, or upgrade for unlimited models and priority execution.
          </p>

          {/* Monthly / Yearly Toggle */}
          <div className={styles.toggleRow}>
            <button
              onClick={() => setIsYearly(false)}
              className={`${styles.toggleBtn} ${!isYearly ? styles.toggleBtnActive : ''}`}
            >
              Monthly Billing
            </button>
            <button
              onClick={() => setIsYearly(true)}
              className={`${styles.toggleBtn} ${isYearly ? styles.toggleBtnActive : ''}`}
            >
              Yearly Billing
              <span className={styles.discountBadge}>SAVE 20%</span>
            </button>
          </div>
        </header>

        {/* Plan Cards */}
        <div className={styles.cardsGrid}>
          {/* FREE Plan */}
          <div className={styles.card}>
            <h3 className={styles.planName}>Free Starter</h3>
            <div className={styles.priceBox}>
              <span className={styles.price}>{freePrice}</span>
              <span className={styles.period}>/ month</span>
            </div>
            <p className={styles.planDesc}>Perfect for developers exploring autonomous AI coding.</p>

            <ul className={styles.featuresList}>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> 50 requests per day
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Kimi K2.6 via NVIDIA NIM
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Full CLI & Terminal Access
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Community Support
              </li>
            </ul>

            <Link href="/install" className={styles.ctaBtn} id="plan-free-cta">
              Get Started Free
            </Link>
          </div>

          {/* PRO Plan */}
          <div className={`${styles.card} ${styles.cardPopular}`}>
            <span className={styles.popularBadge}>Most Popular</span>
            <h3 className={styles.planName}>Vega Pro</h3>
            <div className={styles.priceBox}>
              <span className={styles.price}>{proPrice}</span>
              <span className={styles.period}>/ month</span>
            </div>
            <p className={styles.planDesc}>For professional engineers building apps daily.</p>

            <ul className={styles.featuresList}>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Unlimited AI Requests
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> All 15 AI Models (NVIDIA, Gemini, Groq, DeepSeek)
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> AI Image Generation Studio
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Unlimited Project Downloads (.ZIP)
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Priority Execution Speed
              </li>
            </ul>

            <Link href="/chat" className={`${styles.ctaBtn} ${styles.ctaBtnPopular}`} id="plan-pro-cta">
              ⟡ Start Pro Trial
            </Link>
          </div>

          {/* TEAM Plan */}
          <div className={styles.card}>
            <h3 className={styles.planName}>Team Workspace</h3>
            <div className={styles.priceBox}>
              <span className={styles.price}>{teamPrice}</span>
              <span className={styles.period}>/ seat / mo</span>
            </div>
            <p className={styles.planDesc}>For engineering teams collaborating on complex codebases.</p>

            <ul className={styles.featuresList}>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Includes 5 Team Seats
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Shared Team Dashboard & Keys
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> Custom Model Fine-Tuning
              </li>
              <li className={styles.featureItem}>
                <span className={styles.checkIcon}>✓</span> 24/7 Dedicated Support
              </li>
            </ul>

            <a href="mailto:hello@raimic.dev" className={styles.ctaBtn} id="plan-team-cta">
              Contact Sales
            </a>
          </div>
        </div>

        {/* FAQ Section */}
        <section className={styles.faqSection}>
          <div className={styles.header}>
            <h2 className={styles.title} style={{ fontSize: 32 }}>
              Frequently Asked Questions
            </h2>
          </div>

          <div className={styles.faqGrid}>
            {FAQS.map((faq, i) => (
              <div key={i} className={styles.faqCard}>
                <h3 className={styles.faqQuestion}>{faq.q}</h3>
                <p className={styles.faqAnswer}>{faq.a}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
