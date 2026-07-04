'use client'

import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/lib/store/auth'
import api from '@/lib/api/client'
import Link from 'next/link'
import { FlaskConical, BookOpen, FileText, Loader2 } from 'lucide-react'

async function fetchExperimentsCount(): Promise<number> {
  try {
    const res = await api.get('/api/v1/experiments?limit=1')
    const data = res.data
    // Try to get total count from response
    if (Array.isArray(data)) return data.length
    if (data.total !== undefined) return data.total
    if (data.count !== undefined) return data.count
    if (data.items && Array.isArray(data.items)) return data.items.length
    return 0
  } catch {
    return 0
  }
}

async function fetchNotebooksCount(): Promise<number> {
  try {
    const res = await api.get('/api/v1/notebooks?limit=1')
    const data = res.data
    if (Array.isArray(data)) return data.length
    if (data.total !== undefined) return data.total
    if (data.count !== undefined) return data.count
    if (data.items && Array.isArray(data.items)) return data.items.length
    return 0
  } catch {
    return 0
  }
}

function StatCard({
  title,
  value,
  icon: Icon,
  href,
  color,
}: {
  title: string
  value: number | string
  icon: React.ElementType
  href: string
  color: string
}) {
  return (
    <Link href={href}>
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">{title}</p>
          <Icon className={`h-5 w-5 ${color}`} />
        </div>
        <p className="text-2xl font-bold text-foreground mt-1">{value}</p>
      </div>
    </Link>
  )
}

export default function DashboardHome() {
  const { user, organizations } = useAuthStore()

  const {
    data: experimentsCount,
    isLoading: loadingExperiments,
  } = useQuery({
    queryKey: ['experiments-count'],
    queryFn: fetchExperimentsCount,
    retry: 1,
    staleTime: 30000,
  })

  const {
    data: notebooksCount,
    isLoading: loadingNotebooks,
  } = useQuery({
    queryKey: ['notebooks-count'],
    queryFn: fetchNotebooksCount,
    retry: 1,
    staleTime: 30000,
  })

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-foreground">
          Welcome{user?.name ? `, ${user.name}` : ''}
        </h2>
        <p className="text-muted-foreground mt-1">Here&apos;s an overview of your research.</p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Experiments"
          value={loadingExperiments ? '...' : (experimentsCount ?? 0)}
          icon={FlaskConical}
          href="/dashboard/experiments"
          color="text-blue-600"
        />
        <StatCard
          title="Notebooks"
          value={loadingNotebooks ? '...' : (notebooksCount ?? 0)}
          icon={BookOpen}
          href="/dashboard/notebooks"
          color="text-green-600"
        />
        <StatCard
          title="Papers"
          value={0}
          icon={FileText}
          href="/dashboard/papers"
          color="text-purple-600"
        />
      </div>

      {/* Organization info */}
      {organizations.length > 0 && (
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-foreground">Organizations</h2>
          <div className="mt-3 space-y-2">
            {organizations.map((org) => (
              <div key={org.organization_id} className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-foreground">{org.organization_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {org.organization_slug} &middot; {org.role}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-foreground">Quick Actions</h2>
        <div className="mt-3 flex flex-wrap gap-3">
          <Link
            href="/dashboard/experiments"
            className="rounded-lg bg-blue-50 px-4 py-2 text-sm text-blue-700 hover:bg-blue-100 transition-colors"
          >
            New Experiment
          </Link>
          <Link
            href="/dashboard/notebooks"
            className="rounded-lg bg-green-50 px-4 py-2 text-sm text-green-700 hover:bg-green-100 transition-colors"
          >
            New Notebook
          </Link>
        </div>
      </div>
    </div>
  )
}
