'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import {
  BookOpen,
  Plus,
  Loader2,
  RefreshCw,
  Clock,
  ArrowRight,
  FileText,
  Code,
  Sigma,
  BarChart3,
  MessageSquareQuote,
  Image,
  Table,
  BrainCircuit,
  CheckCircle2,
  XCircle,
  AlertCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useProjectStore } from '@/lib/store/project'
import {
  fetchNotebooks,
  createNotebook,
  type Notebook,
} from '@/lib/api/notebooks'

// ---------- block type config ----------

const BLOCK_TYPE_CONFIG: Record<string, { icon: React.ElementType; label: string; color: string; bg: string }> = {
  markdown: { icon: FileText, label: 'Markdown', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-100 dark:bg-green-900/30' },
  python: { icon: Code, label: 'Python', color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30' },
  rust: { icon: Code, label: 'Rust', color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-100 dark:bg-orange-900/30' },
  sql: { icon: Table, label: 'SQL', color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-100 dark:bg-purple-900/30' },
  latex: { icon: Sigma, label: 'LaTeX', color: 'text-rose-600 dark:text-rose-400', bg: 'bg-rose-100 dark:bg-rose-900/30' },
  mermaid: { icon: Image, label: 'Diagram', color: 'text-teal-600 dark:text-teal-400', bg: 'bg-teal-100 dark:bg-teal-900/30' },
  metric: { icon: BarChart3, label: 'Metric', color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30' },
  citation: { icon: MessageSquareQuote, label: 'Citation', color: 'text-indigo-600 dark:text-indigo-400', bg: 'bg-indigo-100 dark:bg-indigo-900/30' },
  ai_summary: { icon: BrainCircuit, label: 'AI Summary', color: 'text-violet-600 dark:text-violet-400', bg: 'bg-violet-100 dark:bg-violet-900/30' },
}

function BlockTypeBadge({ type }: { type: string }) {
  const config = BLOCK_TYPE_CONFIG[type]
  if (!config) return null
  const Icon = config.icon
  return (
    <span className={`inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium ${config.bg} ${config.color}`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  )
}

// Mock block types for preview (backend doesn't expose blocks yet, so we show demo data)
const MOCK_BLOCK_TYPES = ['markdown', 'python', 'python', 'markdown', 'latex']
const MOCK_EXECUTION_STATUS: Record<string, { icon: React.ElementType; color: string; bg: string; label: string }> = {
  success: { icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-100 dark:bg-emerald-900/30', label: 'Success' },
  failed: { icon: XCircle, color: 'text-red-600', bg: 'bg-red-100 dark:bg-red-900/30', label: 'Failed' },
  pending: { icon: AlertCircle, color: 'text-muted-foreground', bg: 'bg-muted', label: 'Pending' },
}

// ---------- create dialog ----------

function CreateNotebookDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => createNotebook(title, description || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] })
      setTitle('')
      setDescription('')
      onOpenChange(false)
    },
  })

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card rounded-xl shadow-lg border border-border w-full max-w-md p-6 mx-4">
        <h2 className="text-lg font-semibold mb-4">New Notebook</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="e.g., BERT Fine-tuning Analysis"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              rows={3}
              placeholder="What will this notebook document?"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              disabled={!title.trim() || mutation.isPending}
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <BookOpen className="mr-1.5 h-4 w-4" />
                  Create Notebook
                </>
              )}
            </Button>
          </div>
        </div>
        {mutation.isError && (
          <p className="mt-3 text-sm text-destructive">
            Error: {(mutation.error as Error)?.message || 'Failed to create notebook'}
          </p>
        )}
      </div>
    </div>
  )
}

// ---------- notebook card ----------

