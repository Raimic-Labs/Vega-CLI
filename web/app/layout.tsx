import type { Metadata, Viewport } from 'next'
import { Syne, JetBrains_Mono } from 'next/font/google'
import AppLayoutWrapper from '@/components/layout/AppLayoutWrapper'
import './globals.css'

/* ─────────────────────────────────────────────
   Fonts
───────────────────────────────────────────── */
const syne = Syne({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-syne',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  style: ['normal', 'italic'],
  variable: '--font-mono',
  display: 'swap',
})

/* ─────────────────────────────────────────────
   Metadata
───────────────────────────────────────────── */
export const metadata: Metadata = {
  title: {
    default: 'Vega — Code at the speed of stars',
    template: '%s | Vega by Raimic Labs',
  },
  description:
    'Vega is an AI-powered CLI that builds full-stack projects, scripts, and APIs right in your terminal. Powered by NVIDIA, Google, Groq, and DeepSeek.',
  keywords: [
    'Vega CLI', 'AI coding assistant', 'terminal AI', 'code generation',
    'NVIDIA NIM', 'Gemini', 'Groq', 'DeepSeek', 'Raimic Labs',
  ],
  authors: [{ name: 'Raimic Labs', url: 'https://github.com/Raimic-Labs' }],
  creator: 'Raimic Labs',
  publisher: 'Raimic Labs',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    siteName: 'Vega by Raimic Labs',
    title: 'Vega — Code at the speed of stars',
    description:
      'An AI-powered CLI that builds full-stack projects, scripts, and APIs right in your terminal.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Vega — Code at the speed of stars',
    description:
      'An AI-powered CLI that builds full-stack projects, scripts, and APIs right in your terminal.',
    creator: '@raimiclabs',
  },
  robots: {
    index: true,
    follow: true,
  },
  metadataBase: new URL('https://vegacli.raimic.dev'),
}

export const viewport: Viewport = {
  themeColor: '#0A0A0F',
  width: 'device-width',
  initialScale: 1,
  colorScheme: 'dark',
}

/* ─────────────────────────────────────────────
   Root Layout
───────────────────────────────────────────── */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html
      lang="en"
      className={`${syne.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <body>
        {/* Noise texture overlay for depth */}
        <div className="noise-overlay" aria-hidden="true" />
        <AppLayoutWrapper>{children}</AppLayoutWrapper>
      </body>
    </html>
  )
}
