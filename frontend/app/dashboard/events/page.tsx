'use client'

import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  Clock,
  Database,
  Loader2,
  Radio,
  RefreshCw,
  Server,
  XCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { StatusBadge } from '@/components/ui/status-badge'
import {
  fetchEventsHealth,
  fetchStreamStats,
  fetchConsumerHealth,
  retryDlqEvents,
  fetchEventTypes,
  type EventsHealth,
  type StreamStats,
  type ConsumerHealth,
  type EventTypeInfo,
} from '@/lib/api/events'

const CONSUMER_GROUPS = ['projectors', 'notifiers', 'embedders', 'auditors']

function statusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'text-emerald-500'
    case 'degraded':
      return 'text-amber-500'
    case 'unhealthy':
    case 'failed':
      return 'text-red-500'
    default:
      return 'text-muted-foreground'
  }
}

function statusIcon(status: string) {
  switch (status) {
    case 'healthy':
      return <CheckCircle2 className="h-5 w-5 text-emerald-500" />
    case 'degraded':
      return <AlertCircle className="h-5 w-5 text-amber-500" />
    case 'unhealthy':
    case 'failed':
      return <XCircle className="h-5 w-5 text-red-500" />
    default:
      return <AlertCircle className="h-5 w-5 text-muted-foreground" />
  }
}

// ─── Health Card ──────────────────────────────────────────────────────

