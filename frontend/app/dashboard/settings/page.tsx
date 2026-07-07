'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  fetchConnections,
  createConnection,
  updateConnection,
  deleteConnection,
  fetchAPIKeys,
  deleteAPIKey,
  type ConnectionConfig,
  type APIKeyInfo,
} from '@/lib/api/settings'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Key,
  Plus,
  Trash2,
  Plug,
  Bot,
  Database,
  Globe,
  Server,
  ChevronRight,
  Check,
  X,
  AlertCircle,
  ExternalLink,
} from 'lucide-react'

// ─── Section tabs ─────────────────────────────────────────────────────────

const sectionTabs = [
  { id: 'api-keys', label: 'API Keys', icon: Key },
  { id: 'connections', label: 'Connections', icon: Plug },
  { id: 'providers', label: 'AI Providers', icon: Bot },
  { id: 'general', label: 'General', icon: Server },
]

type SectionId = (typeof sectionTabs)[number]['id']

// ─── API Keys Section ──────────────────────────────────────────────────────

function APIKeysSection() {
  const queryClient = useQueryClient()
  const [createOpen, setCreateOpen] = useState(false)
  const [newKeyName, setNewKeyName] = useState('')

  const { data: keys, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: fetchAPIKeys,
  })

  const deleteMutation = useMutation({
    mutationFn: deleteAPIKey,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['api-keys'] }),
  })

  const handleCreate = useCallback(async () => {
    if (!newKeyName.trim()) return
    try {
      const res = await import('@/lib/api/ask').then((m) =>
        m.fetchModels(),
      )
      // Use the existing auth API key creation endpoint
      const api = (await import('@/lib/api/client')).default
      await api.post('/auth/api-keys', { name: newKeyName.trim() })
      setNewKeyName('')
      setCreateOpen(false)
      queryClient.invalidateQueries({ queryKey: ['api-keys'] })
    } catch {
      // Silently fail
    }
  }, [newKeyName, queryClient])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">API Keys</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Manage API keys for programmatic access to ResearchOS.
          </p>
        </div>
        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-1.5">
              <Plus className="h-4 w-4" />
              Create key
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create API Key</DialogTitle>
              <DialogDescription>
                Give your key a name to identify what it is used for.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Key name</label>
                <Input
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="e.g. CI/CD pipeline"
                  onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setCreateOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleCreate} disabled={!newKeyName.trim()}>
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Separator />

      {isLoading ? (
        <div className="text-sm text-muted-foreground py-8 text-center">
          Loading...
        </div>
      ) : !keys?.length ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Key className="h-10 w-10 text-muted-foreground/30 mb-3" />
          <p className="text-sm text-muted-foreground">No API keys yet</p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Create a key to access ResearchOS programmatically.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {keys.map((key) => (
            <div
              key={key.id}
              className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <Key className="h-4 w-4 text-muted-foreground shrink-0" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">
                    {key.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Created {new Date(key.created_at).toLocaleDateString()}
                    {key.last_used_at
                      ? ` · Last used ${new Date(key.last_used_at).toLocaleDateString()}`
                      : ' · Never used'}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {key.expires_at && (
                  <Badge variant="outline" className="text-[10px]">
                    Expires {new Date(key.expires_at).toLocaleDateString()}
                  </Badge>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-muted-foreground hover:text-destructive"
                  onClick={() => deleteMutation.mutate(key.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

// ─── Connections Section ────────────────────────────────────────────────────

const providerOptions = [
  { value: 'jupyter', label: 'Jupyter Server', icon: Globe },
  { value: 'postgresql', label: 'PostgreSQL', icon: Database },
  { value: 'redis', label: 'Redis', icon: Database },
  { value: 'custom', label: 'Custom', icon: Server },
]

function ConnectionsSection() {
  const queryClient = useQueryClient()
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<ConnectionConfig | null>(null)
  const [formName, setFormName] = useState('')
  const [formProvider, setFormProvider] = useState('jupyter')
  const [formUrl, setFormUrl] = useState('')
  const [formToken, setFormToken] = useState('')

  const { data: connections, isLoading } = useQuery({
    queryKey: ['connections'],
    queryFn: fetchConnections,
  })

  const createMutation = useMutation({
    mutationFn: createConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] })
      resetForm()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      updateConnection(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['connections'] })
      resetForm()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteConnection,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['connections'] }),
  })

  const resetForm = () => {
    setFormName('')
    setFormProvider('jupyter')
    setFormUrl('')
    setFormToken('')
    setEditing(null)
    setDialogOpen(false)
  }

  const openEdit = (conn: ConnectionConfig) => {
    setEditing(conn)
    setFormName(conn.name)
    setFormProvider(conn.provider)
    setFormUrl((conn.config?.url as string) || '')
    setFormToken((conn.config?.token as string) || '')
    setDialogOpen(true)
  }

  const handleSave = () => {
    if (!formName.trim()) return
    const config: Record<string, unknown> = { url: formUrl }
    if (formToken) config.token = formToken

    if (editing) {
      updateMutation.mutate({ id: editing.id, data: { name: formName, config } })
    } else {
      createMutation.mutate({
        name: formName,
        provider: formProvider,
        config,
      })
    }
  }

  const ProviderIcon = providerOptions.find((p) => p.value === formProvider)?.icon || Server

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Connections</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Configure connections to external services and databases.
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm" className="gap-1.5" onClick={() => { setEditing(null); resetForm(); setDialogOpen(true) }}>
              <Plus className="h-4 w-4" />
              Add connection
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>{editing ? 'Edit Connection' : 'Add Connection'}</DialogTitle>
              <DialogDescription>
                Configure a connection to an external service.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. My Jupyter Server"
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Type</label>
                <Select value={formProvider} onValueChange={setFormProvider}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {providerOptions.map((p) => (
                      <SelectItem key={p.value} value={p.value}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">URL / Host</label>
                <Input
                  value={formUrl}
                  onChange={(e) => setFormUrl(e.target.value)}
                  placeholder={
                    formProvider === 'jupyter'
                      ? 'http://localhost:8888'
                      : 'Hostname or connection string'
                  }
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Token / Password</label>
                <Input
                  type="password"
                  value={formToken}
                  onChange={(e) => setFormToken(e.target.value)}
                  placeholder="Optional authentication token"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={resetForm}>
                Cancel
              </Button>
              <Button onClick={handleSave} disabled={!formName.trim()}>
                {editing ? 'Save' : 'Add'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Separator />

      {isLoading ? (
        <div className="text-sm text-muted-foreground py-8 text-center">
          Loading...
        </div>
      ) : !connections?.length ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Plug className="h-10 w-10 text-muted-foreground/30 mb-3" />
          <p className="text-sm text-muted-foreground">No connections configured</p>
          <p className="text-xs text-muted-foreground/60 mt-1">
            Add a connection to link external services.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {connections.map((conn) => {
            const ConnIcon =
              providerOptions.find((p) => p.value === conn.provider)?.icon || Server
            return (
              <div
                key={conn.id}
                className="flex items-center justify-between rounded-lg border border-border bg-card px-4 py-3"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div
                    className={cn(
                      'rounded-lg p-2',
                      conn.is_active
                        ? 'bg-emerald-500/10 text-emerald-500'
                        : 'bg-muted text-muted-foreground',
                    )}
                  >
                    <ConnIcon className="h-4 w-4" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-foreground truncate">
                        {conn.name}
                      </p>
                      {conn.is_active && (
                        <Badge variant="default" className="h-5 text-[10px] bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/20">
                          <Check className="h-2.5 w-2.5 mr-1" />
                          Active
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground capitalize">
                      {conn.provider}
                      {conn.config?.url
                        ? ` · ${conn.config.url as string}`
                        : ''}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                    onClick={() => openEdit(conn)}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={() => deleteMutation.mutate(conn.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ─── AI Providers Section ───────────────────────────────────────────────────

function AIProvidersSection() {
  const queryClient = useQueryClient()
  const [openaiKey, setOpenaiKey] = useState('')
  const [anthropicKey, setAnthropicKey] = useState('')
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434')
  const [saved, setSaved] = useState(false)

  const { data: connections } = useQuery({
    queryKey: ['connections'],
    queryFn: fetchConnections,
  })

  useEffect(() => {
    if (connections) {
      const openai = connections.find((c) => c.provider === 'openai')
      const anthropic = connections.find((c) => c.provider === 'anthropic')
      const ollama = connections.find((c) => c.provider === 'ollama')
      if (openai) setOpenaiKey((openai.config?.api_key as string) || '')
      if (anthropic) setAnthropicKey((anthropic.config?.api_key as string) || '')
      if (ollama) setOllamaUrl((ollama.config?.url as string) || 'http://localhost:11434')
    }
  }, [connections])

  const handleSave = async () => {
    try {
      // Save each provider config
      const openaiConn = connections?.find((c) => c.provider === 'openai')
      const anthropicConn = connections?.find((c) => c.provider === 'anthropic')
      const ollamaConn = connections?.find((c) => c.provider === 'ollama')

      const updates = []
      if (openaiKey) {
        const config = { api_key: openaiKey }
        if (openaiConn) {
          updates.push(updateConnection(openaiConn.id, { config }))
        } else {
          updates.push(
            createConnection({
              name: 'OpenAI',
              provider: 'openai',
              config,
              is_active: true,
            }),
          )
        }
      }
      if (anthropicKey) {
        const config = { api_key: anthropicKey }
        if (anthropicConn) {
          updates.push(updateConnection(anthropicConn.id, { config }))
        } else {
          updates.push(
            createConnection({
              name: 'Anthropic',
              provider: 'anthropic',
              config,
              is_active: true,
            }),
          )
        }
      }
      if (ollamaUrl) {
        const config = { url: ollamaUrl }
        if (ollamaConn) {
          updates.push(updateConnection(ollamaConn.id, { config }))
        } else {
          updates.push(
            createConnection({
              name: 'Ollama',
              provider: 'ollama',
              config,
              is_active: true,
            }),
          )
        }
      }

      await Promise.all(updates)
      queryClient.invalidateQueries({ queryKey: ['connections'] })
      setSaved(true)
      setTimeout(() => setSaved(false), 2000)
    } catch {
      // Silently fail
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">AI Providers</h2>
        <p className="text-sm text-muted-foreground mt-1">
          Configure API keys and endpoints for AI model providers.
        </p>
      </div>

      <Separator />

      <div className="space-y-5">
        {/* OpenAI */}
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="rounded-lg bg-emerald-500/10 p-2">
              <Bot className="h-4 w-4 text-emerald-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">OpenAI</p>
              <p className="text-xs text-muted-foreground">GPT-4o, GPT-4, GPT-3.5</p>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">API Key</label>
            <Input
              type="password"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-..."
              className="font-mono text-xs"
            />
          </div>
        </div>

        {/* Anthropic */}
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="rounded-lg bg-amber-500/10 p-2">
              <Bot className="h-4 w-4 text-amber-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Anthropic</p>
              <p className="text-xs text-muted-foreground">Claude Sonnet, Claude Opus</p>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">API Key</label>
            <Input
              type="password"
              value={anthropicKey}
              onChange={(e) => setAnthropicKey(e.target.value)}
              placeholder="sk-ant-..."
              className="font-mono text-xs"
            />
          </div>
        </div>

        {/* Ollama */}
        <div className="rounded-lg border border-border bg-card p-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="rounded-lg bg-sky-500/10 p-2">
              <Server className="h-4 w-4 text-sky-500" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Ollama</p>
              <p className="text-xs text-muted-foreground">Local models (Llama, Mistral, etc.)</p>
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-medium text-muted-foreground">Server URL</label>
            <Input
              value={ollamaUrl}
              onChange={(e) => setOllamaUrl(e.target.value)}
              placeholder="http://localhost:11434"
              className="font-mono text-xs"
            />
          </div>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Button onClick={handleSave} className="gap-1.5">
          {saved ? (
            <>
              <Check className="h-4 w-4" />
              Saved
            </>
          ) : (
            'Save provider settings'
          )}
        </Button>
        {saved && (
          <span className="text-xs text-emerald-500 flex items-center gap-1">
            <Check className="h-3 w-3" />
            Configuration saved
          </span>
        )}
      </div>
    </div>
  )
}

// ─── General Section ────────────────────────────────────────────────────────

function GeneralSection() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-foreground">General</h2>
        <p className="text-sm text-muted-foreground mt-1">
          General application settings and preferences.
        </p>
      </div>

      <Separator />

      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">Default Model</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Model used for the AI chat when no specific model is selected.
            </p>
          </div>
          <Select defaultValue="gpt-4o">
            <SelectTrigger className="w-[180px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="gpt-4o">GPT-4o</SelectItem>
              <SelectItem value="claude-sonnet-4-20250514">Claude Sonnet 4</SelectItem>
              <SelectItem value="llama3.2">Llama 3.2</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">API Endpoint</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              Base URL for the ResearchOS API.
            </p>
          </div>
          <Input
            defaultValue={process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}
            className="w-[240px] font-mono text-xs h-8"
          />
        </div>
      </div>
    </div>
  )
}

// ─── Page ────────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState<SectionId>('api-keys')

  return (
    <div className="flex gap-6">
      {/* Sidebar navigation */}
      <div className="w-48 shrink-0 space-y-1">
        {sectionTabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeSection === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id)}
              className={cn(
                'flex items-center gap-2.5 w-full rounded-lg px-3 py-2 text-sm font-medium text-left transition-all',
                isActive
                  ? 'bg-primary/10 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
              )}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {activeSection === 'api-keys' && <APIKeysSection />}
        {activeSection === 'connections' && <ConnectionsSection />}
        {activeSection === 'providers' && <AIProvidersSection />}
        {activeSection === 'general' && <GeneralSection />}
      </div>
    </div>
  )
}
