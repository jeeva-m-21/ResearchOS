'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
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
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import {
  fetchNotebook,
  fetchBlocks,
  createBlock,
  type Notebook,
  type Block,
} from '@/lib/api/notebooks'
import { CodeBlock } from '@/components/notebooks/CodeBlock'

// ---------- block type config ----------

const BLOCK_TYPE_CONFIG: Record<string, { icon: React.ElementType; label: string; color: string; bg: string }> = {
  markdown: {
    icon: FileText,
    label: 'Markdown',
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
  },
  python: {
    icon: Code,
    label: 'Python',
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
  },
  rust: {
    icon: Code,
    label: 'Rust',
    color: 'text-orange-600 dark:text-orange-400',
    bg: 'bg-orange-100 dark:bg-orange-900/30',
  },
  sql: {
    icon: Table,
    label: 'SQL',
    color: 'text-purple-600 dark:text-purple-400',
    bg: 'bg-purple-100 dark:bg-purple-900/30',
  },
  latex: {
    icon: Sigma,
    label: 'LaTeX',
    color: 'text-rose-600 dark:text-rose-400',
    bg: 'bg-rose-100 dark:bg-rose-900/30',
  },
  mermaid: {
    icon: Image,
    label: 'Diagram',
    color: 'text-teal-600 dark:text-teal-400',
    bg: 'bg-teal-100 dark:bg-teal-900/30',
  },
  metric: {
    icon: BarChart3,
    label: 'Metric',
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
  },
  citation: {
    icon: MessageSquareQuote,
    label: 'Citation',
    color: 'text-indigo-600 dark:text-indigo-400',
    bg: 'bg-indigo-100 dark:bg-indigo-900/30',
  },
  ai_summary: {
    icon: BrainCircuit,
    label: 'AI Summary',
    color: 'text-violet-600 dark:text-violet-400',
    bg: 'bg-violet-100 dark:bg-violet-900/30',
  },
}

const BLOCK_TYPE_NAMES = Object.keys(BLOCK_TYPE_CONFIG)

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

const EXECUTABLE_TYPES = ['python', 'rust', 'sql']

function BlockRow({ block, notebookId }: { block: Block; notebookId: string }) {
  const typeConfig = BLOCK_TYPE_CONFIG[block.block_type]
  const TypeIcon = typeConfig?.icon || FileText
  const isExecutable = EXECUTABLE_TYPES.includes(block.block_type)

  // For executable blocks, render CodeBlock (has its own card styling)
  if (isExecutable) {
    return (
      <div className="flex items-start gap-4">
        <div className="flex flex-col items-center gap-1 pt-1">
          <div className={`rounded-lg p-1.5 ${typeConfig?.bg || 'bg-muted'}`}>
            <TypeIcon className={`h-4 w-4 ${typeConfig?.color || 'text-muted-foreground'}`} />
          </div>
          <div className="w-px h-full bg-border" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`rounded-md px-1.5 py-0.5 text-[10px] font-medium ${typeConfig?.bg || 'bg-muted'} ${typeConfig?.color || 'text-muted-foreground'}`}>
              {typeConfig?.label || block.block_type}
            </span>
            <span className="text-xs text-muted-foreground">Block #{block.position + 1}</span>
            <div className="flex-1" />
            {block.language && (
              <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                {block.language}
              </span>
            )}
          </div>
          <CodeBlock block={block} notebookId={notebookId} />
        </div>
      </div>
    )
  }

  // Non-executable blocks — read-only display
  const content = block.content || ''

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
              {typeConfig?.label || block.block_type}
            </span>
            <span className="text-xs text-muted-foreground">Block #{block.position + 1}</span>
            <div className="flex-1" />
            {block.language && (
              <span className="text-[10px] text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                {block.language}
              </span>
            )}
          </div>
          <pre className="text-xs text-muted-foreground bg-muted/50 rounded-lg p-3 overflow-x-auto mt-2 font-mono leading-relaxed">
            {content || '(empty)'}
          </pre>
        </div>
      </div>
    </div>
  )
}

// ---------- create block dialog ----------

