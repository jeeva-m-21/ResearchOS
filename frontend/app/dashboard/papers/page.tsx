'use client'

import { FileText } from 'lucide-react'

export default function PapersPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <FileText className="h-6 w-6 text-purple-600" />
        <h1 className="text-2xl font-bold text-foreground">Papers</h1>
      </div>
      <p className="text-muted-foreground">
        Compose and manage research papers with AI-assisted writing and citation management.
      </p>
      <div className="rounded-xl bg-white p-8 shadow-sm border border-gray-200 text-center">
        <FileText className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
        <p className="text-muted-foreground">No papers yet. Create your first paper to get started.</p>
      </div>
    </div>
  )
}
