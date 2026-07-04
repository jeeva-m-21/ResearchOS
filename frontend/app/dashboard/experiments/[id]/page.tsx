'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { ArrowLeft, FlaskConical, Play, Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  fetchExperiment,
  fetchRuns,
  startRun,
  type Experiment,
  type Run,
} from '@/lib/api/experiments'

const statusColors: Record<string, string> = {
  created: 'bg-yellow-100 text-yellow-800',
  running: 'bg-blue-100 text-blue-800',
  paused: 'bg-gray-100 text-gray-800',
  completed: 'bg-green-100 text-green-800',
  failed: 'bg-red-100 text-red-800',
  cancelled: 'bg-gray-100 text-gray-800',
}

function RunRow({ experimentId, run }: { experimentId: string; run: Run }) {
  return (
    <Link href={`/dashboard/experiments/${experimentId}/runs/${run.id}`}>
      <div className="flex items-center justify-between p-4 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors cursor-pointer">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-muted-foreground">#{run.run_number}</span>
          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[run.status] || 'bg-gray-100 text-gray-800'}`}>
            {run.status}
          </span>
          <span className="text-sm text-muted-foreground">
            {new Date(run.created_at).toLocaleString()}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {run.duration_ms !== null && (
            <span>{(run.duration_ms / 1000).toFixed(1)}s</span>
          )}
          <span className="text-blue-600 hover:text-blue-800 text-sm font-medium">
            View →
          </span>
        </div>
      </div>
    </Link>
  )
}

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

  if (loadingExp) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (expError || !experiment) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
        <div className="rounded-xl bg-red-50 p-4 border border-red-200">
          <p className="text-sm text-red-600">Experiment not found.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back + header */}
      <div className="space-y-2">
        <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/experiments')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Experiments
        </Button>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FlaskConical className="h-6 w-6 text-blue-600" />
            <div>
              <h1 className="text-2xl font-bold text-foreground">{experiment.name}</h1>
              {experiment.description && (
                <p className="text-sm text-muted-foreground mt-1">{experiment.description}</p>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ${statusColors[experiment.status] || 'bg-gray-100 text-gray-800'}`}>
              {experiment.status}
            </span>
            <Button onClick={handleStartRun} disabled={startRunMutation.isPending}>
              {startRunMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Play className="h-4 w-4 mr-1" />
              )}
              Start Run
            </Button>
            <Button
              variant="outline"
              size="icon"
              onClick={() => {
                queryClient.invalidateQueries({ queryKey: ['runs', experimentId] })
                queryClient.invalidateQueries({ queryKey: ['experiment', experimentId] })
              }}
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {startError && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-600 border border-red-200">
          {startError}
        </div>
      )}

      {/* Experiment info */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
          <p className="text-xs text-muted-foreground">Created</p>
          <p className="text-sm font-medium mt-1">{new Date(experiment.created_at).toLocaleDateString()}</p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
          <p className="text-xs text-muted-foreground">Runs</p>
          <p className="text-sm font-medium mt-1">{runs?.length || 0}</p>
        </div>
        <div className="rounded-xl bg-white p-4 shadow-sm border border-gray-200">
          <p className="text-xs text-muted-foreground">Status</p>
          <p className="text-sm font-medium mt-1 capitalize">{experiment.status}</p>
        </div>
      </div>

      {/* Runs list */}
      <div>
        <h2 className="text-lg font-semibold text-foreground mb-3">Runs</h2>
        {loadingRuns ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : runs && runs.length > 0 ? (
          <div className="space-y-2">
            {runs.map((run) => (
              <RunRow key={run.id} experimentId={experimentId} run={run} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-white p-8 shadow-sm border border-gray-200 text-center">
            <Play className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
            <p className="text-muted-foreground">No runs yet. Click &quot;Start Run&quot; to begin.</p>
          </div>
        )}
      </div>
    </div>
  )
}
