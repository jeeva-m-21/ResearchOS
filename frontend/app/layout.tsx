import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/lib/providers'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import { StarfieldGrid } from '@/components/background/starfield-grid'
import { MouseAura } from '@/components/background/mouse-aura'
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
        <StarfieldGrid starCount={60} connectionDistance={18} />
        <MouseAura />

        {/*
          CRITICAL: ThemeToggle must be INSIDE Providers so it has
          access to next-themes ThemeProvider context.
          Otherwise useTheme() throws at runtime.
        */}
        <Providers>
          {children}

          {/* Global theme toggle — fixed bottom-right */}
          <div className="fixed bottom-6 right-6 z-50">
            <ThemeToggle />
          </div>
        </Providers>
      </body>
    </html>
  )
}
