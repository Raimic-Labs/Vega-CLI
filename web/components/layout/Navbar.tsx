'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import styles from './Navbar.module.css'

/* ─────────────────────────────────────────────
   Types
───────────────────────────────────────────── */
interface NavLink {
  label: string
  href: string
}

/* ─────────────────────────────────────────────
   Data
───────────────────────────────────────────── */
const NAV_LINKS: NavLink[] = [
  { label: 'Home',    href: '/' },
  { label: 'Chat',    href: '/chat' },
  { label: 'Build',   href: '/build' },
  { label: 'Pricing', href: '/pricing' },
  { label: 'Docs',    href: 'https://github.com/Raimic-Labs/Vega-CLI/tree/main/vega-docs' },
]

/* ─────────────────────────────────────────────
   ASCII Logo Component
───────────────────────────────────────────── */
function VegaLogo() {
  return (
    <Link href="/" className={styles.logoLink} aria-label="Vega — home">
      <span className={styles.logoAscii} aria-hidden="true">
        {'⟡'}
      </span>
      <span className={styles.logoText}>
        Vega
        <span className={styles.logoBy}> by Raimic Labs</span>
      </span>
    </Link>
  )
}

/* ─────────────────────────────────────────────
   Hamburger Icon
───────────────────────────────────────────── */
function HamburgerIcon({ open }: { open: boolean }) {
  return (
    <span className={styles.hamburgerIcon} aria-hidden="true">
      <span
        className={styles.hamburgerLine}
        style={{
          transform: open ? 'rotate(45deg) translate(5px, 5px)' : undefined,
        }}
      />
      <span
        className={styles.hamburgerLine}
        style={{
          opacity: open ? 0 : 1,
          transform: open ? 'translateX(-8px)' : undefined,
        }}
      />
      <span
        className={styles.hamburgerLine}
        style={{
          transform: open ? 'rotate(-45deg) translate(5px, -5px)' : undefined,
        }}
      />
    </span>
  )
}

/* ─────────────────────────────────────────────
   Navbar
───────────────────────────────────────────── */
export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const toggleRef = useRef<HTMLButtonElement>(null)

  /* Glassmorphism on scroll */
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  /* Close menu on outside click */
  useEffect(() => {
    if (!mobileOpen) return
    const handler = (e: MouseEvent) => {
      if (
        menuRef.current &&
        !menuRef.current.contains(e.target as Node) &&
        toggleRef.current &&
        !toggleRef.current.contains(e.target as Node)
      ) {
        setMobileOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [mobileOpen])

  /* Close menu on route change / Escape */
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileOpen(false)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

  /* Lock body scroll when mobile menu open */
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [mobileOpen])

  return (
    <>
      <header
        className={`${styles.navbar} ${scrolled ? styles.navbarScrolled : ''}`}
        role="banner"
      >
        <nav className={styles.inner} aria-label="Main navigation">
          {/* ── Logo ── */}
          <VegaLogo />

          {/* ── Desktop Links ── */}
          <ul className={styles.navLinks} role="list">
            {NAV_LINKS.map(({ label, href }) => (
              <li key={label}>
                <Link
                  href={href}
                  className={styles.navLink}
                  {...(href.startsWith('http') ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
                >
                  {label}
                </Link>
              </li>
            ))}
          </ul>

          {/* ── CTA + Hamburger ── */}
          <div className={styles.navActions}>
            <Link href="/install" className={styles.ctaButton} id="navbar-cta">
              <span className={styles.ctaGlow} aria-hidden="true" />
              Get Started
            </Link>

            <button
              ref={toggleRef}
              className={styles.hamburgerBtn}
              onClick={() => setMobileOpen((v) => !v)}
              aria-expanded={mobileOpen}
              aria-controls="mobile-menu"
              aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
              id="navbar-hamburger"
            >
              <HamburgerIcon open={mobileOpen} />
            </button>
          </div>
        </nav>
      </header>

      {/* ── Mobile Menu ── */}
      {mobileOpen && (
        <div
          className={styles.mobileOverlay}
          aria-hidden="true"
          onClick={() => setMobileOpen(false)}
        />
      )}
      <div
        ref={menuRef}
        id="mobile-menu"
        role="dialog"
        aria-modal="true"
        aria-label="Mobile navigation menu"
        className={`${styles.mobileMenu} ${mobileOpen ? styles.mobileMenuOpen : ''}`}
      >
        <ul className={styles.mobileLinks} role="list">
          {NAV_LINKS.map(({ label, href }) => (
            <li key={label}>
              <Link
                href={href}
                className={styles.mobileLinkItem}
                onClick={() => setMobileOpen(false)}
                {...(href.startsWith('http') ? { target: '_blank', rel: 'noopener noreferrer' } : {})}
              >
                {label}
              </Link>
            </li>
          ))}
        </ul>
        <Link
          href="/install"
          className={styles.mobileCtaButton}
          onClick={() => setMobileOpen(false)}
        >
          Get Started →
        </Link>
      </div>
    </>
  )
}
