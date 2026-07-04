'use client'

import { Search } from 'lucide-react'

export default function SearchPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Search className="h-6 w-6 text-foreground" />
        <h1 className="text-2xl font-bold text-foreground">Search</h1>
      </div>
      <p className="text-muted-foreground">
        Search across all your research assets with semantic and keyword search.
      </p>
      <div className="rounded-xl bg-white p-8 shadow-sm border border-gray-200 text-center">
        <Search className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
        <p className="text-muted-foreground">Use the search box above to find experiments, notebooks, papers, and more.</p>
      </div>
    </div>
  )
}
