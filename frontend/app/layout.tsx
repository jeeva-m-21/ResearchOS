import type { Metadata } from 'next'
import './globals.css'
import { Providers } from '@/lib/providers'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import { AuroraBackground } from '@/components/background/aurora-background'
import { MorphingBlobs } from '@/components/background/morphing-blobs'
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
        <MorphingBlobs count={4} />

        {/* Global theme toggle — fixed bottom-right */}
        <div className="fixed bottom-6 right-6 z-50">
          <ThemeToggle />
        </div>

        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
