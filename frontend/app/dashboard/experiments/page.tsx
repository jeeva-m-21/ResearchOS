'use client'

import { useState, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import {
  FlaskConical,
  Plus,
  Loader2,
  RefreshCw,
  Search as SearchIcon,
  Play,
  CheckCircle2,
  XCircle,
  Pause,
  Clock,
  AlertCircle,
  ArrowRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { useProjectStore } from '@/lib/store/project'
import {
  fetchExperiments,
  createExperiment,
  type Experiment,
} from '@/lib/api/experiments'

// ---------- status helpers ----------

const STATUS_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string; bg: string; animate: boolean }> = {
  created: {
    label: 'Created',
    icon: Clock,
    color: 'text-muted-foreground',
    bg: 'bg-muted',
    animate: false,
  },
  running: {
    label: 'Running',
    icon: Play,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    animate: true,
  },
  paused: {
    label: 'Paused',
    icon: Pause,
    color: 'text-amber-600 dark:text-amber-400',
    bg: 'bg-amber-100 dark:bg-amber-900/30',
    animate: false,
  },
  completed: {
    label: 'Completed',
    icon: CheckCircle2,
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'bg-emerald-100 dark:bg-emerald-900/30',
    animate: false,
  },
  failed: {
    label: 'Failed',
    icon: XCircle,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
    animate: false,
  },
  cancelled: {
    label: 'Cancelled',
    icon: AlertCircle,
    color: 'text-muted-foreground',
    bg: 'bg-muted',
    animate: false,
  },
}

function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.created
  const Icon = config.icon
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${config.bg} ${config.color}`}>
      {config.animate ? (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
        </span>
      ) : (
        <Icon className="h-3 w-3" />
      )}
      {config.label}
    </span>
  )
}

// ---------- filter bar ----------

const STATUS_TABS = [
  { value: 'all', label: 'All' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'created', label: 'Draft' },
]

function FilterBar({
  activeStatus,
  onStatusChange,
  searchQuery,
  onSearchChange,
}: {
  activeStatus: string
  onStatusChange: (s: string) => void
  searchQuery: string
  onSearchChange: (s: string) => void
}) {
  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
      <div className="flex items-center gap-1 bg-card rounded-lg border border-border p-0.5">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => onStatusChange(tab.value)}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              activeStatus === tab.value
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <div className="relative flex-1 max-w-xs w-full">
        <SearchIcon className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search experiments..."
          className="w-full rounded-lg border border-border bg-card py-1.5 pl-8 pr-3 text-xs focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>
    </div>
  )
}

// ---------- create dialog ----------

function CreateExperimentDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => createExperiment(name, description || undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
      setName('')
      setDescription('')
      onOpenChange(false)
    },
  })

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-card rounded-xl shadow-lg border border-border w-full max-w-md p-6 mx-4">
        <h2 className="text-lg font-semibold mb-4">New Experiment</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Experiment name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="e.g., BERT fine-tuning on PubMed"
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
              placeholder="What hypothesis are you testing?"
            />
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => mutation.mutate()}
              disabled={!name.trim() || mutation.isPending}
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <FlaskConical className="mr-1.5 h-4 w-4" />
                  Start Experiment
                </>
              )}
            </Button>
          </div>
        </div>
        {mutation.isError && (
          <p className="mt-3 text-sm text-destructive">
            Error: {(mutation.error as Error)?.message || 'Failed to create experiment'}
          </p>
        )}
      </div>
    </div>
  )
}

// ---------- experiment card ----------

function ExperimentCard({ experiment }: { experiment: Experiment }) {
  return (
    <Link href={`/dashboard/experiments/${experiment.id}`} className="h-full">
      <div className="group flex flex-col h-full rounded-xl bg-card p-5 shadow-sm border border-border hover:shadow-md hover:border-primary/20 transition-all duration-200 cursor-pointer relative overflow-hidden">
        {/* Top gradient line on hover */}
        <div className="absolute inset-x-0 -top-px h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        <div className="flex items-start justify-between flex-1">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <FlaskConical className="h-4 w-4 text-muted-foreground shrink-0" />
              <h3 className="font-semibold text-foreground truncate">{experiment.name}</h3>
            </div>
            {experiment.description && (
              <p className="text-sm text-muted-foreground mt-1.5 line-clamp-2 ml-6">
                {experiment.description}
              </p>
            )}
          </div>
          <StatusBadge status={experiment.status} />
        </div>

        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground shrink-0 ml-6">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {new Date(experiment.created_at).toLocaleDateString()}
          </span>
          <span className="flex items-center gap-1 text-foreground/50 group-hover:text-foreground transition-colors">
            View details <ArrowRight className="h-3 w-3" />
          </span>
        </div>
      </div>
    </Link>
  )
}

// ---------- page ----------

export default function ExperimentsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const [activeStatus, setActiveStatus] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const queryClient = useQueryClient()

  const currentProjectId = useProjectStore((s) => s.currentProjectId)

  const { data: experiments, isLoading, isError, error } = useQuery({
    queryKey: ['experiments', currentProjectId ?? ''],
    queryFn: () => fetchExperiments(currentProjectId ?? undefined),
  })

  const filteredExperiments = useMemo(() => {
    if (!experiments) return []
    let result = experiments

    if (activeStatus !== 'all') {
      result = result.filter((e) => e.status === activeStatus)
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      result = result.filter(
        (e) =>
          e.name.toLowerCase().includes(q) ||
          (e.description && e.description.toLowerCase().includes(q))
      )
    }

    return result
  }, [experiments, activeStatus, searchQuery])

  const runningCount = experiments?.filter((e) => e.status === 'running').length || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="rounded-xl bg-primary/10 p-2.5">
            <FlaskConical className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-foreground">Experiments</h1>
            <p className="text-sm text-muted-foreground">
              {experiments?.length || 0} total
              {runningCount > 0 && ` · ${runningCount} running`}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['experiments'] })}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <Button onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1" />
            New Experiment
          </Button>
        </div>
      </div>

      {/* Filter bar */}
      <FilterBar
        activeStatus={activeStatus}
        onStatusChange={setActiveStatus}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
      />

      {/* Error state */}
      {isError && (
        <div className="rounded-xl bg-destructive/10 p-4 border border-destructive/20">
          <p className="text-sm text-destructive">
            Error loading experiments: {(error as Error)?.message || 'Unknown error'}
          </p>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="rounded-xl bg-card p-5 shadow-sm border border-border animate-pulse">
              <div className="flex items-start justify-between">
                <div className="space-y-2 flex-1">
                  <div className="h-5 w-48 bg-muted rounded" />
                  <div className="h-4 w-72 bg-muted rounded" />
                </div>
                <div className="h-6 w-20 bg-muted rounded-full" />
              </div>
              <div className="mt-4 h-4 w-32 bg-muted rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state — all */}
      {!isLoading && !isError && experiments?.length === 0 && (
        <div className="rounded-xl bg-card p-12 shadow-sm border border-border text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4">
            <FlaskConical className="h-8 w-8 text-primary" />
          </div>
          <h3 className="text-lg font-medium text-foreground">Your first experiment awaits</h3>
          <p className="text-muted-foreground mt-1 max-w-sm mx-auto">
            Track ML experiments, log metrics, compare runs — all in one place.
          </p>
          <div className="flex items-center justify-center gap-3 mt-6">
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-1" />
              Create Experiment
            </Button>
            <Button variant="outline" onClick={() => queryClient.invalidateQueries({ queryKey: ['experiments'] })}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
          </div>
        </div>
      )}

      {/* Empty state — filtered */}
      {!isLoading && !isError && experiments && experiments.length > 0 && filteredExperiments.length === 0 && (
        <div className="rounded-xl bg-card p-8 shadow-sm border border-border text-center">
          <SearchIcon className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
          <p className="text-muted-foreground">No experiments match your filters.</p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2"
            onClick={() => {
              setActiveStatus('all')
              setSearchQuery('')
            }}
          >
            Clear filters
          </Button>
        </div>
      )}

      {/* Experiments grid */}
      {filteredExperiments.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredExperiments.map((exp) => (
            <ExperimentCard key={exp.id} experiment={exp} />
          ))}
        </div>
      )}

      {/* Create dialog */}
      <CreateExperimentDialog open={showCreate} onOpenChange={setShowCreate} />
    </div>
  )
}
