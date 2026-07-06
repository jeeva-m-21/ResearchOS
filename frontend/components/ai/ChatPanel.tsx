'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { ChatMessage, type Message } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { ModelSelector } from './ModelSelector'
import { askStream, type StreamEvent } from '@/lib/api/ask'
import { Card } from '@/components/ui/card'
import { MessageSquare, Sparkles, AlertCircle } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useProjectStore } from '@/lib/store/project'

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
  const abortRef = useRef<AbortController | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const currentProjectId = useProjectStore((s) => s.currentProjectId)

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, scrollToBottom])

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
            // Optionally show tool calls in the UI
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

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3 border-b bg-background/50">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-purple-600/10">
            <Sparkles className="h-4 w-4 text-purple-600" />
          </div>
          <h2 className="text-sm font-semibold">AI Assistant</h2>
          {isLoading && (
            <span className="text-[10px] text-muted-foreground animate-pulse ml-1">
              thinking...
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <ModelSelector value={selectedModel} onChange={setSelectedModel} />
          {messages.length > 1 && (
            <button
              onClick={clearChat}
              className="text-[11px] text-muted-foreground hover:text-foreground transition-colors px-2 py-1 rounded-md hover:bg-accent"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}

        {error && (
          <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/5 rounded-lg px-4 py-2">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        onStop={handleStop}
        isLoading={isLoading}
      />
    </div>
  )
}
