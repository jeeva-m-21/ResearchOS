import api from './client'
import { useProjectStore } from '@/lib/store/project'

export interface Citation {
  id: string
  citation_key: string
  cited_paper_id: string | null
  cited_doi: string | null
  title: string
  authors: string[]
  year: number
  venue: string | null
  url: string | null
  citation_text: string | null
  created_at: string
}

export interface Paper {
  id: string
  project_id: string
  title: string
  abstract: string | null
  status: string
  version: number
  authors: string[]
  doi: string | null
  arxiv_id: string | null
  tags: string[]
  latex_content: string | null
  created_at: string
  updated_at: string
  citations?: Citation[]
}

function getProjectId(): string {
  return useProjectStore.getState().currentProjectId ?? ''
}

export async function fetchPapers(projectId?: string, statusFilter?: string): Promise<Paper[]> {
  const params: Record<string, string | number> = {}
  if (projectId) params.project_id = projectId
  if (statusFilter) params.status_filter = statusFilter
  const res = await api.get('/v1/papers/', { params })
  return res.data
}

export async function fetchPaper(id: string): Promise<Paper> {
  const res = await api.get(`/v1/papers/${id}`)
  return res.data
}

export async function createPaper(
  title: string,
  abstract?: string,
  authors?: string,
  latex_content?: string,
): Promise<{ id: string; title: string; status: string }> {
  const params: Record<string, string> = { title, project_id: getProjectId() }
  if (abstract) params.abstract = abstract
  if (authors) params.authors = authors
  if (latex_content) params.latex_content = latex_content
  const res = await api.post('/v1/papers/', null, { params })
  return res.data
}

export async function updatePaper(
  id: string,
  data: {
    title?: string
    abstract?: string
    status?: string
    authors?: string
    doi?: string
    arxiv_id?: string
    tags?: string
    latex_content?: string
  },
): Promise<Paper> {
  const params: Record<string, string> = {}
  if (data.title !== undefined) params.title = data.title
  if (data.abstract !== undefined) params.abstract = data.abstract
  if (data.status !== undefined) params.status = data.status
  if (data.authors !== undefined) params.authors = data.authors
  if (data.doi !== undefined) params.doi = data.doi
  if (data.arxiv_id !== undefined) params.arxiv_id = data.arxiv_id
  if (data.tags !== undefined) params.tags = data.tags
  if (data.latex_content !== undefined) params.latex_content = data.latex_content
  const res = await api.patch(`/v1/papers/${id}`, null, { params })
  return res.data
}

export async function deletePaper(id: string): Promise<void> {
  await api.delete(`/v1/papers/${id}`)
}

export async function fetchCitations(paperId: string): Promise<Citation[]> {
  const res = await api.get(`/v1/papers/${paperId}/citations`)
  return res.data
}

export async function addCitation(
  paperId: string,
  citation_key: string,
  title: string,
  year: number,
  cited_doi?: string,
  authors?: string,
  venue?: string,
): Promise<{ id: string; citation_key: string; title: string; year: number }> {
  const params: Record<string, string | number> = { citation_key, title, year }
  if (cited_doi) params.cited_doi = cited_doi
  if (authors) params.authors = authors
  if (venue) params.venue = venue
  const res = await api.post(`/v1/papers/${paperId}/citations`, null, { params })
  return res.data
}

export async function deleteCitation(paperId: string, citationId: string): Promise<void> {
  await api.delete(`/v1/papers/${paperId}/citations/${citationId}`)
}

export async function fetchPapersCount(projectId?: string): Promise<number> {
  try {
    const data = await fetchPapers(projectId)
    return data.length
  } catch {
    return 0
  }
}
