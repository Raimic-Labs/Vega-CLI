'use client'

import { usePathname } from 'next/navigation'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'

export default function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isStandaloneWorkspace =
    pathname === '/chat' ||
    pathname?.startsWith('/chat/') ||
    pathname === '/build' ||
    pathname?.startsWith('/build/')

  if (isStandaloneWorkspace) {
    return <main id="main-content">{children}</main>
  }

  return (
    <>
      <Navbar />
      <main id="main-content" tabIndex={-1}>
        {children}
      </main>
      <Footer />
    </>
  )
}
