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
