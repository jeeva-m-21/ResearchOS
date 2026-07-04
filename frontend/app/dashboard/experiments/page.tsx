'use client'

import { FlaskConical } from 'lucide-react'

export default function ExperimentsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <FlaskConical className="h-6 w-6 text-blue-600" />
        <h1 className="text-2xl font-bold text-foreground">Experiments</h1>
      </div>
      <p className="text-muted-foreground">
        Manage your machine learning experiments. Track runs, log metrics, and compare results.
      </p>
      <div className="rounded-xl bg-white p-8 shadow-sm border border-gray-200 text-center">
        <FlaskConical className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
        <p className="text-muted-foreground">No experiments yet. Create your first experiment to get started.</p>
      </div>
    </div>
  )
}
