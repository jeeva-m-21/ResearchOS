'use client'

import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'
import { scaleIn } from '@/lib/hooks/use-motion'
import {
  Play,
  Pause,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
} from 'lucide-react'

type StatusType =
  | 'running'
  | 'active'
  | 'completed'
  | 'success'
  | 'failed'
  | 'error'
  | 'paused'
  | 'pending'
  | 'created'
  | 'draft'
  | 'published'
  | 'in_review'
  | 'archived'
  | 'cancelled'

interface StatusBadgeProps {
  status: StatusType
  className?: string
  /**
   * If true, shows just the dot without text label.
   * Useful for inline indicators in tables.
   */
  dotOnly?: boolean
}

const statusConfig: Record<StatusType, { label: string; color: string; Icon?: any }> = {
  running: { label: 'Running', color: 'text-foreground bg-accent', Icon: Play },
  active: { label: 'Active', color: 'text-foreground bg-accent', Icon: Play },
  completed: { label: 'Completed', color: 'text-secondary-foreground bg-secondary', Icon: CheckCircle2 },
  success: { label: 'Success', color: 'text-foreground bg-accent', Icon: CheckCircle2 },
  failed: { label: 'Failed', color: 'text-muted-foreground bg-muted', Icon: XCircle },
  error: { label: 'Error', color: 'text-muted-foreground bg-muted', Icon: XCircle },
  paused: { label: 'Paused', color: 'text-secondary-foreground bg-secondary', Icon: Pause },
  pending: { label: 'Pending', color: 'text-muted-foreground bg-muted', Icon: Clock },
  created: { label: 'Created', color: 'text-muted-foreground bg-muted', Icon: Clock },
  draft: { label: 'Draft', color: 'text-muted-foreground bg-muted', Icon: Clock },
  published: { label: 'Published', color: 'text-foreground bg-accent', Icon: CheckCircle2 },
  in_review: { label: 'In Review', color: 'text-secondary-foreground bg-secondary', Icon: AlertCircle },
  archived: { label: 'Archived', color: 'text-muted-foreground bg-muted', Icon: Clock },
  cancelled: { label: 'Cancelled', color: 'text-muted-foreground bg-muted', Icon: XCircle },
}

export function StatusBadge({ status, className, dotOnly }: StatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.pending
  const { label, color, Icon } = config

  // Running status gets a subtle pulse animation
  const isRunning = status === 'running' || status === 'active'

  if (dotOnly) {
    return (
      <span
        className={cn(
          'inline-block h-2 w-2 rounded-full',
          isRunning && 'animate-pulse-soft',
          color.split(' ')[0],
        )}
        title={label}
      />
    )
  }

  return (
    <motion.span
      variants={scaleIn}
      initial="hidden"
      animate="visible"
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        color,
        className,
      )}
    >
      {Icon ? (
        <Icon className={cn('h-3 w-3', isRunning && 'animate-pulse-soft')} />
      ) : (
        <span className="h-1.5 w-1.5 rounded-full bg-current" />
      )}
      {label}
    </motion.span>
  )
}
