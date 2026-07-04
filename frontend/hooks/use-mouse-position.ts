'use client'

import { useCallback, useEffect, useRef, useState } from 'react'

interface MousePosition {
  x: number
  y: number
}

/**
 * Tracks mouse position relative to the viewport.
 * Uses requestAnimationFrame for smooth updates.
 */
export function useMousePosition(): MousePosition {
  const [position, setPosition] = useState<MousePosition>({ x: 0, y: 0 })
  const rafRef = useRef<number | null>(null)

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (rafRef.current !== null) return
    rafRef.current = requestAnimationFrame(() => {
      setPosition({ x: e.clientX, y: e.clientY })
      rafRef.current = null
    })
  }, [])

  useEffect(() => {
    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      if (rafRef.current !== null) {
        cancelAnimationFrame(rafRef.current)
      }
    }
  }, [handleMouseMove])

  return position
}

interface ElementMousePosition {
  x: number
  y: number
  centerX: number
  centerY: number
  isInside: boolean
}

/**
 * Tracks mouse position relative to a specific element.
 * Returns normalized center coordinates (-1 to 1) and whether the mouse is inside.
 */
export function useElementMousePosition<T extends HTMLElement>(): [
  React.RefObject<T | null>,
  ElementMousePosition,
] {
  const ref = useRef<T | null>(null)
  const [position, setPosition] = useState<ElementMousePosition>({
    x: 0,
    y: 0,
    centerX: 0,
    centerY: 0,
    isInside: false,
  })

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const handleMouseMove = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      setPosition({
        x,
        y,
        centerX: (x / rect.width - 0.5) * 2,
        centerY: (y / rect.height - 0.5) * 2,
        isInside: true,
      })
    }

    const handleMouseLeave = () => {
      setPosition((prev) => ({ ...prev, isInside: false }))
    }

    el.addEventListener('mousemove', handleMouseMove)
    el.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      el.removeEventListener('mousemove', handleMouseMove)
      el.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [])

  return [ref, position]
}
