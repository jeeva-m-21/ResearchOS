import api from './client'
import { useAuthStore } from '../store/auth'

export interface SearchResult {
  id: string
  node_type: string
  title: string
  description: string | null
  score: number
  highlights?: string[]
}

export interface SuggestionResult {
  id: string
  title: string
  node_type: string
  similarity: number
}

export interface SearchResponse {
  results: SearchResult[]
  total: number
  took_ms: number
  query: string
}

export interface SearchParams {
  q: string
  types?: string[]
  limit?: number
  offset?: number
}

function getOrgId(): string {
  const { organizations } = useAuthStore.getState()
  return organizations[0]?.organization_id || ''
}

export async function searchResults(params: SearchParams): Promise<SearchResponse> {
  const orgId = getOrgId()
  const reqParams: Record<string, string | number> = {
    q: params.q,
    organization_id: orgId,
    limit: params.limit ?? 10,
    offset: params.offset ?? 0,
  }

  if (params.types && params.types.length > 0) {
    // FastAPI accepts repeated query params for list types
    reqParams.types = params.types.join(',')
  }

  const res = await api.get('/v1/search/', { params: reqParams })
  return res.data
}

export async function fetchSuggestions(q: string, limit: number = 5): Promise<SuggestionResult[]> {
  if (!q.trim()) return []

  const orgId = getOrgId()
  const res = await api.get('/v1/search/suggestions', {
    params: { q, organization_id: orgId, limit },
  })
  return res.data
}

export const NODE_TYPES = [
  { value: 'idea', label: 'Ideas' },
  { value: 'hypothesis', label: 'Hypotheses' },
  { value: 'experiment', label: 'Experiments' },
  { value: 'paper', label: 'Papers' },
  { value: 'dataset', label: 'Datasets' },
  { value: 'model', label: 'Models' },
  { value: 'notebook', label: 'Notebooks' },
  { value: 'insight', label: 'Insights' },
  { value: 'person', label: 'People' },
] as const
