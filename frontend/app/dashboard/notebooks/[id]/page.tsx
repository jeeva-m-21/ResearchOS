'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, BookOpen, RefreshCw, Plus, FileCode } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  fetchNotebook,
  type Notebook,
} from '@/lib/api/notebooks'
import { Loader2 } from 'lucide-react'

function InfoCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl bg-card p-4 shadow-sm border border-border">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium mt-1">{value}</p>
    </div>
  )
}

export default function NotebookDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const notebookId = params.id as string

  const { data: notebook, isLoading, isError } = useQuery({
    queryKey: ['notebook', notebookId],
    queryFn: () => fetchNotebook(notebookId),
    enabled: !!notebookId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (isError || !notebook) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
        <div className="rounded-xl bg-destructive/10 p-4 border border-destructive/20">
          <p className="text-sm text-destructive">Notebook not found.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div className="space-y-2">
        <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/notebooks')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Notebooks
        </Button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="h-6 w-6 text-foreground" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">{notebook.title}</h1>
              {notebook.description && (
                <p className="text-sm text-muted-foreground mt-1">{notebook.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center rounded-full px-3 py-1 text-sm font-medium bg-secondary text-secondary-foreground">
              {notebook.branch}
            </span>
            <Button
              variant="outline"
              size="icon"
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ['notebook', notebookId] })
              }}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Notebook info */}
      <div className="grid grid-cols-3 gap-4">
        <InfoCard label="Created" value={new Date(notebook.created_at).toLocaleDateString()} />
        <InfoCard label="Branch" value={notebook.branch} />
        <InfoCard label="Updated" value={new Date(notebook.updated_at).toLocaleDateString()} />
      </div>

      {/* Blocks section (placeholder — blocks API coming soon) */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-foreground">Blocks</h2>
          <Button variant="outline" size="sm" disabled>
            <Plus className="h-4 w-4 mr-1" />
            Add Block
          </Button>
        </div>
        <div className="rounded-xl bg-card p-8 shadow-sm border border-border text-center">
          <FileCode className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
          <p className="text-muted-foreground">
            Block-level editing and execution coming soon.
          </p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Notebooks support Python, SQL, Markdown, LaTeX, and more block types.
          </p>
        </div>
      </div>
    </div>
  )
}
