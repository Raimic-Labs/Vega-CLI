'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 h-16 flex items-center transition-all duration-300 ${
        scrolled
          ? 'bg-[#0A0A0F]/80 backdrop-blur-md border-b border-white/10 shadow-lg'
          : 'bg-transparent border-b border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6 w-full flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-[#00FFFF]/10 border border-[#00FFFF]/30 flex items-center justify-center text-[#00FFFF] font-mono text-base shadow-[0_0_12px_rgba(0,255,255,0.2)] group-hover:shadow-[0_0_20px_rgba(0,255,255,0.4)] transition-all">
            ⟡
          </div>
          <span className="font-bold text-lg tracking-tight text-white group-hover:text-[#00FFFF] transition-colors">
            Raimic <span className="text-[#00FFFF]">Labs</span>
          </span>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-1">
          <Link
            href="/"
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 transition-all"
          >
            Home
          </Link>
          <Link
            href="/products"
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 transition-all"
          >
            Products
          </Link>
          <Link
            href="/contact"
            className="px-4 py-2 rounded-lg text-sm font-medium text-gray-300 hover:text-white hover:bg-white/5 transition-all"
          >
            Contact
          </Link>
        </nav>

        {/* CTA Button */}
        <a
          href="https://github.com/Raimic-Labs"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden sm:inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#00FFFF] text-[#0A0A0F] font-bold text-xs tracking-wide uppercase shadow-[0_0_16px_rgba(0,255,255,0.3)] hover:shadow-[0_0_24px_rgba(0,255,255,0.5)] hover:scale-105 transition-all"
        >
          GitHub ➔
        </a>
      </div>
    </header>
  )
}
