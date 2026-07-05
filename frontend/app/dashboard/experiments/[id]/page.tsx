'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import {
  ArrowLeft,
  FlaskConical,
  Play,
  Loader2,
  RefreshCw,
  Clock,
  BarChart3,
  Hash,
  Activity,
  CheckCircle2,
  XCircle,
  Pause,
  AlertCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  fetchExperiment,
  fetchRuns,
  fetchMetrics,
  startRun,
  type Experiment,
  type Run,
} from '@/lib/api/experiments'

// ---------- status config ----------

const STATUS_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
  created: { label: 'Created', icon: Clock, color: 'text-muted-foreground', bg: 'bg-muted' },
  running: { label: 'Running', icon: Play, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-100 dark:bg-blue-900/30' },
  paused: { label: 'Paused', icon: Pause, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-100 dark:bg-amber-900/30' },
  completed: { label: 'Completed', icon: CheckCircle2, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-100 dark:bg-emerald-900/30' },
  failed: { label: 'Failed', icon: XCircle, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-100 dark:bg-red-900/30' },
  cancelled: { label: 'Cancelled', icon: AlertCircle, color: 'text-muted-foreground', bg: 'bg-muted' },
}

function StatusBadge({ status, size = 'sm' }: { status: string; size?: 'sm' | 'md' }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.created
  const Icon = config.icon
  const sizeClasses = size === 'md' ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs'
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full font-medium ${sizeClasses} ${config.bg} ${config.color}`}>
      {status === 'running' ? (
        <span className="relative flex h-2 w-2">
          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
          <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
        </span>
      ) : (
        <Icon className="h-3.5 w-3.5" />
      )}
      {config.label}
    </span>
  )
}

// ---------- info card ----------

function InfoCard({ icon: Icon, label, value, sub }: { icon: React.ElementType; label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl bg-card p-4 shadow-sm border border-border">
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="text-sm font-medium text-foreground">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  )
}

// ---------- run row ----------

function RunRow({ experimentId, run }: { experimentId: string; run: Run }) {
  const config = STATUS_CONFIG[run.status] || STATUS_CONFIG.created
  const Icon = config.icon
  return (
    <Link href={`/dashboard/experiments/${experimentId}/runs/${run.id}`}>
      <div className="group flex items-center justify-between p-4 rounded-lg border border-border bg-card hover:bg-accent/50 transition-all cursor-pointer">
        <div className="flex items-center gap-4">
          <div className={`rounded-lg p-2 ${config.bg}`}>
            <Icon className={`h-4 w-4 ${config.color}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">Run #{run.run_number}</span>
              {run.status === 'running' && (
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500" />
                </span>
              )}
            </div>
            <span className="text-xs text-muted-foreground">
              {new Date(run.created_at).toLocaleString()}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          {run.duration_ms !== null && (
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {(run.duration_ms / 1000).toFixed(1)}s
            </span>
          )}
          <ArrowRightIcon />
        </div>
      </div>
    </Link>
  )
}

function ArrowRightIcon() {
  return (
    <svg className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
    </svg>
  )
}

// ---------- metric summary strip ----------

function MetricSummaryStrip({ experimentId }: { experimentId: string }) {
  const { data: runs } = useQuery({
    queryKey: ['runs', experimentId],
    queryFn: () => fetchRuns(experimentId),
    enabled: !!experimentId,
  })

  // Get latest completed run's metrics
  const latestRun = runs?.filter((r) => r.status === 'completed' || r.status === 'failed').slice(-1)[0]

  const { data: metrics } = useQuery({
    queryKey: ['metrics', experimentId, latestRun?.id],
    queryFn: () => fetchMetrics(experimentId, latestRun!.id),
    enabled: !!latestRun,
  })

  if (!metrics || metrics.length === 0) return null

  // Group by key and show latest value
  const latestByKey: Record<string, { value: number; step: number }> = {}
  metrics.forEach((m) => {
    if (!latestByKey[m.key] || m.step > latestByKey[m.key].step) {
      latestByKey[m.key] = { value: m.value, step: m.step }
    }
  })

  return (
    <div className="rounded-xl bg-card p-4 shadow-sm border border-border">
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
        <BarChart3 className="h-3.5 w-3.5" />
        Latest metrics
      </div>
      <div className="flex flex-wrap gap-4">
        {Object.entries(latestByKey).slice(0, 4).map(([key, { value, step }]) => (
          <div key={key} className="text-center min-w-[80px]">
            <p className="text-xs text-muted-foreground truncate">{key}</p>
            <p className="text-lg font-bold text-foreground">{typeof value === 'number' ? value.toFixed(4) : value}</p>
            <p className="text-xs text-muted-foreground">step {step}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ---------- page ----------

export default function ExperimentDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const experimentId = params.id as string
  const [startError, setStartError] = useState('')

  const { data: experiment, isLoading: loadingExp, isError: expError } = useQuery({
    queryKey: ['experiment', experimentId],
    queryFn: () => fetchExperiment(experimentId),
    enabled: !!experimentId,
  })

  const { data: runs, isLoading: loadingRuns } = useQuery({
    queryKey: ['runs', experimentId],
    queryFn: () => fetchRuns(experimentId),
    enabled: !!experimentId,
  })

  const startRunMutation = useMutation({
    mutationFn: () => startRun(experimentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['runs', experimentId] })
      queryClient.invalidateQueries({ queryKey: ['experiment', experimentId] })
      setStartError('')
    },
    onError: (err: Error) => {
      setStartError(err.message)
    },
  })

  const handleStartRun = () => {
    setStartError('')
    startRunMutation.mutate()
  }

  // Loading
  if (loadingExp) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-32 bg-muted rounded-lg animate-pulse" />
        <div className="h-8 w-64 bg-muted rounded-lg animate-pulse" />
        <div className="grid grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-muted rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  // Error
  if (expError || !experiment) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
        <div className="rounded-xl bg-destructive/10 p-4 border border-destructive/20">
          <p className="text-sm text-destructive">Experiment not found.</p>
        </div>
      </div>
    )
  }

  const config = STATUS_CONFIG[experiment.status] || STATUS_CONFIG.created
  const Icon = config.icon
  const runningCount = runs?.filter((r) => r.status === 'running').length || 0
  const lastRun = runs && runs.length > 0 ? runs[0] : null

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/experiments')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Experiments
        </Button>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className={`rounded-xl p-3 ${config.bg}`}>
            <Icon className={`h-6 w-6 ${config.color}`} />
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-foreground">{experiment.name}</h1>
              <StatusBadge status={experiment.status} size="md" />
            </div>
            {experiment.description && (
              <p className="text-sm text-muted-foreground mt-1">{experiment.description}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['runs', experimentId] })
              queryClient.invalidateQueries({ queryKey: ['experiment', experimentId] })
              queryClient.invalidateQueries({ queryKey: ['metrics', experimentId] })
            }}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <Button onClick={handleStartRun} disabled={startRunMutation.isPending}>
            {startRunMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-1" />
            )}
            Start Run
          </Button>
        </div>
      </div>

      {/* Error */}
      {startError && (
        <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive border border-destructive/20">
          {startError}
        </div>
      )}

      {/* Metric summary */}
      <MetricSummaryStrip experimentId={experimentId} />

      {/* Info cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <InfoCard icon={Clock} label="Created" value={new Date(experiment.created_at).toLocaleDateString()} sub={new Date(experiment.created_at).toLocaleTimeString()} />
        <InfoCard icon={Activity} label="Status" value={config.label} />
        <InfoCard icon={Hash} label="Total Runs" value={String(runs?.length || 0)} sub={runningCount > 0 ? `${runningCount} active` : undefined} />
        <InfoCard icon={BarChart3} label="Last Run" value={lastRun ? new Date(lastRun.created_at).toLocaleDateString() : '—'} sub={lastRun ? `#${lastRun.run_number}` : undefined} />
      </div>

      {/* Runs section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-foreground">Runs</h2>
          <Button size="sm" onClick={handleStartRun} disabled={startRunMutation.isPending}>
            {startRunMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Play className="h-4 w-4 mr-1" />
            )}
            Start Run
          </Button>
        </div>

        {loadingRuns ? (
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <div key={i} className="h-16 bg-muted rounded-lg animate-pulse" />
            ))}
          </div>
        ) : runs && runs.length > 0 ? (
          <div className="space-y-2">
            {runs.map((run) => (
              <RunRow key={run.id} experimentId={experimentId} run={run} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-card p-8 shadow-sm border border-border text-center">
            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-3">
              <Play className="h-6 w-6 text-primary" />
            </div>
            <p className="text-foreground font-medium">No runs yet</p>
            <p className="text-sm text-muted-foreground mt-1">
              Start your first run to begin tracking metrics and parameters.
            </p>
            <Button className="mt-4" onClick={handleStartRun} disabled={startRunMutation.isPending}>
              <Play className="h-4 w-4 mr-1" />
              Start Run
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
