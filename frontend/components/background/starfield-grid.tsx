'use client'

import { useEffect, useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface Star {
  id: number
  x: number
  y: number
  size: number
  pulseDuration: number
  pulseDelay: number
  baseOpacity: number
}

interface Connection {
  from: number
  to: number
}

interface StarfieldGridProps {
  className?: string
  starCount?: number
  connectionDistance?: number
}

/**
 * Research-oriented starfield background.
 *
 * Renders a subtle graphing-paper grid with twinkling stars and
 * constellation-like connections — evoking exploration, discovery,
 * and the research graph that powers ResearchOS.
 */
export function StarfieldGrid({
  className,
  starCount = 60,
  connectionDistance = 18,
}: StarfieldGridProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  // Generate stars with random positions and animation params
  const stars: Star[] = useMemo(
    () =>
      Array.from({ length: starCount }, (_, i) => ({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 2 + 0.8,
        pulseDuration: Math.random() * 4 + 3,
        pulseDelay: Math.random() * -5,
        baseOpacity: Math.random() * 0.15 + 0.08,
      })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  )

  // Generate constellation connections between nearby stars
  const connections: Connection[] = useMemo(() => {
    const result: Connection[] = []
    for (let i = 0; i < stars.length; i++) {
      for (let j = i + 1; j < stars.length; j++) {
        const dx = stars[i].x - stars[j].x
        const dy = stars[i].y - stars[j].y
        const dist = Math.sqrt(dx * dx + dy * dy)
        if (dist < connectionDistance && Math.random() > 0.92) {
          result.push({ from: i, to: j })
        }
      }
    }
    return result
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  if (!mounted) {
    return <div className={cn('pointer-events-none fixed inset-0', className)} />
  }

  return (
    <div className={cn('pointer-events-none fixed inset-0 overflow-hidden', className)}>
      {/* Layer 1: Subtle graphing-paper grid */}
      <div
        className="absolute inset-0 opacity-[0.02] dark:opacity-[0.03]"
        style={{
          backgroundImage: [
            'linear-gradient(hsl(var(--muted-foreground)) 1px, transparent 1px)',
            'linear-gradient(90deg, hsl(var(--muted-foreground)) 1px, transparent 1px)',
          ].join(', '),
          backgroundSize: '60px 60px',
        }}
      />

      {/* Layer 2: Scattered dot pattern — organic feel, pure CSS */}
      <div
        className="absolute inset-0 opacity-[0.03] dark:opacity-[0.04]"
        style={{
          backgroundImage: [
            'radial-gradient(circle at 10px 10px, hsl(var(--muted-foreground)) 1px, transparent 1px)',
            'radial-gradient(circle at 28px 18px, hsl(var(--muted-foreground)) 0.8px, transparent 0.8px)',
            'radial-gradient(circle at 45px 40px, hsl(var(--muted-foreground)) 0.6px, transparent 0.6px)',
          ].join(', '),
          backgroundSize: '60px 60px, 70px 70px, 80px 80px',
        }}
      />

      {/* Layer 3: Constellation SVG lines */}
      <svg className="absolute inset-0 h-full w-full" aria-hidden>
        {connections.map((conn) => {
          const from = stars[conn.from]
          const to = stars[conn.to]
          return (
            <line
              key={`${conn.from}-${conn.to}`}
              x1={`${from.x}%`}
              y1={`${from.y}%`}
              x2={`${to.x}%`}
              y2={`${to.y}%`}
              className="stroke-muted-foreground/3 dark:stroke-muted-foreground/4"
              strokeWidth="0.5"
            />
          )
        })}
      </svg>

      {/* Layer 4: Twinkling stars */}
      {stars.map((star) => (
        <motion.div
          key={star.id}
          className="absolute rounded-full bg-muted-foreground"
          style={{
            width: star.size,
            height: star.size,
            left: `${star.x}%`,
            top: `${star.y}%`,
          }}
          animate={{
            opacity: [
              star.baseOpacity * 0.15,
              star.baseOpacity * 0.6,
              star.baseOpacity * 0.15,
            ],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: star.pulseDuration,
            delay: star.pulseDelay,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
        />
      ))}

    </div>
  )
}
