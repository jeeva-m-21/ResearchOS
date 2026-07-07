import api from './client'

export interface ConnectionConfig {
  id: string
  organization_id: string
  name: string
  provider: string
  config: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface APIKeyInfo {
  id: string
  name: string
  created_at: string
  last_used_at: string | null
  expires_at: string | null
}

export async function fetchConnections(): Promise<ConnectionConfig[]> {
  const res = await api.get('/v1/settings/connections')
  return res.data
}

export async function createConnection(data: {
  name: string
  provider: string
  config: Record<string, unknown>
  is_active?: boolean
}): Promise<ConnectionConfig> {
  const res = await api.post('/v1/settings/connections', data)
  return res.data
}

export async function updateConnection(
  id: string,
  data: {
    name?: string
    config?: Record<string, unknown>
    is_active?: boolean
  },
): Promise<ConnectionConfig> {
  const res = await api.put(`/v1/settings/connections/${id}`, data)
  return res.data
}

export async function deleteConnection(id: string): Promise<void> {
  await api.delete(`/v1/settings/connections/${id}`)
}

export async function fetchAPIKeys(): Promise<APIKeyInfo[]> {
  const res = await api.get('/v1/settings/api-keys')
  return res.data
}

export async function deleteAPIKey(id: string): Promise<void> {
  await api.delete(`/v1/settings/api-keys/${id}`)
}
