'use client'

import { motion } from 'framer-motion'
import { fadeInUp } from '@/lib/hooks/use-motion'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { ChevronLeft } from 'lucide-react'

interface PageHeaderProps {
  title: string
  description?: string
  actions?: React.ReactNode
  onBack?: () => void
  className?: string
}

export function PageHeader({ title, description, actions, onBack, className }: PageHeaderProps) {
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      className={cn('flex items-start justify-between border-b pb-6 mb-6', className)}
    >
      <div className="flex items-start gap-3 min-w-0">
        {onBack && (
          <Button variant="ghost" size="icon" onClick={onBack} className="mt-0.5 shrink-0">
            <ChevronLeft className="h-5 w-5" />
          </Button>
        )}
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          {description && (
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </motion.div>
  )
}
