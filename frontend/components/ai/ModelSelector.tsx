'use client'

import React, { useEffect, useState } from 'react'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ModelInfo, fetchModels } from '@/lib/api/ask'
import { Sparkles } from 'lucide-react'

interface ModelSelectorProps {
  value: string
  onChange: (model: string) => void
}

export function ModelSelector({ value, onChange }: ModelSelectorProps) {
  const [models, setModels] = useState<ModelInfo[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const fetched = await fetchModels()
        if (!cancelled) {
          setModels(fetched)
          // Set default if none selected
          if (!value && fetched.length > 0) {
            onChange(fetched[0].id)
          }
        }
      } catch {
        // Models API might not be available — use sensible defaults
        if (!cancelled) {
          setModels([
            { id: 'gpt-4o', name: 'GPT-4o', provider: 'openai', description: 'OpenAI GPT-4o', available: true },
            { id: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4', provider: 'anthropic', description: 'Anthropic Claude Sonnet 4', available: true },
            { id: 'llama3.2', name: 'Llama 3.2', provider: 'ollama', description: 'Ollama Llama 3.2', available: true },
          ])
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Group models by provider
  const grouped = models.reduce<Record<string, ModelInfo[]>>((acc, m) => {
    if (!acc[m.provider]) acc[m.provider] = []
    acc[m.provider].push(m)
    return acc
  }, {})

  return (
    <Select
      value={value || undefined}
      onValueChange={onChange}
      disabled={loading}
    >
      <SelectTrigger className="h-8 w-[180px] text-xs border-dashed">
        <Sparkles className="h-3.5 w-3.5 mr-1 text-purple-500" />
        <SelectValue placeholder={loading ? 'Loading...' : 'Select model'} />
      </SelectTrigger>
      <SelectContent>
        {Object.entries(grouped).map(([provider, providerModels]) => (
          <React.Fragment key={provider}>
            <div className="px-2 py-1.5 text-[10px] font-semibold uppercase text-muted-foreground tracking-wider">
              {provider}
            </div>
            {providerModels.map((m) => (
              <SelectItem key={m.id} value={m.id} className="text-sm">
                {m.name}
              </SelectItem>
            ))}
          </React.Fragment>
        ))}
      </SelectContent>
    </Select>
  )
}
