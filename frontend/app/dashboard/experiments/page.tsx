'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Link from 'next/link'
import { FlaskConical, Plus, Loader2, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  fetchExperiments,
  createExperiment,
  type Experiment,
} from '@/lib/api/experiments'

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
      <div className="bg-white rounded-xl shadow-lg w-full max-w-md p-6 mx-4">
        <h2 className="text-lg font-semibold mb-4">Create Experiment</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="My Experiment"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              rows={3}
              placeholder="Optional description"
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
                'Create'
              )}
            </Button>
          </div>
        </div>
        {mutation.isError && (
          <p className="mt-3 text-sm text-red-600">
            Error: {(mutation.error as Error)?.message || 'Failed to create experiment'}
          </p>
        )}
      </div>
    </div>
  )
}

function ExperimentCard({ experiment }: { experiment: Experiment }) {
  const statusColors: Record<string, string> = {
    created: 'bg-yellow-100 text-yellow-800',
    running: 'bg-blue-100 text-blue-800',
    paused: 'bg-gray-100 text-gray-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    cancelled: 'bg-gray-100 text-gray-800',
  }

  const statusColor = statusColors[experiment.status] || 'bg-gray-100 text-gray-800'

  return (
    <Link href={`/dashboard/experiments/${experiment.id}`}>
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200 hover:shadow-md hover:border-blue-200 transition-all cursor-pointer">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-foreground truncate">{experiment.name}</h3>
            {experiment.description && (
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                {experiment.description}
              </p>
            )}
          </div>
          <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ml-3 ${statusColor}`}>
            {experiment.status}
          </span>
        </div>
        <div className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
          <span>Created {new Date(experiment.created_at).toLocaleDateString()}</span>
        </div>
      </div>
    </Link>
  )
}

export default function ExperimentsPage() {
  const [showCreate, setShowCreate] = useState(false)
  const queryClient = useQueryClient()

  const { data: experiments, isLoading, isError, error } = useQuery({
    queryKey: ['experiments'],
    queryFn: fetchExperiments,
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FlaskConical className="h-6 w-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-foreground">Experiments</h1>
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

      {/* Error state */}
      {isError && (
        <div className="rounded-xl bg-red-50 p-4 border border-red-200">
          <p className="text-sm text-red-600">
            Error loading experiments: {(error as Error)?.message || 'Unknown error'}
          </p>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !isError && experiments?.length === 0 && (
        <div className="rounded-xl bg-white p-12 shadow-sm border border-gray-200 text-center">
          <FlaskConical className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-foreground">No experiments yet</h3>
          <p className="text-muted-foreground mt-1">Create your first experiment to track runs and metrics.</p>
          <Button className="mt-4" onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1" />
            Create Experiment
          </Button>
        </div>
      )}

      {/* Experiments list */}
      {experiments && experiments.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {experiments.map((exp) => (
            <ExperimentCard key={exp.id} experiment={exp} />
          ))}
        </div>
      )}

      {/* Create dialog */}
      <CreateExperimentDialog open={showCreate} onOpenChange={setShowCreate} />
    </div>
  )
}
