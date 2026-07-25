import type { Metadata } from 'next'
import { Syne, Inter } from 'next/font/google'
import Navbar from '@/components/Navbar'
import Footer from '@/components/Footer'
import StarCanvas from '@/components/StarCanvas'
import './globals.css'

const syne = Syne({
  subsets: ['latin'],
  weight: ['400', '600', '700', '800'],
  variable: '--font-syne',
  display: 'swap',
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Raimic Labs — Building developer tools from the cosmos',
  description:
    'Raimic Labs builds powerful, open source AI developer tools accessible to everyone. Creators of Vega CLI, Vega Web, and next-gen AI tools.',
  keywords: ['Raimic Labs', 'Vega CLI', 'AI developer tools', 'terminal AI', 'open source AI'],
  authors: [{ name: 'Raimic Labs', url: 'https://github.com/Raimic-Labs' }],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${syne.variable} ${inter.variable}`}>
      <body className="bg-[#0A0A0F] text-white relative">
        <StarCanvas />
        <Navbar />
        <main className="relative z-10 min-h-screen">{children}</main>
        <Footer />
      </body>
    </html>
  )
}
