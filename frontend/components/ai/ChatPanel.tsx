'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { ChatMessage, type Message } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { ModelSelector } from './ModelSelector'
import { askStream, type StreamEvent } from '@/lib/api/ask'
import { MessageSquare, Sparkles, AlertCircle, ArrowDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useProjectStore } from '@/lib/store/project'
import { Button } from '@/components/ui/button'

let messageCounter = 0
function nextId() {
  messageCounter += 1
  return `msg-${Date.now()}-${messageCounter}`
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hello! I\'m your **ResearchOS AI assistant**. I can help you:\n\n' +
        '- 🔍 **Search** across experiments, notebooks, and papers\n' +
        '- 📊 **Analyze** experiment results and metrics\n' +
        '- 📓 **Read** notebook contents\n' +
        '- 💡 **Answer** questions about your research\n\n' +
        'What would you like to explore?',
      timestamp: new Date(),
    },
  ])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  const currentProjectId = useProjectStore((s) => s.currentProjectId)

  // Auto-scroll to bottom
  const scrollToBottom = useCallback((smooth = true) => {
    messagesEndRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

  // Show scroll-to-bottom button when scrolled up
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

      // Add user message
      const userMessage: Message = {
        id: nextId(),
        role: 'user',
        content,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, userMessage])

      // Add placeholder for assistant
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
            collected += `\n\n_🔧 Using tool: **${event.content.name}**..._`
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
                  content: `**Error**: ${msg}\n\nPlease try again or select a different model.`,
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
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: 'Hello! I\'m your **ResearchOS AI assistant**. How can I help you today?',
        timestamp: new Date(),
      },
    ])
    setSessionId(null)
    setError(null)
  }, [])

  const hasMessages = messages.length > 1

  return (
    <div className="flex flex-col h-full relative">
      {/* Floating header — model selector */}
      <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center pointer-events-none">
        <div className="pointer-events-auto flex items-center gap-3 bg-background/80 backdrop-blur-sm border border-border/50 rounded-full px-4 py-1.5 shadow-xs mt-3">
          <ModelSelector value={selectedModel} onChange={setSelectedModel} />
          {hasMessages && (
            <button
              onClick={clearChat}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-accent"
            >
              New chat
            </button>
          )}
        </div>
      </div>

      {/* Messages — centered */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto"
      >
        <div className="max-w-3xl mx-auto px-4 pt-16 pb-4 space-y-6">
          {/* Welcome header when no conversation started */}
          {!hasMessages && (
            <div className="text-center pt-12 pb-6 animate-fade-in-down">
              <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 mb-5">
                <Sparkles className="h-7 w-7 text-primary" />
              </div>
              <h1 className="text-2xl font-bold text-foreground mb-2">
                How can I help you?
              </h1>
              <p className="text-sm text-muted-foreground max-w-md mx-auto">
                Ask about your experiments, notebooks, papers, or anything in your research workspace.
              </p>
            </div>
          )}

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

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-10">
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

      {/* Input — centered */}
      <div className="border-t bg-background/95 backdrop-blur-sm">
        <div className="max-w-3xl mx-auto px-4 py-3">
          <ChatInput
            onSend={handleSend}
            onStop={handleStop}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  )
}
