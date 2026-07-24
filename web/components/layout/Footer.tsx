import Link from 'next/link'
import styles from './Footer.module.css'

/* ─────────────────────────────────────────────
   Data
───────────────────────────────────────────── */
const FOOTER_LINKS = [
  {
    heading: 'Product',
    links: [
      { label: 'Home',     href: '/' },
      { label: 'Chat',     href: '/chat' },
      { label: 'Build',    href: '/build' },
      { label: 'Pricing',  href: '/pricing' },
    ],
  },
  {
    heading: 'Resources',
    links: [
      { label: 'Docs',          href: 'https://github.com/Raimic-Labs/Vega-CLI/tree/main/vega-docs' },
      { label: 'GitHub',        href: 'https://github.com/Raimic-Labs/Vega-CLI' },
      { label: 'Changelog',     href: '/changelog' },
      { label: 'Roadmap',       href: '/roadmap' },
    ],
  },
  {
    heading: 'Company',
    links: [
      { label: 'About',    href: '/about' },
      { label: 'Contact',  href: 'mailto:hello@raimic.dev' },
      { label: 'Twitter',  href: 'https://twitter.com/raimiclabs' },
      { label: 'PyPI',     href: 'https://pypi.org/project/vega-raimic/' },
    ],
  },
]

/* ─────────────────────────────────────────────
   Install Code Block
───────────────────────────────────────────── */
function InstallBlock() {
  return (
    <div className={styles.installBlock} role="region" aria-label="Install command">
      <div className={styles.installHeader}>
        <span className={styles.installDot} style={{ background: '#FF5F57' }} />
        <span className={styles.installDot} style={{ background: '#FEBC2E' }} />
        <span className={styles.installDot} style={{ background: '#28C840' }} />
        <span className={styles.installLabel}>terminal</span>
      </div>
      <div className={styles.installBody}>
        <span className={styles.installPrompt}>$</span>
        <code className={styles.installCmd}>pip install vega-raimic</code>
      </div>
      <div className={styles.installBody} style={{ marginTop: 4 }}>
        <span className={styles.installPrompt}>$</span>
        <code className={styles.installCmd}>vega</code>
      </div>
    </div>
  )
}

/* ─────────────────────────────────────────────
   Footer
───────────────────────────────────────────── */
export default function Footer() {
  const year = new Date().getFullYear()

  return (
    <footer className={styles.footer} role="contentinfo">
      {/* Top border glow */}
      <div className={styles.topGlow} aria-hidden="true" />

      <div className={styles.inner}>
        {/* ── Brand Column ── */}
        <div className={styles.brandCol}>
          {/* Logo */}
          <Link href="/" className={styles.logoLink} aria-label="Vega — home">
            <span className={styles.logoMark} aria-hidden="true">⟡</span>
            <span className={styles.logoText}>Vega</span>
          </Link>

          {/* Tagline */}
          <p className={styles.tagline}>
            Code at the speed of stars.
          </p>

          {/* By Raimic Labs */}
          <p className={styles.byLine}>
            Built by{' '}
            <a
              href="https://github.com/Raimic-Labs"
              target="_blank"
              rel="noopener noreferrer"
              className={styles.raimicLink}
            >
              Raimic Labs
            </a>
          </p>

          {/* Install block */}
          <InstallBlock />
        </div>

        {/* ── Link Columns ── */}
        <div className={styles.linkColumns}>
          {FOOTER_LINKS.map(({ heading, links }) => (
            <div key={heading} className={styles.linkGroup}>
              <h3 className={styles.linkGroupHeading}>{heading}</h3>
              <ul className={styles.linkList} role="list">
                {links.map(({ label, href }) => (
                  <li key={label}>
                    <Link
                      href={href}
                      className={styles.footerLink}
                      {...(href.startsWith('http') || href.startsWith('mailto')
                        ? { target: href.startsWith('mailto') ? undefined : '_blank', rel: 'noopener noreferrer' }
                        : {})}
                    >
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {/* ── Bottom Bar ── */}
      <div className={styles.bottomBar}>
        <p className={styles.copyright}>
          &copy; {year} Raimic Labs. All rights reserved.
        </p>
        <div className={styles.bottomLinks}>
          <a
            href="https://github.com/Raimic-Labs/Vega-CLI"
            target="_blank"
            rel="noopener noreferrer"
            className={styles.bottomLink}
            aria-label="GitHub repository"
          >
            GitHub
          </a>
          <span className={styles.bottomDivider} aria-hidden="true">·</span>
          <Link href="/privacy" className={styles.bottomLink}>Privacy</Link>
          <span className={styles.bottomDivider} aria-hidden="true">·</span>
          <Link href="/terms" className={styles.bottomLink}>Terms</Link>
        </div>
      </div>
    </footer>
  )
}
