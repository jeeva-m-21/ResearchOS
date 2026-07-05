import api from './client'

export interface Notebook {
  id: string
  title: string
  description: string | null
  project_id: string
  branch: string
  created_at: string
  updated_at: string
}

const TEST_PROJECT_ID = '90c7cb47-cc1f-472f-99c5-2b17a9e088a8'

export async function fetchNotebooks(): Promise<Notebook[]> {
  const res = await api.get('/v1/notebooks/')
  return res.data
}

export async function fetchNotebook(id: string): Promise<Notebook> {
  const res = await api.get(`/v1/notebooks/${id}`)
  return res.data
}

export async function createNotebook(title: string, description?: string): Promise<{ id: string; title: string; project_id: string }> {
  const params: Record<string, string> = { title, project_id: TEST_PROJECT_ID }
  if (description) params.description = description
  const res = await api.post('/v1/notebooks/', null, { params })
  return res.data
}

export async function fetchNotebooksCount(): Promise<number> {
  try {
    const data = await fetchNotebooks()
    return data.length
  } catch {
    return 0
  }
}
