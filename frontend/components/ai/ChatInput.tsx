'use client'

import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Send, StopCircle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  onStop: () => void
  isLoading: boolean
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({ onSend, onStop, isLoading, disabled, placeholder }: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    const el = textareaRef.current
    if (el) {
      el.style.height = 'auto'
      el.style.height = Math.min(el.scrollHeight, 160) + 'px'
    }
  }, [input])

  useEffect(() => {
    textareaRef.current?.focus()
  }, [])

  const handleSend = useCallback(() => {
    if (input.trim() && !isLoading) {
      onSend(input.trim())
      setInput('')
    }
  }, [input, isLoading, onSend])

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault()
        handleSend()
      }
    },
    [handleSend],
  )

  return (
    <div className="flex items-end gap-2">
      <div className="relative flex-1">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || 'Ask about your research...'}
          rows={1}
          disabled={disabled || isLoading}
          className={cn(
            'w-full resize-none rounded-2xl border border-border/60 bg-muted/30 px-5 py-3.5 pr-14 text-sm',
            'placeholder:text-muted-foreground/50',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/30 focus-visible:border-ring',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'min-h-[52px] max-h-[160px]',
            'transition-all',
          )}
        />
        {isLoading ? (
          <Button
            onClick={onStop}
            size="icon"
            variant="ghost"
            className="absolute right-1.5 bottom-1.5 h-9 w-9 rounded-xl text-destructive hover:text-destructive hover:bg-destructive/10"
            title="Stop generating"
          >
            <StopCircle className="h-5 w-5" />
          </Button>
        ) : (
          <Button
            onClick={handleSend}
            size="icon"
            disabled={!input.trim() || disabled}
            className={cn(
              'absolute right-1.5 bottom-1.5 h-9 w-9 rounded-xl transition-all',
              input.trim()
                ? 'bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm'
                : 'bg-muted text-muted-foreground',
            )}
            title="Send"
          >
            <Send className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}
