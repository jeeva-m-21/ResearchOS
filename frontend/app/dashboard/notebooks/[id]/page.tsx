'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  BookOpen,
  RefreshCw,
  Plus,
  FileText,
  Code,
  Sigma,
  BarChart3,
  MessageSquareQuote,
  Image,
  Table,
  BrainCircuit,
  Clock,
  GitBranch,
  CheckCircle2,
  XCircle,
  Play,
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  fetchNotebook,
  type Notebook,
} from '@/lib/api/notebooks'

// ---------- block type config ----------

const BLOCK_TYPE_CONFIG: Record<string, { icon: React.ElementType; label: string; color: string; bg: string; preview: string }> = {
  markdown: {
    icon: FileText,
    label: 'Markdown',
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
    preview: '## Research Notes\nThis notebook documents the experimental setup for...',
  },
  python: {
    icon: Code,
    label: 'Python',
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    preview: 'import torch\nimport numpy as np\n\nmodel = torch.nn.Linear(128, 10)',
  },
  rust: {
    icon: Code,
    label: 'Rust',
    color: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    preview: 'fn main() {\n    println!("Hello, research!");\n}',
  },
  sql: {
    icon: Table,
    label: 'SQL',
    color: 'text-purple-600 dark:text-purple-400',
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    preview: 'SELECT model, AVG(accuracy) as avg_acc\nFROM experiments\nGROUP BY model\nORDER BY avg_acc DESC;',
  },
  latex: {
    icon: Sigma,
    label: 'LaTeX',
    color: 'text-rose-600 dark:text-rose-400',
    bg: 'bg-rose-100 dark:bg-rose-900/30',
    preview: '\\begin{equation}\n  L(\\theta) = -\\sum_{i} y_i \\log(\\hat{y}_i)\n\\end{equation}',
  },
  mermaid: {
    icon: Image,
    label: 'Diagram',
    color: 'text-teal-600 dark:text-teal-400',
    bg: 'bg-teal-100 dark:bg-teal-900/30',
    preview: 'graph TD\n    A[Data] --> B[Preprocess]\n    B --> C[Train]',
  },
  metric: {
    icon: BarChart3,
    label: 'Metric',
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    preview: 'accuracy: 0.9562\nloss: 0.1245\nf1: 0.9421',
  },
  citation: {
    icon: MessageSquareQuote,
    label: 'Citation',
    color: 'text-indigo-600 dark:text-indigo-400',
    bg: 'bg-indigo-100 dark:bg-indigo-900/30',
    preview: 'Vaswani et al., "Attention Is All You Need", NeurIPS 2017',
  },
  ai_summary: {
    icon: BrainCircuit,
    label: 'AI Summary',
    color: 'text-violet-600 dark:text-violet-400',
    bg: 'bg-violet-100 dark:bg-violet-900/30',
    preview: 'This experiment demonstrates that transfer learning with BERT...',
  },
}

// ---------- mock blocks for visual demo ----------

const MOCK_BLOCKS = [
  { id: '1', type: 'markdown', label: 'Introduction', status: 'success' as const },
  { id: '2', type: 'python', label: 'Data Loading', status: 'success' as const },
  { id: '3', type: 'python', label: 'Model Training', status: 'running' as const },
  { id: '4', type: 'metric', label: 'Results', status: 'pending' as const },
  { id: '5', type: 'latex', label: 'Formulation', status: 'pending' as const },
]

const EXECUTION_STATUS_CONFIG = {
  success: { icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
  failed: { icon: XCircle, color: 'text-red-500', bg: 'bg-red-100 dark:bg-red-900/30' },
  running: { icon: Play, color: 'text-blue-500', bg: 'bg-blue-100 dark:bg-blue-900/30' },
  pending: { icon: Clock, color: 'text-muted-foreground', bg: 'bg-muted' },
}

// ---------- info card ----------

function InfoCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="rounded-xl bg-card p-4 shadow-sm border border-border">
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="text-sm font-medium text-foreground">{value}</p>
    </div>
  )
}

// ---------- block row ----------