function SystemHealthCard({ health }: { health: EventsHealth | undefined }) {
  return (
    <div className="rounded-xl bg-card p-5 shadow-sm border border-border">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-muted-foreground">System Health</h3>
        {health ? (
          <Badge variant={health.status === 'healthy' ? 'default' : 'destructive'}>
            {health.status}
          </Badge>
        ) : (
          <Badge variant="outline">loading</Badge>
        )}
      </div>

      {health ? (
        <div className="space-y-2">
          {Object.entries(health.components || {}).map(([key, comp]) => (
            <div key={key} className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground capitalize">
                {key.replace(/_/g, ' ')}
              </span>
              <span className={statusColor(comp.status)}>
                {comp.status}
              </span>
            </div>
          ))}

          {health.metrics && (
            <div className="border-t pt-3 mt-3 space-y-1.5">
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Events Emitted</span>
                <span className="font-mono">{health.metrics.events_emitted}</span>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Events Processed</span>
                <span className="font-mono">{health.metrics.events_processed}</span>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Consumer Errors</span>
                <span className="font-mono">{health.metrics.consumer_errors}</span>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Active Consumers</span>
                <span className="font-mono">{health.metrics.active_consumers}</span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}
    </div>
  )
}

// ─── Stream Statistics Card ───────────────────────────────────────────

function StreamStatsCard({ stats }: { stats: StreamStats | undefined }) {
  return (
    <div className="rounded-xl bg-card p-5 shadow-sm border border-border">
      <div className="flex items-center gap-2 mb-4">
        <Radio className="h-4 w-4 text-muted-foreground" />
        <h3 className="text-sm font-medium text-muted-foreground">Stream Statistics</h3>
      </div>

      {stats ? (
        <div className="space-y-3">
          {stats.stream_info && (
            <>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Stream Length</span>
                <span className="font-mono">{stats.stream_info.length}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Last Entry ID</span>
                <span className="font-mono text-xs">{stats.stream_info.last_entry_id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">First Entry ID</span>
                <span className="font-mono text-xs">{stats.stream_info.first_entry_id}</span>
              </div>
            </>
          )}

          {stats.metrics && (
            <>
              <div className="border-t pt-3 mt-1" />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Emission Rate</span>
                <span className="font-mono">{stats.metrics.events_emitted} total</span>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Consumer Errors</span>
                <span className="font-mono">{stats.metrics.consumer_errors}</span>
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}
    </div>
  )
}

// ─── Consumer Group Card ──────────────────────────────────────────────

function ConsumerGroupCard({
  groupName,
  health,
  onRetry,
  retrying,
}: {
  groupName: string
  health: ConsumerHealth | undefined
  onRetry: () => void
  retrying: boolean
}) {
  return (
    <div className="rounded-xl bg-card p-5 shadow-sm border border-border">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {health ? statusIcon(health.status) : <Loader2 className="h-4 w-4 animate-spin" />}
          <h3 className="text-sm font-semibold capitalize">{groupName}</h3>
        </div>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 text-xs"
          onClick={onRetry}
          disabled={retrying}
        >
          <RefreshCw className={`h-3 w-3 mr-1 ${retrying ? 'animate-spin' : ''}`} />
          Retry DLQ
        </Button>
      </div>

      {health ? (
        <div className="space-y-1.5 text-sm">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Status</span>
            <Badge variant={health.status === 'healthy' ? 'outline' : 'secondary'} className="text-xs">
              {health.status}
            </Badge>
          </div>
          {health.pending_messages !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Pending</span>
              <span className="font-mono">{health.pending_messages}</span>
            </div>
          )}
          {health.consumer_lag_seconds !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Lag</span>
              <span className="font-mono">{health.consumer_lag_seconds.toFixed(1)}s</span>
            </div>
          )}
          {health.uptime_seconds !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Uptime</span>
              <span className="font-mono">{Math.round(health.uptime_seconds / 60)}m</span>
            </div>
          )}
          {health.error && (
            <div className="mt-2 p-2 rounded bg-red-500/10 text-red-600 text-xs">
              {health.error}
            </div>
          )}
        </div>
      ) : (
        <div className="flex items-center justify-center py-4">
          <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
        </div>
      )}
    </div>
  )
}

// ─── Event Types Table ────────────────────────────────────────────────

function EventTypesTable({ types }: { types: EventTypeInfo[] | undefined }) {
  return (
    <div className="rounded-xl bg-card shadow-sm border border-border overflow-hidden">
      <div className="px-5 py-4 border-b border-border">
        <h3 className="text-sm font-medium text-muted-foreground">Event Types</h3>
      </div>
      {types && types.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/30">
                <th className="text-left px-5 py-2.5 font-medium text-muted-foreground">Type</th>
                <th className="text-left px-5 py-2.5 font-medium text-muted-foreground">Description</th>
                <th className="text-left px-5 py-2.5 font-medium text-muted-foreground">Aggregate</th>
                <th className="text-right px-5 py-2.5 font-medium text-muted-foreground">Version</th>
              </tr>
            </thead>
            <tbody>
              {types.map((et) => (
                <tr key={et.type} className="border-b border-border last:border-0 hover:bg-muted/20">
                  <td className="px-5 py-2.5 font-mono text-xs">{et.type}</td>
                  <td className="px-5 py-2.5 text-muted-foreground">{et.description}</td>
                  <td className="px-5 py-2.5">
                    <StatusBadge status={et.aggregate.toLowerCase() as any} />
                  </td>
                  <td className="px-5 py-2.5 text-right font-mono">v{et.version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
          {types === undefined ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : null}
          {types === undefined ? 'Loading...' : 'No event types available'}
        </div>
      )}
    </div>
  )
}

// ─── Main Page ────────────────────────────────────────────────────────

export default function EventsDashboardPage() {
  const [retrying, setRetrying] = useState<Record<string, boolean>>({})

  const { data: health, refetch: refetchHealth } = useQuery({
    queryKey: ['events', 'health'],
    queryFn: fetchEventsHealth,
    refetchInterval: 15000,
  })

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['events', 'stats'],
    queryFn: fetchStreamStats,
    refetchInterval: 15000,
  })

  const { data: eventTypes } = useQuery({
    queryKey: ['events', 'types'],
    queryFn: fetchEventTypes,
  })

  // Fetch consumer health for each group in parallel
  const consumerQueries = CONSUMER_GROUPS.map((group) => ({
    queryKey: ['events', 'consumers', group],
    queryFn: () => fetchConsumerHealth(group),
    refetchInterval: 15000,
  }))

  const consumerHealthData = useQuery({
    queryKey: ['events', 'consumers', 'all'],
    queryFn: async () => {
      const results: Record<string, ConsumerHealth> = {}
      for (const group of CONSUMER_GROUPS) {
        try {
          results[group] = await fetchConsumerHealth(group)
        } catch {
          results[group] = { status: 'error', consumer_group: group, organization_id: '' }
        }
      }
      return results
    },
    refetchInterval: 15000,
  })

  const handleRetry = async (group: string) => {
    setRetrying((prev) => ({ ...prev, [group]: true }))
    try {
      await retryDlqEvents(group)
    } catch {
      // ignore error for now
    } finally {
      setRetrying((prev) => ({ ...prev, [group]: false }))
    }
  }

  const handleRefresh = () => {
    refetchHealth()
    refetchStats()
    consumerHealthData.refetch()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-6 w-6 text-foreground" />
          <h1 className="text-2xl font-bold text-foreground">Event System</h1>
        </div>
        <Button variant="outline" size="sm" onClick={handleRefresh}>
          <RefreshCw className="h-4 w-4 mr-1" />
          Refresh
        </Button>
      </div>

      <p className="text-muted-foreground">
        Monitor event streams, consumer groups, and dead letter queues across the event-driven architecture.
      </p>

      {/* Overview cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <SystemHealthCard health={health} />
        <StreamStatsCard stats={stats} />

        {/* Quick summary card */}
        <div className="rounded-xl bg-card p-5 shadow-sm border border-border">
          <div className="flex items-center gap-2 mb-4">
            <Database className="h-4 w-4 text-muted-foreground" />
            <h3 className="text-sm font-medium text-muted-foreground">Event Types</h3>
          </div>
          {eventTypes ? (
            <div className="space-y-2">
              <div className="text-3xl font-bold">{eventTypes.length}</div>
              <p className="text-xs text-muted-foreground">registered event types</p>
              <div className="flex flex-wrap gap-1.5 mt-3">
                {eventTypes.map((et) => (
                  <Badge key={et.type} variant="secondary" className="text-[10px]">
                    {et.type.split('.').pop()}
                  </Badge>
                ))}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          )}
        </div>
      </div>

      {/* Consumer groups */}
      <div>
        <h2 className="text-lg font-semibold mb-3">Consumer Groups</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {CONSUMER_GROUPS.map((group) => (
            <ConsumerGroupCard
              key={group}
              groupName={group}
              health={consumerHealthData.data?.[group]}
              onRetry={() => handleRetry(group)}
              retrying={retrying[group] ?? false}
            />
          ))}
        </div>
      </div>

      {/* Event types table */}
      <EventTypesTable types={eventTypes} />
    </div>
  )
}
