'use client'

import { useEffect, useRef, useState } from 'react'
import styles from './TerminalMockup.module.css'

const LINES = [
  { delay: 0,    text: '$ vega',                                prompt: true  },
  { delay: 800,  text: '',                                       prompt: false },
  { delay: 900,  text: '  ██╗   ██╗███████╗ ██████╗  █████╗',   prompt: false },
  { delay: 950,  text: '  ██║   ██║██╔════╝██╔════╝ ██╔══██╗', prompt: false },
  { delay: 1000, text: '  ██║   ██║█████╗  ██║  ███╗███████║',  prompt: false },
  { delay: 1050, text: '  ╚██╗ ██╔╝██╔══╝  ██║   ██║██╔══██║', prompt: false },
  { delay: 1100, text: '   ╚████╔╝ ███████╗╚██████╔╝██║  ██║',  prompt: false },
  { delay: 1150, text: '    ╚═══╝  ╚══════╝ ╚═════╝ ╚═╝  ╚═╝', prompt: false },
  { delay: 1200, text: '',                                        prompt: false },
  { delay: 1300, text: '  ✦ Vega v0.1.0 — Code at the speed of stars', prompt: false, cyan: true },
  { delay: 1500, text: '  ✦ Vega is ready. Type /help for commands.',    prompt: false, cyan: true },
  { delay: 1700, text: '',                                        prompt: false },
  { delay: 1900, text: '  ✦ › build me a SaaS landing page',    prompt: false, input: true },
  { delay: 2500, text: '',                                        prompt: false },
  { delay: 2700, text: '  ⟡ CodeAgent active (Kimi K2)',         prompt: false, agent: true },
  { delay: 3000, text: '  ✦ Planning project structure…',        prompt: false, dim: true  },
  { delay: 3400, text: '  ✦ Generating files… [████████████░] 9/11', prompt: false, dim: true },
  { delay: 4200, text: '  ✦ Build complete! 11 files → ./saas-landing/', prompt: false, success: true },
  { delay: 4600, text: '',                                        prompt: false },
  { delay: 4800, text: '  Open index.html in browser? [y/N] y',  prompt: false, input: true },
  { delay: 5200, text: '  ✔  Opened → /saas-landing/index.html', prompt: false, success: true },
]

export default function TerminalMockup() {
  const [visibleCount, setVisibleCount] = useState(0)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = []
    LINES.forEach((_, i) => {
      timers.push(
        setTimeout(() => setVisibleCount(i + 1), LINES[i].delay)
      )
    })
    return () => timers.forEach(clearTimeout)
  }, [])

  // Auto-scroll to bottom as lines appear
  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight
    }
  }, [visibleCount])

  return (
    <div className={styles.window}>
      {/* Traffic-light dots */}
      <div className={styles.titleBar}>
        <span className={styles.dot} style={{ background: '#FF5F57' }} />
        <span className={styles.dot} style={{ background: '#FEBC2E' }} />
        <span className={styles.dot} style={{ background: '#28C840' }} />
        <span className={styles.title}>terminal — vega</span>
      </div>

      {/* Output */}
      <div ref={containerRef} className={styles.body}>
        {LINES.slice(0, visibleCount).map((line, i) => (
          <div
            key={i}
            className={`${styles.line}
              ${line.prompt  ? styles.prompt  : ''}
              ${line.cyan    ? styles.cyan    : ''}
              ${line.dim     ? styles.dim     : ''}
              ${line.agent   ? styles.agent   : ''}
              ${line.input   ? styles.input   : ''}
              ${line.success ? styles.success : ''}
            `}
          >
            {line.prompt && <span className={styles.promptChar}>$</span>}
            <span>{line.text || '\u00A0'}</span>
            {/* Blinking cursor on last visible line */}
            {i === visibleCount - 1 && visibleCount < LINES.length && (
              <span className={styles.cursor} aria-hidden="true">▋</span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