function BlockRow({ block }: { block: typeof MOCK_BLOCKS[0] }) {
  const typeConfig = BLOCK_TYPE_CONFIG[block.type]
  const execConfig = EXECUTION_STATUS_CONFIG[block.status]
  const ExecIcon = execConfig.icon
  const TypeIcon = typeConfig?.icon || FileText

  return (
    <div className="group rounded-xl bg-card p-4 shadow-sm border border-border hover:shadow-md hover:border-primary/20 transition-all duration-200">
      <div className="flex items-start gap-4">
        {/* Block number */}
        <div className="flex flex-col items-center gap-1 pt-1">
          <div className={`rounded-lg p-1.5 ${typeConfig?.bg || 'bg-muted'}`}>
            <TypeIcon className={`h-4 w-4 ${typeConfig?.color || 'text-muted-foreground'}`} />
          </div>
          <div className="w-px h-full bg-border" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-medium ${typeConfig?.bg || 'bg-muted'} ${typeConfig?.color || 'text-muted-foreground'}`}>
              {typeConfig?.label || block.type}
            </span>
            <span className="text-xs text-muted-foreground">{block.label}</span>
            <div className="flex-1" />
            <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium ${execConfig.bg} ${execConfig.color}`}>
              {block.status === 'running' ? (
                <span className="relative flex h-1.5 w-1.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
                  <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-blue-500" />
                </span>
              ) : (
                <ExecIcon className="h-3 w-3" />
              )}
              {block.status}
            </span>
          </div>
          <pre className="text-xs text-muted-foreground bg-muted/50 rounded-lg p-3 overflow-x-auto mt-2 font-mono leading-relaxed">
            {typeConfig?.preview || '// content'}
          </pre>
        </div>
      </div>
    </div>
  )
}

// ---------- page ----------

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
      <div className="space-y-4">
        <div className="h-8 w-32 bg-muted rounded-lg animate-pulse" />
        <div className="h-8 w-64 bg-muted rounded-lg animate-pulse" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-muted rounded-xl animate-pulse" />
          ))}
        </div>
        {[1, 2].map((i) => (
          <div key={i} className="h-32 bg-muted rounded-xl animate-pulse" />
        ))}
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
      {/* Back */}
      <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/notebooks')}>
        <ArrowLeft className="h-4 w-4 mr-1" /> Back to Notebooks
      </Button>

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-indigo-100 dark:bg-indigo-900/30 p-3">
            <BookOpen className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">{notebook.title}</h1>
              <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-secondary text-secondary-foreground">
                {notebook.branch}
              </span>
            </div>
            {notebook.description && (
              <p className="text-sm text-muted-foreground mt-1">{notebook.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => queryClient.invalidateQueries({ queryKey: ['notebook', notebookId] })}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <Button disabled title="Coming in next update">
            <Plus className="h-4 w-4 mr-1" />
            Add Block
          </Button>
        </div>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-3 gap-4">
        <InfoCard icon={Clock} label="Created" value={new Date(notebook.created_at).toLocaleDateString()} />
        <InfoCard icon={GitBranch} label="Branch" value={notebook.branch} />
        <InfoCard icon={RefreshCw} label="Updated" value={new Date(notebook.updated_at).toLocaleDateString()} />
      </div>

      {/* Block type legend */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-foreground">Blocks</h2>
          <span className="text-xs text-muted-foreground">
            {MOCK_BLOCKS.length} blocks
          </span>
        </div>

        {/* Quick type reference */}
        <div className="flex flex-wrap gap-1.5 mb-4">
          {Object.entries(BLOCK_TYPE_CONFIG).slice(0, 6).map(([key, config]) => {
            const Icon = config.icon
            return (
              <span key={key} className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium ${config.bg} ${config.color}`}>
                <Icon className="h-3 w-3" />
                {config.label}
              </span>
            )
          })}
        </div>

        {/* Block list */}
        <div className="space-y-3">
          {MOCK_BLOCKS.map((block, i) => (
            <BlockRow key={block.id} block={block} />
          ))}
        </div>

        {/* Info callout */}
        <div className="mt-4 rounded-xl bg-muted/50 p-4 border border-border text-center">
          <p className="text-sm text-muted-foreground">
            Block editing, reordering, and execution are coming in the next update.
          </p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Supported types: Markdown, Python, Rust, SQL, LaTeX, Mermaid, Metrics, Citations, AI Summary
          </p>
        </div>
      </div>
    </div>
  )
}
