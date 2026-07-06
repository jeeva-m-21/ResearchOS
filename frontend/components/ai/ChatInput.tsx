'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Send, Sparkles, StopCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  onStop: () => void
  isLoading: boolean
  disabled?: boolean
}

export function ChatInput({ onSend, onStop, isLoading, disabled }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 200) + 'px'
    }
  }, [input])

  // Focus on mount
  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  // Cmd+Enter to send
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        if (input.trim() && !isLoading) {
          onSend(input.trim())
          setInput('')
        }
      }
      if (e.key === 'Enter' && !e.shiftKey && !e.metaKey && !e.ctrlKey) {
        e.preventDefault()
        if (input.trim() && !isLoading) {
          onSend(input.trim())
          setInput('')
        }
      }
    },
    [input, isLoading, onSend],
  )

  const handleSend = () => {
    if (input.trim() && !isLoading) {
      onSend(input.trim())
      setInput('')
    }
  }

  return (
    <div className="flex items-end gap-2 border-t bg-background/95 backdrop-blur-sm p-4">
      <div className="relative flex-1">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about your research..."
          rows={1}
          disabled={disabled}
          className={cn(
            'flex w-full resize-none rounded-xl border border-input bg-muted/50 px-4 py-3 text-sm',
            'placeholder:text-muted-foreground/60',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'min-h-[44px] max-h-[200px]',
          )}
        />
      </div>

      {isLoading ? (
        <Button
          onClick={onStop}
          size="icon"
          variant="destructive"
          className="h-11 w-11 shrink-0 rounded-xl"
          title="Stop generating"
        >
          <StopCircle className="h-5 w-5" />
        </Button>
      ) : (
        <Button
          onClick={handleSend}
          size="icon"
          disabled={!input.trim() || disabled}
          className="h-11 w-11 shrink-0 rounded-xl bg-primary hover:bg-primary/90"
          title="Send (Enter)"
        >
          <Send className="h-5 w-5" />
        </Button>
      )}
    </div>
  )
}
