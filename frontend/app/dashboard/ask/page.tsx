'use client'

import React from 'react'
import { ChatPanel } from '@/components/ai/ChatPanel'
import { Card } from '@/components/ui/card'

export default function AskPage() {
  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col">
      <Card className="flex-1 flex flex-col overflow-hidden shadow-sm border-border/60">
        <ChatPanel />
      </Card>
    </div>
  )
}
