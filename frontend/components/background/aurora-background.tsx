'use client'

import { useEffect, useRef } from 'react'
import { cn } from '@/lib/utils'

interface AuroraBackgroundProps {
  className?: string
  /**
   * Color scheme variant
   * @default 'blue'
   */
  variant?: 'blue' | 'purple' | 'green' | 'neutral'
  /**
   * Speed multiplier (1 = normal)
   * @default 1
   */
  speed?: number
  /**
   * Opacity of the aurora effect
   * @default 0.4
   */
  opacity?: number
}

const variantColors = {
  blue: {
    light: ['hsl(221.2 83.2% 53.3% / 0.15)', 'hsl(221.2 83.2% 53.3% / 0.05)', 'hsl(221.2 83.2% 53.3% / 0.02)'],
    dark: ['hsl(217.2 91.2% 59.8% / 0.12)', 'hsl(217.2 91.2% 59.8% / 0.05)', 'hsl(217.2 91.2% 59.8% / 0.02)'],
  },
  purple: {
    light: ['hsl(270 80% 60% / 0.15)', 'hsl(270 80% 60% / 0.05)', 'hsl(270 80% 60% / 0.02)'],
    dark: ['hsl(270 80% 60% / 0.12)', 'hsl(270 80% 60% / 0.05)', 'hsl(270 80% 60% / 0.02)'],
  },
  green: {
    light: ['hsl(142 71% 45% / 0.15)', 'hsl(142 71% 45% / 0.05)', 'hsl(142 71% 45% / 0.02)'],
    dark: ['hsl(142 71% 45% / 0.12)', 'hsl(142 71% 45% / 0.05)', 'hsl(142 71% 45% / 0.02)'],
  },
  neutral: {
    light: ['hsl(0 0% 50% / 0.08)', 'hsl(0 0% 50% / 0.03)', 'hsl(0 0% 50% / 0.01)'],
    dark: ['hsl(0 0% 60% / 0.06)', 'hsl(0 0% 60% / 0.02)', 'hsl(0 0% 60% / 0.01)'],
  },
}

export function AuroraBackground({
  className,
  variant = 'blue',
  speed = 1,
  opacity = 0.4,
}: AuroraBackgroundProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const handleMouseMove = (e: MouseEvent) => {
      const { left, top, width, height } = container.getBoundingClientRect()
      const x = (e.clientX - left) / width
      const y = (e.clientY - top) / height

      // Subtle parallax shift on the aurora layers
      container.style.setProperty('--aurora-x', String(x))
      container.style.setProperty('--aurora-y', String(y))
    }

    window.addEventListener('mousemove', handleMouseMove)
    return () => window.removeEventListener('mousemove', handleMouseMove)
  }, [])

  return (
    <div
      ref={containerRef}
      className={cn('pointer-events-none fixed inset-0 overflow-hidden', className)}
      style={
        {
          '--aurora-x': '0.5',
          '--aurora-y': '0.5',
        } as React.CSSProperties
      }
    >
      {/* Aurora gradients - three large blurred blobs that drift */}
      <div
        className="absolute inset-0 transition-all duration-1000 ease-out"
        style={{
          background: [
            `radial-gradient(ellipse 80% 60% at calc(var(--aurora-x, 0.5) * 100%) calc(var(--aurora-y, 0.5) * 100%), var(--aurora-color-1, transparent) 0%, transparent 70%)`,
            `radial-gradient(ellipse 60% 50% at calc((1 - var(--aurora-x, 0.5)) * 100%) calc((1 - var(--aurora-y, 0.5)) * 100%), var(--aurora-color-2, transparent) 0%, transparent 60%)`,
            `radial-gradient(ellipse 50% 40% at calc(var(--aurora-x, 0.5) * 80% + 10%) calc(var(--aurora-y, 0.5) * 80% + 10%), var(--aurora-color-3, transparent) 0%, transparent 50%)`,
          ].join(', '),
          opacity,
        }}
      />

      {/* Drifting horizontal bands */}
      <div
        className="aurora-band-1 absolute inset-0"
        style={{
          background: `linear-gradient(90deg, transparent, var(--aurora-color-1, transparent), var(--aurora-color-2, transparent), transparent)`,
          backgroundSize: '200% 100%',
          animation: `auroraDrift ${12 / speed}s ease-in-out infinite`,
          opacity: opacity * 0.6,
        }}
      />
      <div
        className="aurora-band-2 absolute inset-0"
        style={{
          background: `linear-gradient(90deg, transparent, var(--aurora-color-2, transparent), var(--aurora-color-3, transparent), transparent)`,
          backgroundSize: '200% 100%',
          animation: `auroraDrift ${18 / speed}s ease-in-out infinite reverse`,
          opacity: opacity * 0.4,
        }}
      />
      <div
        className="aurora-band-3 absolute inset-0"
        style={{
          background: `linear-gradient(120deg, transparent, var(--aurora-color-1, transparent), transparent, var(--aurora-color-3, transparent), transparent)`,
          backgroundSize: '200% 100%',
          animation: `auroraDrift ${22 / speed}s ease-in-out infinite`,
          opacity: opacity * 0.3,
        }}
      />

      {/* Vignette overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: `radial-gradient(ellipse at center, transparent 40%, hsl(var(--background)) 100%)`,
        }}
      />
    </div>
  )
}
