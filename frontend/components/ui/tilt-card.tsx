'use client'

import { useRef, type ReactNode } from 'react'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { cn } from '@/lib/utils'

interface TiltCardProps {
  children: ReactNode
  className?: string
  /**
   * Max tilt angle in degrees
   * @default 8
   */
  tiltDegree?: number
  /**
   * Perspective for 3D effect
   * @default 800
   */
  perspective?: number
  /**
   * Scale on hover
   * @default 1.02
   */
  scale?: number
  /**
   * Glow effect on mouse position
   * @default true
   */
  glare?: boolean
}

export function TiltCard({
  children,
  className,
  tiltDegree = 8,
  perspective = 800,
  scale = 1.02,
  glare = true,
}: TiltCardProps) {
  const ref = useRef<HTMLDivElement>(null)

  const x = useMotionValue(0)
  const y = useMotionValue(0)

  const springConfig = { damping: 25, stiffness: 300, mass: 0.5 }
  const xSpring = useSpring(x, springConfig)
  const ySpring = useSpring(y, springConfig)

  const rotateX = useTransform(ySpring, [-0.5, 0.5], [tiltDegree, -tiltDegree])
  const rotateY = useTransform(xSpring, [-0.5, 0.5], [-tiltDegree, tiltDegree])

  const glareX = useTransform(xSpring, [-0.5, 0.5], [0, 100])
  const glareY = useTransform(ySpring, [-0.5, 0.5], [0, 100])

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return

    const width = rect.width
    const height = rect.height
    const mouseX = e.clientX - rect.left
    const mouseY = e.clientY - rect.top

    x.set(mouseX / width - 0.5)
    y.set(mouseY / height - 0.5)
  }

  const handleMouseLeave = () => {
    x.set(0)
    y.set(0)
  }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX,
        rotateY,
        transformStyle: 'preserve-3d',
        perspective,
      }}
      whileHover={{ scale }}
      className={cn('relative', className)}
    >
      {children}

      {/* Glare/spotlight effect */}
      {glare && (
        <motion.div
          className="pointer-events-none absolute inset-0 rounded-[inherit]"
          style={{
            background: `radial-gradient(circle at ${glareX}% ${glareY}%, hsl(var(--primary) / 0.08), transparent 60%)`,
          }}
        />
      )}
    </motion.div>
  )
}