function NotebookCard({ notebook }: { notebook: Notebook }) {
  const uniqueTypes = [...new Set(MOCK_BLOCK_TYPES)].slice(0, 4)

  return (
    <Link href={`/dashboard/notebooks/${notebook.id}`} className="h-full">
      <div className="group flex flex-col h-full rounded-xl bg-card p-5 shadow-sm border border-border hover:shadow-md hover:border-primary/20 transition-all duration-200 cursor-pointer relative overflow-hidden">
        <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        <div className="flex items-start justify-between flex-1">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-indigo-500 shrink-0" />
              <h3 className="font-semibold text-foreground truncate">{notebook.title}</h3>
            </div>
            {notebook.description && (
              <p className="text-sm text-muted-foreground mt-1.5 line-clamp-2 ml-6">
                {notebook.description}
              </p>
            )}
          </div>
          <span className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium bg-secondary text-secondary-foreground shrink-0 ml-2 mt-0.5">
            {notebook.branch}
          </span>
        </div>

        {/* Block type preview */}
        <div className="mt-3 flex items-center gap-1.5 ml-6">
          {uniqueTypes.map((type) => (
            <BlockTypeBadge key={type} type={type} />
          ))}
          <span className="text-[10px] text-muted-foreground ml-1">+{MOCK_BLOCK_TYPES.length} blocks</span>
        </div>

        {/* Footer */}
        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground shrink-0 ml-6">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date(notebook.created_at).toLocaleDateString()}
          </span>
          <span className="flex items-center gap-1 text-foreground/50 group-hover:text-foreground transition-colors">
            Open <ArrowRight className="h-3 w-3" />
          </span>
        </div>
      </div>
    </Link>
  )
}

// ---------- page ----------

export default function NotebooksPage() {
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()

  const currentProjectId = useProjectStore((s) => s.currentProjectId)

  const { data: notebooks, isLoading, isError, error } = useQuery({
    queryKey: ['notebooks', currentProjectId ?? ''],
    queryFn: () => fetchNotebooks(currentProjectId ?? undefined),
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-100 dark:bg-indigo-900/30 p-2.5">
            <BookOpen className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Notebooks</h1>
            <p className="text-sm text-muted-foreground">
              {notebooks?.length || 0} total
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['notebooks'] })}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1" />
            New Notebook
          </Button>
        </div>
      </div>

      {/* Error */}
      {isError && (
        <div className="rounded-xl bg-destructive/10 p-4 border border-destructive/20">
          <p className="text-sm text-destructive">
            Error loading notebooks: {(error as Error)?.message || 'Unknown error'}
          </p>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-xl bg-card p-5 shadow-sm border border-border animate-pulse">
              <div className="flex items-start justify-between">
                <div className="space-y-2 flex-1">
                  <div className="h-5 w-48 bg-muted rounded" />
                  <div className="h-4 w-72 bg-muted rounded" />
                </div>
                <div className="h-5 w-14 bg-muted rounded-full" />
              </div>
              <div className="mt-3 flex gap-1.5">
                {[1, 2, 3].map((j) => (
                  <div key={j} className="h-5 w-16 bg-muted rounded" />
                ))}
              </div>
              <div className="mt-3 h-4 w-32 bg-muted rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && notebooks?.length === 0 && (
        <div className="rounded-xl bg-card p-12 shadow-sm border border-border text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-indigo-100 dark:bg-indigo-900/30 mb-4">
            <BookOpen className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h3 className="text-lg font-medium text-foreground">Start your first notebook</h3>
          <p className="text-muted-foreground mt-1 max-w-sm mx-auto">
            Block-based notebooks with Markdown, Python, SQL, LaTeX, and more.
          </p>
          <div className="flex items-center justify-center gap-2 mt-3 text-xs text-muted-foreground">
            {['Markdown', 'Python', 'SQL', 'LaTeX', 'Diagrams'].map((type) => (
              <span key={type} className="rounded-md bg-muted px-2 py-1">{type}</span>
            ))}
          </div>
          <Button className="mt-6" onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Create Notebook
          </Button>
        </div>
      )}

      {/* Notebooks grid */}
      {notebooks && notebooks.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {notebooks.map((nb) => (
            <NotebookCard key={nb.id} notebook={nb} />
          ))}
        </div>
      )}

      <CreateNotebookDialog open={showCreate} onOpenChange={setShowCreate} />
    </div>
  )
}
