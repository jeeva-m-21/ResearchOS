'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/lib/store/auth'
import { Loader2 } from 'lucide-react'
import { useHydrated } from '@/lib/hooks/useHydrated'

export default function ProtectedRoute({
  children,
}: {
  children: React.ReactNode
}) {
  const { isAuthenticated } = useAuthStore()
  const router = useRouter()
  const hydrated = useHydrated()

  useEffect(() => {
    if (hydrated && !isAuthenticated) {
      router.push('/login')
    }
  }, [hydrated, isAuthenticated, router])

  // Always show loading until hydration is complete
  // This prevents flash-of-unauthenticated-content
  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="text-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}
