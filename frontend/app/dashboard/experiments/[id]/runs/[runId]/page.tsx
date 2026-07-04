'use client'

import { useParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Activity, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  fetchMetrics,
  type Metric,
} from '@/lib/api/experiments'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

function MetricsChart({ metrics }: { metrics: Metric[] }) {
  // Group by key
  const byKey: Record<string, Metric[]> = {}
  metrics.forEach((m) => {
    if (!byKey[m.key]) byKey[m.key] = []
    byKey[m.key].push(m)
  })

  const keys = Object.keys(byKey)
  if (keys.length === 0) return null

  // Build chart data indexed by step
  const stepMap: Record<number, Record<string, number>> = {}
  metrics.forEach((m) => {
    if (!stepMap[m.step]) stepMap[m.step] = {}
    stepMap[m.step][m.key] = m.value
    stepMap[m.step]['step'] = m.step
  })

  const chartData = Object.values(stepMap).sort((a, b) => (a.step || 0) - (b.step || 0))

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-200">
      <h3 className="text-sm font-semibold text-foreground mb-4">Metrics</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis
            dataKey="step"
            tick={{ fontSize: 12 }}
            className="text-muted-foreground"
            label={{ value: 'Step', position: 'insideBottomRight', offset: -5 }}
          />
          <YAxis tick={{ fontSize: 12 }} className="text-muted-foreground" />
          <Tooltip />
          <Legend />
          {keys.map((key, i) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              stroke={colors[i % colors.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
              activeDot={{ r: 5 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function MetricsTable({ metrics }: { metrics: Metric[] }) {
  if (metrics.length === 0) return null

  return (
    <div className="rounded-xl bg-white shadow-sm border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 bg-gray-50">
              <th className="text-left px-4 py-3 font-medium text-muted-foreground">Key</th>
              <th className="text-right px-4 py-3 font-medium text-muted-foreground">Value</th>
              <th className="text-right px-4 py-3 font-medium text-muted-foreground">Step</th>
              <th className="text-right px-4 py-3 font-medium text-muted-foreground">Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((m) => (
              <tr key={m.id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="px-4 py-3 font-medium">{m.key}</td>
                <td className="px-4 py-3 text-right font-mono">{m.value.toFixed(4)}</td>
                <td className="px-4 py-3 text-right">{m.step}</td>
                <td className="px-4 py-3 text-right text-muted-foreground">
                  {new Date(m.timestamp).toLocaleTimeString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function RunDetailPage() {
  const params = useParams()
  const router = useRouter()
  const experimentId = params.id as string
  const runId = params.runId as string

  const { data: metrics, isLoading, isError } = useQuery({
    queryKey: ['metrics', experimentId, runId],
    queryFn: () => fetchMetrics(experimentId, runId),
    enabled: !!experimentId && !!runId,
  })

  return (
    <div className="space-y-6">
      {/* Back */}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => router.push(`/dashboard/experiments/${experimentId}`)}
      >
        <ArrowLeft className="h-4 w-4 mr-1" /> Back to Experiment
      </Button>

      {/* Header */}
      <div className="flex items-center gap-2">
        <Activity className="h-6 w-6 text-blue-600" />
        <h1 className="text-2xl font-bold text-foreground">Run Details</h1>
        <span className="text-muted-foreground text-sm ml-2">ID: {runId.slice(0, 8)}...</span>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Error */}
      {isError && (
        <div className="rounded-xl bg-red-50 p-4 border border-red-200">
          <p className="text-sm text-red-600">Failed to load metrics.</p>
        </div>
      )}

      {/* Metrics chart and table */}
      {metrics && metrics.length > 0 && (
        <>
          <MetricsChart metrics={metrics} />
          <MetricsTable metrics={metrics} />
        </>
      )}

      {/* Empty */}
      {!isLoading && !isError && metrics?.length === 0 && (
        <div className="rounded-xl bg-white p-12 shadow-sm border border-gray-200 text-center">
          <Activity className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-foreground">No metrics logged</h3>
          <p className="text-muted-foreground mt-1">
            Log metrics to this run to see charts and data.
          </p>
        </div>
      )}
    </div>
  )
}
