'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface Orb {
  id: number
  size: number
  x: number
  y: number
  duration: number
  delay: number
  color: string
}

interface FloatingOrbsProps {
  className?: string
  count?: number
  /**
   * @default 'blue'
   */
  variant?: 'blue' | 'purple' | 'mixed'
}

const variantColors = {
  blue: ['hsl(var(--primary) / 0.08)', 'hsl(var(--primary) / 0.04)', 'hsl(221.2 83.2% 53.3% / 0.06)'],
  purple: ['hsl(270 80% 60% / 0.08)', 'hsl(270 80% 60% / 0.04)', 'hsl(270 80% 60% / 0.06)'],
  mixed: [
    'hsl(var(--primary) / 0.08)',
    'hsl(270 80% 60% / 0.06)',
    'hsl(var(--primary) / 0.05)',
    'hsl(142 71% 45% / 0.04)',
  ],
}

export function FloatingOrbs({ className, count = 6, variant = 'mixed' }: FloatingOrbsProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Don't render during SSR to prevent hydration mismatch from Math.random()
  if (!mounted) {
    return <div className={cn('pointer-events-none fixed inset-0 overflow-hidden', className)} />
  }

  const colors = variantColors[variant]
  const orbs: Orb[] = Array.from({ length: count }, (_, i) => ({
    id: i,
    size: Math.random() * 300 + 100,
    x: Math.random() * 100,
    y: Math.random() * 100,
    duration: Math.random() * 20 + 15,
    delay: Math.random() * -10,
    color: colors[i % colors.length],
  }))

  return (
    <div className={cn('pointer-events-none fixed inset-0 overflow-hidden', className)}>
      {orbs.map((orb) => (
        <motion.div
          key={orb.id}
          className="absolute rounded-full blur-3xl"
          style={{
            width: orb.size,
            height: orb.size,
            background: orb.color,
            left: `${orb.x}%`,
            top: `${orb.y}%`,
          }}
          animate={{
            x: [0, Math.random() * 100 - 50, Math.random() * 100 - 50, 0],
            y: [0, Math.random() * 100 - 50, Math.random() * 100 - 50, 0],
            scale: [1, 1.2, 0.9, 1.05, 1],
          }}
          transition={{
            duration: orb.duration,
            delay: orb.delay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}
    </div>
  )
}
