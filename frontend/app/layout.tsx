import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/lib/providers'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import { AuroraBackground } from '@/components/background/aurora-background'
import { FloatingOrbs } from '@/components/background/floating-orbs'

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
        <AuroraBackground variant="blue" speed={0.8} opacity={0.35} />
        <FloatingOrbs count={5} variant="mixed" />
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
