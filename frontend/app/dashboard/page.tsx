'use client'

import React from 'react'
import { ChatPanel } from '@/components/ai/ChatPanel'

export default function DashboardHome() {
  return (
    <div className="h-[calc(100vh-3.5rem)] -m-6">
      <ChatPanel />
    </div>
  )
}
