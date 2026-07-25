import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="relative bg-[#0D0D14] border-t border-white/10 pt-12 pb-8 overflow-hidden">
      {/* Top Gradient Line */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-[#00FFFF] to-transparent opacity-50" />

      <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-8 mb-12">
        {/* Brand */}
        <div className="md:col-span-2 flex flex-col gap-3">
          <Link href="/" className="flex items-center gap-2 text-white font-bold text-xl">
            <span className="text-[#00FFFF]">⟡</span> Raimic Labs
          </Link>
          <p className="text-gray-400 text-sm max-w-sm leading-relaxed">
            Building powerful AI developer tools from the cosmos. Free, open source, and accessible to everyone.
          </p>
        </div>

        {/* Links */}
        <div className="flex flex-col gap-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Navigation</h4>
          <Link href="/" className="text-sm text-gray-300 hover:text-[#00FFFF] transition-colors">Home</Link>
          <Link href="/products" className="text-sm text-gray-300 hover:text-[#00FFFF] transition-colors">Products</Link>
          <Link href="/contact" className="text-sm text-gray-300 hover:text-[#00FFFF] transition-colors">Contact</Link>
        </div>

        {/* Connect */}
        <div className="flex flex-col gap-3">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Connect</h4>
          <a href="https://github.com/Raimic-Labs" target="_blank" rel="noopener noreferrer" className="text-sm text-gray-300 hover:text-[#00FFFF] transition-colors">
            GitHub
          </a>
          <a href="mailto:hello@raimic.dev" className="text-sm text-gray-300 hover:text-[#00FFFF] transition-colors">
            hello@raimic.dev
          </a>
          <a href="https://twitter.com/raimiclabs" target="_blank" rel="noopener noreferrer" className="text-sm text-gray-300 hover:text-[#00FFFF] transition-colors">
            Twitter / X
          </a>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 pt-6 border-t border-white/5 flex flex-col sm:flex-row items-center justify-between text-xs text-gray-500 gap-4">
        <p>&copy; 2026 Raimic Labs. All rights reserved.</p>
        <p className="font-mono">Building developer tools from the cosmos ✦</p>
      </div>
    </footer>
  )
}
