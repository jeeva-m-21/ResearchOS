import api from './client'
import { useProjectStore } from '@/lib/store/project'

export interface Notebook {
  id: string
  title: string
  description: string | null
  project_id: string
  branch: string
  created_at: string
  updated_at: string
}

function getProjectId(): string {
  return useProjectStore.getState().currentProjectId ?? ''
}

export async function fetchNotebooks(projectId?: string): Promise<Notebook[]> {
  const params: Record<string, string | number> = {}
  if (projectId) params.project_id = projectId
  const res = await api.get('/v1/notebooks/', { params })
  return res.data
}

export async function fetchNotebook(id: string): Promise<Notebook> {
  const res = await api.get(`/v1/notebooks/${id}`)
  return res.data
}

export async function createNotebook(title: string, description?: string): Promise<{ id: string; title: string; project_id: string }> {
  const params: Record<string, string> = { title, project_id: getProjectId() }
  if (description) params.description = description
  const res = await api.post('/v1/notebooks/', null, { params })
  return res.data
}

export async function fetchNotebooksCount(projectId?: string): Promise<number> {
  try {
    const data = await fetchNotebooks(projectId)
    return data.length
  } catch {
    return 0
  }
}

// ── Block types & API ─────────────────────────────────────────────────

export interface Block {
  id: string
  notebook_id: string
  block_type: string
  position: number
  current_version: number
  created_at: string
  updated_at: string
  content: string | null
  language: string | null
  content_version: number | null
}

export async function fetchBlocks(notebookId: string): Promise<Block[]> {
  const res = await api.get(`/v1/notebooks/${notebookId}/blocks`)
  return res.data
}

export async function fetchBlock(notebookId: string, blockId: string): Promise<Block> {
  const res = await api.get(`/v1/notebooks/${notebookId}/blocks/${blockId}`)
  return res.data
}

export async function createBlock(
  notebookId: string,
  data: {
    block_type: string
    content: string
    language?: string | null
    position?: number | null
  }
): Promise<Block> {
  const res = await api.post(`/v1/notebooks/${notebookId}/blocks`, data)
  return res.data
}

// ── Block Update ───────────────────────────────────────────────────

export interface UpdateBlockData {
  content?: string | null
  language?: string | null
  position?: number | null
}

export async function updateBlock(
  notebookId: string,
  blockId: string,
  data: UpdateBlockData,
): Promise<Block> {
  const res = await api.put(`/v1/notebooks/${notebookId}/blocks/${blockId}`, data)
  return res.data
}

// ── Block Execution ─────────────────────────────────────────────────

export interface Execution {
  id: string
  block_content_id: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'timeout'
  started_at: string
  ended_at: string | null
  duration_ms: number | null
  output: string | null
  error: string | null
}

export async function executeBlock(
  notebookId: string,
  blockId: string,
): Promise<{
  execution_id: string
  status: string
  output: string | null
  error: string | null
  duration_ms: number | null
}> {
  const res = await api.post(`/v1/notebooks/${notebookId}/blocks/${blockId}/execute`)
  return res.data
}

export async function fetchExecutions(
  notebookId: string,
  blockId: string,
  params?: { limit?: number; offset?: number },
): Promise<Execution[]> {
  const res = await api.get(`/v1/notebooks/${notebookId}/blocks/${blockId}/executions`, {
    params: { limit: params?.limit ?? 10, offset: params?.offset ?? 0 },
  })
  return res.data
}
