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
      <p className="text-sm text-muted-foreground pt-4 border-t border-border">
        Search is coming soon. Use the API or SDK to query your research graph programmatically.
      </p>
    </div>
  )
}
