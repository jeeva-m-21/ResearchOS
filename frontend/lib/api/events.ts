import api from './client'
import { useAuthStore } from '@/lib/store/auth'

export interface EventsHealth {
  status: 'healthy' | 'unhealthy' | 'degraded'
  components: Record<string, {
    status: string
    error?: string
  }>
  metrics?: {
    events_emitted: number
    events_processed: number
    consumer_errors: number
    active_consumers: number
  }
  organization_id: string
}

export interface ConsumerHealth {
  status: string
  consumer_group: string
  stream_key?: string
  active?: boolean
  pending_messages?: number
  consumer_lag_seconds?: number
  uptime_seconds?: number
  error?: string
  organization_id: string
}

export interface StreamStats {
  organization_id: string
  stream_info?: {
    length: number
    last_entry_id: string
    first_entry_id: string
  }
  consumer_groups?: Record<string, {
    pending_messages: number
    consumer_lag_seconds: number
    consumer_name: string
    error?: string
  }>
  metrics?: {
    events_emitted: number
    events_processed: number
    consumer_errors: number
    active_consumers: number
  }
  error?: string
}

export interface EventTypeInfo {
  type: string
  description: string
  aggregate: string
  version: number
}

export interface DqlRetryResult {
  status: string
  consumer_group: string
  limit: number
  attempted: number
  successful: number
  failed: number
  details: string[]
}

function getOrgId(): string {
  const { organizations } = useAuthStore.getState()
  return organizations[0]?.organization_id ?? ''
}

export async function fetchEventsHealth(): Promise<EventsHealth> {
  const res = await api.get('/v1/events/health', {
    params: { organization_id: getOrgId() },
  })
  return res.data
}

export async function fetchStreamStats(): Promise<StreamStats> {
  const res = await api.get('/v1/events/stats', {
    params: { organization_id: getOrgId() },
  })
  return res.data
}

export async function fetchConsumerHealth(consumerGroup: string): Promise<ConsumerHealth> {
  const res = await api.get(`/v1/events/consumers/${consumerGroup}/health`, {
    params: { organization_id: getOrgId() },
  })
  return res.data
}

export async function retryDlqEvents(consumerGroup: string, limit = 10): Promise<DqlRetryResult> {
  const res = await api.post(`/v1/events/dlq/${consumerGroup}/retry`, null, {
    params: { limit, organization_id: getOrgId() },
  })
  return res.data
}

export async function fetchEventTypes(): Promise<EventTypeInfo[]> {
  const res = await api.get('/v1/events/types')
  return res.data
}
