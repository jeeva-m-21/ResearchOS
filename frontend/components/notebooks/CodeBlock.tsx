'use client'

import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  Terminal,
  Pencil,
  Save,
  Clock,
  History,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  executeBlock,
  fetchExecutions,
  updateBlock,
  type Block,
  type Execution,
} from '@/lib/api/notebooks'

interface CodeBlockProps {
  block: Block
  notebookId: string
}

interface ExecutionResult {
  execution_id: string
  status: string
  output: string | null
  error: string | null
  duration_ms: number | null
}

export function CodeBlock({ block, notebookId }: CodeBlockProps) {
  const queryClient = useQueryClient()
  const [execution, setExecution] = useState<ExecutionResult | null>(null)
  const [isEditing, setIsEditing] = useState(false)
  const [editContent, setEditContent] = useState(block.content || '')
  const [showHistory, setShowHistory] = useState(false)
  const content = block.content || ''

  // ── Run mutation ──────────────────────────────────────────────────

  const runMutation = useMutation({
    mutationFn: () => executeBlock(notebookId, block.id),
    onSuccess: (data) => {
      setExecution(data)
      // Refresh execution history after a successful run
      queryClient.invalidateQueries({ queryKey: ['executions', notebookId, block.id] })
    },
    onError: (err: Error) => {
      setExecution({
        execution_id: '',
        status: 'failed',
        output: null,
        error: err.message || 'Execution failed',
        duration_ms: null,
      })
    },
  })

  // ── Update mutation ───────────────────────────────────────────────

  const updateMutation = useMutation({
    mutationFn: (data: { content: string }) =>
      updateBlock(notebookId, block.id, { content: data.content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['blocks', notebookId] })
      setIsEditing(false)
    },
  })

  // ── Execution history query ───────────────────────────────────────

  const { data: executions = [] } = useQuery({
    queryKey: ['executions', notebookId, block.id],
    queryFn: () => fetchExecutions(notebookId, block.id, { limit: 10 }),
    enabled: showHistory,
  })

  // ── Handlers ──────────────────────────────────────────────────────

  const handleStartEdit = () => {
    setEditContent(content)
    setIsEditing(true)
  }

  const handleCancelEdit = () => {
    setEditContent(content)
    setIsEditing(false)
  }

  const handleSave = () => {
    updateMutation.mutate({ content: editContent })
  }

  // ── Render ────────────────────────────────────────────────────────

  return (
    <div className="rounded-xl bg-card p-4 shadow-sm border border-border hover:shadow-md hover:border-primary/20 transition-all duration-200">
      {/* Code display / edit area */}
      {isEditing ? (
        <div className="space-y-2">
          <Textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={Math.max(6, (editContent.match(/\n/g)?.length || 0) + 2)}
            className="font-mono text-sm min-h-[120px]"
            autoFocus
          />
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleSave}
              disabled={updateMutation.isPending || editContent === content}
            >
              {updateMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
              ) : (
                <Save className="h-3.5 w-3.5 mr-1" />
              )}
              Save
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={handleCancelEdit}
              disabled={updateMutation.isPending}
            >
              Cancel
            </Button>
            {updateMutation.isError && (
              <span className="text-xs text-destructive">
                Save failed: {(updateMutation.error as Error).message}
              </span>
            )}
          </div>
        </div>
      ) : (
        <div className="relative group/code">
          <pre className="text-xs text-muted-foreground bg-muted/50 rounded-lg p-3 overflow-x-auto font-mono leading-relaxed">
            {content || '(empty)'}
          </pre>
          <div className="absolute top-2 right-2 flex items-center gap-1">
            <button
              onClick={handleStartEdit}
              className="opacity-0 group-hover/code:opacity-100 transition-opacity rounded-md p-1.5 hover:bg-muted-foreground/10 text-muted-foreground hover:text-foreground"
              title="Edit code"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => runMutation.mutate()}
              disabled={runMutation.isPending || !content.trim()}
              className="h-7 text-xs gap-1"
            >
              {runMutation.isPending ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="h-3.5 w-3.5" />
              )}
              <span>Run</span>
            </Button>
          </div>
        </div>
      )}

      {/* Loading indicator */}
      {runMutation.isPending && (
        <div className="mt-3 rounded-lg bg-black/5 dark:bg-white/5 p-3 border border-border">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" />
            Running...
          </div>
        </div>
      )}

      {/* Output panel */}
      {execution && !runMutation.isPending && !isEditing && (
        <div className="mt-3 rounded-lg bg-black/5 dark:bg-white/5 border border-border overflow-hidden">
          {/* Status bar */}
          <div className="flex items-center justify-between px-3 py-1.5 border-b border-border bg-muted/30">
            <div className="flex items-center gap-2">
              <Terminal className="h-3 w-3 text-muted-foreground" />
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                Output
              </span>
            </div>
            <div className="flex items-center gap-2">
              {execution.status === 'success' ? (
                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-green-600 dark:text-green-400">
                  <CheckCircle2 className="h-3 w-3" />
                  Success
                </span>
              ) : execution.status === 'running' ? (
                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-blue-600 dark:text-blue-400">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Running
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[10px] font-medium text-red-600 dark:text-red-400">
                  <XCircle className="h-3 w-3" />
                  {execution.status === 'timeout' ? 'Timeout' : 'Failed'}
                </span>
              )}
            </div>
          </div>

          {/* Output content */}
          <pre className="p-3 text-xs font-mono leading-relaxed overflow-x-auto max-h-60 overflow-y-auto">
            {execution.error ? (
              <span className="text-red-600 dark:text-red-400">{execution.error}</span>
            ) : execution.output ? (
              <span className="text-foreground">{execution.output}</span>
            ) : (
              <span className="text-muted-foreground italic">No output</span>
            )}
          </pre>

          {/* Duration footer */}
          {execution.duration_ms !== null && (
            <div className="px-3 py-1 border-t border-border text-[10px] text-muted-foreground">
              Completed in {execution.duration_ms}ms
            </div>
          )}
        </div>
      )}

      {/* Execution history toggle */}
      <div className="mt-2">
        <button
          onClick={() => setShowHistory(!showHistory)}
          className="inline-flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        >
          <History className="h-3 w-3" />
          {showHistory ? 'Hide History' : 'Execution History'}
        </button>

        {showHistory && (
          <div className="mt-2 space-y-1">
            {executions.length === 0 ? (
              <p className="text-[10px] text-muted-foreground italic px-1">No executions yet.</p>
            ) : (
              executions.map((ex: Execution) => (
                <div
                  key={ex.id}
                  className="flex items-center gap-2 rounded-md px-2 py-1.5 bg-muted/30 border border-border"
                >
                  <div className="flex-shrink-0">
                    {ex.status === 'success' ? (
                      <CheckCircle2 className="h-3 w-3 text-green-500" />
                    ) : ex.status === 'failed' || ex.status === 'timeout' ? (
                      <XCircle className="h-3 w-3 text-red-500" />
                    ) : (
                      <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <pre className="text-[10px] font-mono truncate text-muted-foreground">
                      {ex.output || ex.error || '(no output)'}
                    </pre>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {ex.duration_ms !== null && (
                      <span className="text-[10px] text-muted-foreground flex items-center gap-0.5">
                        <Clock className="h-2.5 w-2.5" />
                        {ex.duration_ms}ms
                      </span>
                    )}
                    <span className="text-[10px] text-muted-foreground">
                      {new Date(ex.started_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  )
}
