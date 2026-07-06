'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { ChatMessage, type Message } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { ModelSelector } from './ModelSelector'
import { askStream } from '@/lib/api/ask'
import { fetchExperiments } from '@/lib/api/experiments'
import { fetchNotebooks } from '@/lib/api/notebooks'
import { useQuery } from '@tanstack/react-query'
import { useProjectStore } from '@/lib/store/project'
import { useAuthStore } from '@/lib/store/auth'
import Link from 'next/link'
import { cn } from '@/lib/utils'
import {
  FlaskConical,
  BookOpen,
  FileText,
  Search,
  ArrowDown,
  ChevronRight,
  AlertCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

let messageCounter = 0
function nextId() {
  messageCounter += 1
  return `msg-${Date.now()}-${messageCounter}`
}

const quickCreateItems = [
  {
    label: 'Experiment',
    description: 'Track runs and metrics',
    icon: FlaskConical,
    href: '/dashboard/experiments',
    color: 'text-primary',
    bgColor: 'bg-primary/5 hover:bg-primary/10',
    borderColor: 'hover:border-primary/30',
  },
  {
    label: 'Notebook',
    description: 'Write research documents',
    icon: BookOpen,
    href: '/dashboard/notebooks',
    color: 'text-indigo-500',
    bgColor: 'bg-indigo-500/5 hover:bg-indigo-500/10',
    borderColor: 'hover:border-indigo-500/30',
  },
  {
    label: 'Paper',
    description: 'Compose and publish',
    icon: FileText,
    href: '/dashboard/papers',
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/5 hover:bg-amber-500/10',
    borderColor: 'hover:border-amber-500/30',
  },
  {
    label: 'Search',
    description: 'Find across your workspace',
    icon: Search,
    href: '/dashboard/search',
    color: 'text-sky-500',
    bgColor: 'bg-sky-500/5 hover:bg-sky-500/10',
    borderColor: 'hover:border-sky-500/30',
  },
]

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d ago`
  return new Date(dateStr).toLocaleDateString()
}

function QuickCreateCards({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
      {quickCreateItems.map((item) => {
        const Icon = item.icon
        return (
          <Link
            key={item.label}
            href={item.href}
            onClick={onNavigate}
            className={cn(
              'flex flex-col items-center justify-center rounded-xl border border-border bg-card p-4 transition-all',
              item.bgColor,
              item.borderColor,
            )}
          >
            <Icon className={cn('h-5 w-5 mb-2', item.color)} />
            <span className="text-sm font-medium text-foreground">{item.label}</span>
            <span className="text-[11px] text-muted-foreground mt-0.5 text-center leading-tight">
              {item.description}
            </span>
          </Link>
        )
      })}
    </div>
  )
}

function RecentItems() {
  const currentProjectId = useProjectStore((s) => s.currentProjectId)

  const { data: experiments } = useQuery({
    queryKey: ['recent-experiments', currentProjectId ?? ''],
    queryFn: () =>
      fetchExperiments(currentProjectId ?? undefined).then((r) =>
        r
          .sort(
            (a, b) =>
              new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
          )
          .slice(0, 3),
      ),
    retry: 1,
    staleTime: 30000,
  })

  const { data: notebooks } = useQuery({
    queryKey: ['recent-notebooks', currentProjectId ?? ''],
    queryFn: () =>
      fetchNotebooks(currentProjectId ?? undefined).then((r) =>
        r
          .sort(
            (a, b) =>
              new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
          )
          .slice(0, 3),
      ),
    retry: 1,
    staleTime: 30000,
  })

  const allRecent =
    [
      ...(experiments?.map((e) => ({ type: 'experiment' as const, id: e.id, title: e.name, subtitle: e.status, updatedAt: e.updated_at, href: `/dashboard/experiments?id=${e.id}` })) ?? []),
      ...(notebooks?.map((n) => ({ type: 'notebook' as const, id: n.id, title: n.title, subtitle: n.branch, updatedAt: n.updated_at, href: `/dashboard/notebooks?id=${n.id}` })) ?? []),
    ]
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
      .slice(0, 5)

  if (!allRecent.length) return null

  return (
    <div className="w-full">
      <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
        Recent Activity
      </h3>
      <div className="space-y-1">
        {allRecent.map((item) => {
          const Icon = item.type === 'experiment' ? FlaskConical : BookOpen
          return (
            <Link
              key={`${item.type}-${item.id}`}
              href={item.href}
              className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-accent transition-colors group"
            >
              <Icon
                className={cn(
                  'h-3.5 w-3.5 shrink-0',
                  item.type === 'experiment' ? 'text-primary' : 'text-indigo-500',
                )}
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-foreground truncate">{item.title}</p>
                <p className="text-xs text-muted-foreground">{item.subtitle}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] text-muted-foreground">
                  {timeAgo(item.updatedAt)}
                </span>
                <ChevronRight className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const [hasStarted, setHasStarted] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  const currentProjectId = useProjectStore((s) => s.currentProjectId)
  const { user } = useAuthStore()

  const hour = new Date().getHours()
  let greeting = 'evening'
  if (hour < 12) greeting = 'morning'
  else if (hour < 17) greeting = 'afternoon'

  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' })
  }, [])

  useEffect(() => {
    if (hasStarted) {
      scrollToBottom()
    }
  }, [messages, scrollToBottom, hasStarted])

  const handleScroll = useCallback(() => {
    const el = messagesContainerRef.current
    if (el) {
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
      setShowScrollButton(distanceFromBottom > 200)
    }
  }, [])

  const handleSend = useCallback(
    async (content: string) => {
      if (isLoading) return

      setError(null)
      setHasStarted(true)

      const userMessage: Message = {
        id: nextId(),
        role: 'user',
        content,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMessage])

      const assistantId = nextId()
      const assistantMessage: Message = {
        id: assistantId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(true)

      try {
        let collected = ''

        for await (const event of askStream({
          message: content,
          model: selectedModel || undefined,
          session_id: sessionId || undefined,
          project_id: currentProjectId || undefined,
          stream: true,
        })) {
          if (event.type === 'token') {
            collected += event.content
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: collected } : m,
              ),
            )
          } else if (event.type === 'done') {
            setSessionId(event.content.session_id)
          } else if (event.type === 'tool_call') {
            collected += `\n\n_Using tool: **${event.content.name}**..._`
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId ? { ...m, content: collected } : m,
              ),
            )
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'An error occurred'
        setError(msg)
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? {
                  ...m,
                  content: `Error: ${msg}\n\nPlease try again or select a different model.`,
                }
              : m,
          ),
        )
      } finally {
        setIsLoading(false)
      }
    },
    [isLoading, selectedModel, sessionId, currentProjectId],
  )

  const handleStop = useCallback(() => {
    abortRef.current?.abort()
    setIsLoading(false)
  }, [])

  const clearChat = useCallback(() => {
    setMessages([])
    setSessionId(null)
    setError(null)
    setHasStarted(false)
  }, [])

  return (
    <div className="flex flex-col h-full relative">
      {/* Chat messages — hidden until first message */}
      {hasStarted && (
        <div
          ref={messagesContainerRef}
          onScroll={handleScroll}
          className="flex-1 overflow-y-auto"
        >
          <div className="max-w-3xl mx-auto px-4 pt-4 pb-4 space-y-6">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {error && (
              <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/5 rounded-lg px-4 py-2">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Scroll to bottom button */}
      {showScrollButton && hasStarted && (
        <div className="absolute bottom-28 left-1/2 -translate-x-1/2 z-10">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8 rounded-full shadow-md bg-background/80 backdrop-blur-sm"
            onClick={() => scrollToBottom(true)}
          >
            <ArrowDown className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Hub landing — shown before first message */}
      {!hasStarted && (
        <div className="flex-1 overflow-y-auto">
          <div className="min-h-full flex flex-col items-center justify-center px-4 py-12">
            <div className="w-full max-w-2xl mx-auto space-y-10">
              {/* Brand + Greeting */}
              <div className="text-center space-y-2">
                <h1 className="text-2xl font-semibold text-foreground tracking-tight">
                  Good {greeting}{user?.name ? `, ${user.name.split(' ')[0]}` : ''}
                </h1>
                <p className="text-sm text-muted-foreground">
                  Ask anything about your research, or create something new.
                </p>
              </div>

              {/* Input area — centered, prominent */}
              <div className="space-y-3">
                <div className="max-w-xl mx-auto">
                  <ChatInput
                    onSend={handleSend}
                    onStop={handleStop}
                    isLoading={isLoading}
                    placeholder="Ask about your research..."
                  />
                </div>
                <div className="flex justify-center">
                  <ModelSelector value={selectedModel} onChange={setSelectedModel} compact />
                </div>
              </div>

              {/* Quick create cards */}
              <QuickCreateCards />

              {/* Recent items */}
              <RecentItems />
            </div>
          </div>
        </div>
      )}

      {/* Input — pinned at bottom when chat is active */}
      {hasStarted && (
        <div className="border-t bg-background/95 backdrop-blur-sm shrink-0">
          <div className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-3">
            <div className="flex-1">
              <ChatInput
                onSend={handleSend}
                onStop={handleStop}
                isLoading={isLoading}
                placeholder="Ask a follow-up..."
              />
            </div>
            <div className="hidden sm:block shrink-0">
              <ModelSelector value={selectedModel} onChange={setSelectedModel} compact />
            </div>
          </div>
        </div>
      )}

      {/* New chat button — subtle, in corner when chat is active */}
      {hasStarted && (
        <button
          onClick={clearChat}
          className="absolute top-3 right-3 z-10 text-xs text-muted-foreground hover:text-foreground transition-colors px-3 py-1.5 rounded-md hover:bg-accent"
        >
          New chat
        </button>
      )}
    </div>
  )
}