function CreateBlockDialog({
  notebookId,
  open,
  onOpenChange,
}: {
  notebookId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const queryClient = useQueryClient()
  const [blockType, setBlockType] = useState('markdown')
  const [content, setContent] = useState('')
  const [language, setLanguage] = useState('')

  const mutation = useMutation({
    mutationFn: () =>
      createBlock(notebookId, {
        block_type: blockType,
        content,
        language: language || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blocks', notebookId] })
      setBlockType('markdown')
      setContent('')
      setLanguage('')
      onOpenChange(false)
    },
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="h-4 w-4 mr-1" />
          Add Block
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Add Block</DialogTitle>
          <DialogDescription>
            Create a new block in this notebook.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="block-type">Block Type</Label>
            <Select value={blockType} onValueChange={setBlockType}>
              <SelectTrigger id="block-type">
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {BLOCK_TYPE_NAMES.map((bt) => {
                  const cfg = BLOCK_TYPE_CONFIG[bt]
                  const Icon = cfg.icon
                  return (
                    <SelectItem key={bt} value={bt}>
                      <span className="flex items-center gap-2">
                        <Icon className={`h-3.5 w-3.5 ${cfg.color}`} />
                        {cfg.label}
                      </span>
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
          </div>
          {(blockType === 'python' || blockType === 'rust' || blockType === 'sql') && (
            <div className="space-y-2">
              <Label htmlFor="language">Language (optional)</Label>
              <Input
                id="language"
                placeholder="e.g. python3, rustc, postgresql"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
              />
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="content">Content</Label>
            <Textarea
              id="content"
              placeholder={blockType === 'markdown' ? '# My Heading\n\nSome text...' : '// your code here'}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              className="font-mono text-sm"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={() => mutation.mutate()} disabled={!content.trim() || mutation.isPending}>
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Creating...
              </>
            ) : (
              'Create'
            )}
          </Button>
        </DialogFooter>
        {mutation.isError && (
          <p className="text-sm text-destructive mt-2">
            Failed to create block: {(mutation.error as Error).message}
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ---------- page ----------

export default function NotebookDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const notebookId = params.id as string
  const [createOpen, setCreateOpen] = useState(false)

  const { data: notebook, isLoading: nbLoading, isError: nbError } = useQuery({
    queryKey: ['notebook', notebookId],
    queryFn: () => fetchNotebook(notebookId),
    enabled: !!notebookId,
  })

  const { data: blocks = [], isLoading: blocksLoading } = useQuery({
    queryKey: ['blocks', notebookId],
    queryFn: () => fetchBlocks(notebookId),
    enabled: !!notebookId,
  })

  if (nbLoading) {
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

  if (nbError || !notebook) {
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
          <Button variant="outline" size="sm" onClick={() => {
            queryClient.invalidateQueries({ queryKey: ['notebook', notebookId] })
            queryClient.invalidateQueries({ queryKey: ['blocks', notebookId] })
          }}>
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <CreateBlockDialog notebookId={notebookId} open={createOpen} onOpenChange={setCreateOpen} />
        </div>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-3 gap-4">
        <InfoCard icon={Clock} label="Created" value={new Date(notebook.created_at).toLocaleDateString()} />
        <InfoCard icon={GitBranch} label="Branch" value={notebook.branch} />
        <InfoCard icon={RefreshCw} label="Updated" value={new Date(notebook.updated_at).toLocaleDateString()} />
      </div>

      {/* Block list */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-foreground">Blocks</h2>
          <span className="text-xs text-muted-foreground">
            {blocks.length} {blocks.length === 1 ? 'block' : 'blocks'}
          </span>
        </div>

        {blocksLoading ? (
          <div className="space-y-3">
            {[1, 2].map((i) => (
              <div key={i} className="h-24 bg-muted rounded-xl animate-pulse" />
            ))}
          </div>
        ) : blocks.length === 0 ? (
          <div className="rounded-xl bg-muted/50 p-8 border border-border text-center">
            <BookOpen className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No blocks yet.</p>
            <p className="text-xs text-muted-foreground/60 mt-1">
              Click "Add Block" to create your first block.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {blocks.map((block) => (
              <BlockRow key={block.id} block={block} notebookId={notebookId} />
            ))}
          </div>
        )}

        {/* Quick type reference */}
        <div className="mt-4 flex flex-wrap gap-1.5">
          {Object.entries(BLOCK_TYPE_CONFIG).map(([key, config]) => {
            const Icon = config.icon
            return (
              <span key={key} className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium ${config.bg} ${config.color}`}>
                <Icon className="h-3 w-3" />
                {config.label}
              </span>
            )
          })}
        </div>
      </div>
    </div>
  )
}
