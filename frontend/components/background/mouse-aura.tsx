'use client'

import { useEffect, useRef, useCallback } from 'react'

/**
 * Subtle mouse-following radial gradient.
 * Renders a faint glow that follows the cursor, creating a gentle
 * interactive atmosphere without distracting from content.
 *
 * Fully passive — pointer-events: none, no DOM thrashing.
 */
export function MouseAura() {
  const ref = useRef<HTMLDivElement>(null)
  const raf = useRef(0)

  const handleMouse = useCallback((e: MouseEvent) => {
    if (raf.current) return
    raf.current = requestAnimationFrame(() => {
      raf.current = 0
      if (!ref.current) return
      const x = (e.clientX / window.innerWidth) * 100
      const y = (e.clientY / window.innerHeight) * 100
      ref.current.style.background = `radial-gradient(600px circle at ${x}% ${y}%, hsl(var(--foreground) / 0.04) 0%, transparent 70%)`
    })
  }, [])

  useEffect(() => {
    window.addEventListener('mousemove', handleMouse, { passive: true })
    return () => {
      window.removeEventListener('mousemove', handleMouse)
      if (raf.current) cancelAnimationFrame(raf.current)
    }
  }, [handleMouse])

  return (
    <div
      ref={ref}
      className="pointer-events-none fixed inset-0 z-10"
      style={{ background: 'transparent' }}
      aria-hidden
    />
  )
}
