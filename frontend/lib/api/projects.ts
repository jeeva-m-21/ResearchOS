import api from './client'

export interface Project {
  id: string
  name: string
  description: string | null
  visibility: string
  created_at: string
  updated_at: string
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await api.get('/v1/projects/')
  return res.data
}

export async function fetchProject(id: string): Promise<Project> {
  const res = await api.get(`/v1/projects/${id}`)
  return res.data
}
