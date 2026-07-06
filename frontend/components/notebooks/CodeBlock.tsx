'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Play,
  Loader2,
  CheckCircle2,
  XCircle,
  Terminal,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  executeBlock,
  type Block,
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
  const [execution, setExecution] = useState<ExecutionResult | null>(null)
  const content = block.content || ''

  const mutation = useMutation({
    mutationFn: () => executeBlock(notebookId, block.id),
    onSuccess: (data) => {
      setExecution(data)
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

  return (
    <div className="rounded-xl bg-card p-4 shadow-sm border border-border hover:shadow-md hover:border-primary/20 transition-all duration-200">
      {/* Code display with Run button */}
      <div className="relative">
        <pre className="text-xs text-muted-foreground bg-muted/50 rounded-lg p-3 overflow-x-auto font-mono leading-relaxed">
          {content || '(empty)'}
        </pre>
        <div className="absolute top-2 right-2">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending || !content.trim()}
            className="h-7 text-xs gap-1"
          >
            {mutation.isPending ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="h-3.5 w-3.5" />
            )}
            <span>Run</span>
          </Button>
        </div>
      </div>

      {/* Loading indicator */}
      {mutation.isPending && (
        <div className="mt-3 rounded-lg bg-black/5 dark:bg-white/5 p-3 border border-border">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin" />
            Running...
          </div>
        </div>
      )}

      {/* Output panel */}
      {execution && !mutation.isPending && (
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
    </div>
  )
}
