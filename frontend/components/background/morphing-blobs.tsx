'use client'

import { useEffect, useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

interface Blob {
  id: number
  initialSize: number
  initialX: number
  initialY: number
  duration: number
  color: string
  borderRadius: string
}

interface MorphingBlobsProps {
  className?: string
  count?: number
}

/**
 * Organic morphing blobs that smoothly change shape, size, and position.
 * More creative than floating orbs — each blob has a unique border-radius
 * that animates to create fluid, organic shape-shifting.
 */
export function MorphingBlobs({ className, count = 4 }: MorphingBlobsProps) {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  const blobs: Blob[] = useMemo(
    () =>
      Array.from({ length: count }, (_, i) => {
        // Generate a unique organic-looking initial border-radius
        const r1 = 30 + Math.random() * 40
        const r2 = 30 + Math.random() * 40
        const r3 = 30 + Math.random() * 40
        const r4 = 30 + Math.random() * 40
        return {
          id: i,
          initialSize: 200 + Math.random() * 400,
          initialX: Math.random() * 100,
          initialY: Math.random() * 100,
          duration: 25 + Math.random() * 20,
          color: i % 2 === 0
            ? 'hsla(0, 0%, 100%, 0.03)'
            : 'hsla(0, 0%, 100%, 0.02)',
          borderRadius: `${r1}% ${r2}% ${r3}% ${r4}% / ${r4}% ${r3}% ${r2}% ${r1}%`,
        }
      }),
    [count],
  )

  if (!mounted) {
    return <div className={cn('pointer-events-none fixed inset-0 overflow-hidden', className)} />
  }

  return (
    <div className={cn('pointer-events-none fixed inset-0 overflow-hidden', className)}>
      {blobs.map((blob) => {
        // Generate random animation targets once per mount
        const moveX = [0, (Math.random() - 0.5) * 300, (Math.random() - 0.5) * 300, 0]
        const moveY = [0, (Math.random() - 0.5) * 300, (Math.random() - 0.5) * 300, 0]
        const scaleSequence = [1, 1.3 + Math.random() * 0.5, 0.8 + Math.random() * 0.3, 1.1, 1]

        // Generate morphing borderRadius keyframes
        const br1 = 25 + Math.random() * 45
        const br2 = 25 + Math.random() * 45
        const br3 = 25 + Math.random() * 45
        const br4 = 25 + Math.random() * 45
        const borderRadiusSequence = [
          blob.borderRadius,
          `${br1}% ${br2}% ${br3}% ${br4}% / ${br4}% ${br3}% ${br2}% ${br1}%`,
          `${br3}% ${br1}% ${br4}% ${br2}% / ${br2}% ${br4}% ${br1}% ${br3}%`,
          blob.borderRadius,
        ]

        return (
          <motion.div
            key={blob.id}
            className="absolute blur-3xl will-change-transform"
            style={{
              width: blob.initialSize,
              height: blob.initialSize,
              background: blob.color,
              left: `${blob.initialX}%`,
              top: `${blob.initialY}%`,
              borderRadius: blob.borderRadius,
            }}
            animate={{
              x: moveX,
              y: moveY,
              scale: scaleSequence,
              borderRadius: borderRadiusSequence,
            }}
            transition={{
              duration: blob.duration,
              repeat: Infinity,
              ease: 'easeInOut',
              times: [0, 0.33, 0.66, 1],
            }}
          />
        )
      })}
    </div>
  )
}
