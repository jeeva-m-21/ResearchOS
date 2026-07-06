import api from './client'
import { useAuthStore } from '@/lib/store/auth'

export interface ModelInfo {
  id: string
  name: string
  provider: string
  description: string
  available: boolean
}

export interface AskRequest {
  message: string
  model?: string
  session_id?: string
  project_id?: string
  stream?: boolean
}

// SSE event types from the backend
export interface TokenEvent {
  type: 'token'
  content: string
}

export interface ToolCallEvent {
  type: 'tool_call'
  content: {
    id: string
    name: string
    arguments: Record<string, unknown>
  }
}

export interface ToolResultEvent {
  type: 'tool_result'
  content: {
    name: string
    result: string
  }
}

export interface DoneEvent {
  type: 'done'
  content: {
    session_id: string
  }
}

export type StreamEvent = TokenEvent | ToolCallEvent | ToolResultEvent | DoneEvent

export async function fetchModels(): Promise<ModelInfo[]> {
  const res = await api.get('/v1/ask/models')
  return res.data
}

export async function* askStream(request: AskRequest): AsyncGenerator<StreamEvent> {
  const { organizations } = useAuthStore.getState()
  const orgId = organizations[0]?.organization_id

  const params = new URLSearchParams()
  if (orgId) params.set('organization_id', orgId)

  const response = await fetch(
    `${api.defaults.baseURL}/v1/ask${params.toString() ? '?' + params.toString() : ''}`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${useAuthStore.getState().accessToken}`,
      },
      body: JSON.stringify(request),
    },
  )

  if (!response.ok) {
    throw new Error(`Ask request failed: ${response.status} ${response.statusText}`)
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      try {
        const data = JSON.parse(line.slice(6))
        yield data as StreamEvent
      } catch {
        // skip malformed JSON
      }
    }
  }
}

export async function ask(request: AskRequest): Promise<string> {
  const chunks: string[] = []
  for await (const event of askStream({ ...request, stream: true })) {
    if (event.type === 'token') {
      chunks.push(event.content)
    }
  }
  return chunks.join('')
}
