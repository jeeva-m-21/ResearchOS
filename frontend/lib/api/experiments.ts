import api from './client'
import { useProjectStore } from '@/lib/store/project'

export interface Experiment {
  id: string
  name: string
  description: string | null
  project_id: string
  status: string
  created_at: string
  updated_at: string
}

export interface Run {
  id: string
  run_number: number
  status: string
  started_at: string | null
  ended_at: string | null
  duration_ms: number | null
  git_commit: string | null
  created_at: string
}

export interface Metric {
  id: string
  run_id: string
  key: string
  value: number
  step: number
  timestamp: string
  metadata?: Record<string, unknown>
}

function getProjectId(): string {
  return useProjectStore.getState().currentProjectId ?? ''
}

export async function fetchExperiments(): Promise<Experiment[]> {
  const res = await api.get('/v1/experiments/')
  return res.data
}

export async function fetchExperiment(id: string): Promise<Experiment> {
  const res = await api.get(`/v1/experiments/${id}`)
  return res.data
}

export async function createExperiment(name: string, description?: string): Promise<{ id: string; name: string }> {
  const params: Record<string, string> = { name, project_id: getProjectId() }
  if (description) params.description = description
  const res = await api.post('/v1/experiments/', null, { params })
  return res.data
}

export async function fetchRuns(experimentId: string): Promise<Run[]> {
  const res = await api.get(`/v1/experiments/${experimentId}/runs`)
  return res.data
}

export async function startRun(experimentId: string): Promise<{ run_id: string; run_number: number }> {
  const res = await api.post(`/v1/experiments/${experimentId}/runs`)
  return res.data
}

export async function fetchMetrics(experimentId: string, runId: string, key?: string): Promise<Metric[]> {
  const params: Record<string, string | number> = {}
  if (key) params.key = key
  const res = await api.get(`/v1/experiments/${experimentId}/runs/${runId}/metrics`, { params })
  return res.data
}

export async function logMetric(
  experimentId: string,
  runId: string,
  key: string,
  value: number,
  step: number = 0,
): Promise<{ id: string; key: string; value: number; step: number }> {
  const res = await api.post(`/v1/experiments/${experimentId}/runs/${runId}/metrics`, null, {
    params: { key, value, step },
  })
  return res.data
}

export async function completeRun(
  experimentId: string,
  runId: string,
  runStatus: string = 'completed',
  error?: string,
): Promise<{ run_id: string; status: string }> {
  const params: Record<string, string> = { run_status: runStatus }
  if (error) params.error = error
  const res = await api.post(`/v1/experiments/${experimentId}/runs/${runId}/complete`, null, { params })
  return res.data
}

export async function fetchExperimentsCount(): Promise<number> {
  try {
    const data = await fetchExperiments()
    return data.length
  } catch {
    return 0
  }
}
