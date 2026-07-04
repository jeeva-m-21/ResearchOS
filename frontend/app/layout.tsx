import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/lib/providers'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import { AuroraBackground } from '@/components/background/aurora-background'
import { FloatingOrbs } from '@/components/background/floating-orbs'
import { ThemeToggle } from '@/components/theme-toggle'

export const metadata: Metadata = {
  title: 'ResearchOS',
  description: 'The research operating system for AI/ML teams',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body className="relative">
        <AuroraBackground variant="neutral" speed={0.8} opacity={0.25} />
        <FloatingOrbs count={5} variant="mixed" />

        {/* Global theme toggle — fixed top-right on every page */}
        <div className="fixed top-4 right-4 z-50">
          <ThemeToggle />
        </div>

        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
