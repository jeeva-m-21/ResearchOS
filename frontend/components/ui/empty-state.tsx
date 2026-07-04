'use client'

import { motion } from 'framer-motion'
import { fadeInUp } from '@/lib/hooks/use-motion'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon: React.ElementType
  title: string
  description?: string
  action?: React.ReactNode
  className?: string
}

export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <motion.div
      variants={fadeInUp}
      initial="hidden"
      animate="visible"
      className={cn(
        'flex flex-col items-center justify-center py-16 text-center',
        className,
      )}
    >
      <div className="rounded-full bg-accent p-4 mb-4">
        <Icon className="h-8 w-8 text-muted-foreground" />
      </div>
      <h3 className="text-lg font-semibold">{title}</h3>
      {description && (
        <p className="text-sm text-muted-foreground mt-1 max-w-sm">{description}</p>
      )}
      {action && <div className="mt-4">{action}</div>}
    </motion.div>
  )
}
