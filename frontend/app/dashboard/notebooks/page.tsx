'use client'

import { BookOpen } from 'lucide-react'

export default function NotebooksPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <BookOpen className="h-6 w-6 text-green-600" />
        <h1 className="text-2xl font-bold text-foreground">Notebooks</h1>
      </div>
      <p className="text-muted-foreground">
        Create and manage block-based research notebooks with executable code blocks.
      </p>
      <div className="rounded-xl bg-white p-8 shadow-sm border border-gray-200 text-center">
        <BookOpen className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
        <p className="text-muted-foreground">No notebooks yet. Create your first notebook to get started.</p>
      </div>
    </div>
  )
}
