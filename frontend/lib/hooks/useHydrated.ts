'use client'

import { useEffect, useState } from 'react'

/**
 * Returns true once the component has mounted on the client.
 * Prevents hydration mismatches by suppressing SSR-dependent renders
 * until the client is fully hydrated.
 */
export function useHydrated() {
  const [hydrated, setHydrated] = useState(false)
  useEffect(() => {
    setHydrated(true)
  }, [])
  return hydrated
}
