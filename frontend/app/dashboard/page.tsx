'use client'

import { useAuthStore } from '@/lib/store/auth'

export default function DashboardHome() {
  const { user, organizations } = useAuthStore()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome{user?.name ? `, ${user.name}` : ''}
        </h1>
        <p className="text-gray-600 mt-1">Here&apos;s an overview of your research.</p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Experiments</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">0</p>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Notebooks</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">0</p>
        </div>
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <p className="text-sm text-gray-500">Papers</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">0</p>
        </div>
      </div>

      {/* Organization info */}
      {organizations.length > 0 && (
        <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Organizations</h2>
          <div className="mt-3 space-y-2">
            {organizations.map((org) => (
              <div key={org.organization_id} className="flex items-center justify-between py-2">
                <div>
                  <p className="text-sm font-medium text-gray-900">{org.organization_name}</p>
                  <p className="text-xs text-gray-500">{org.organization_slug} &middot; {org.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick actions */}
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Quick Actions</h2>
        <div className="mt-3 flex flex-wrap gap-3">
          <a
            href="/dashboard/experiments"
            className="rounded-lg bg-blue-50 px-4 py-2 text-sm text-blue-700 hover:bg-blue-100 transition-colors"
          >
            New Experiment
          </a>
          <a
            href="/dashboard/notebooks"
            className="rounded-lg bg-green-50 px-4 py-2 text-sm text-green-700 hover:bg-green-100 transition-colors"
          >
            New Notebook
          </a>
        </div>
      </div>
    </div>
  )
}
