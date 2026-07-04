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
  running: { label: 'Running', color: 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950', Icon: Play },
  active: { label: 'Active', color: 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950', Icon: Play },
  completed: { label: 'Completed', color: 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950', Icon: CheckCircle2 },
  success: { label: 'Success', color: 'text-emerald-600 bg-emerald-50 dark:text-emerald-400 dark:bg-emerald-950', Icon: CheckCircle2 },
  failed: { label: 'Failed', color: 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950', Icon: XCircle },
  error: { label: 'Error', color: 'text-red-600 bg-red-50 dark:text-red-400 dark:bg-red-950', Icon: XCircle },
  paused: { label: 'Paused', color: 'text-amber-600 bg-amber-50 dark:text-amber-400 dark:bg-amber-950', Icon: Pause },
  pending: { label: 'Pending', color: 'text-yellow-600 bg-yellow-50 dark:text-yellow-400 dark:bg-yellow-950', Icon: Clock },
  created: { label: 'Created', color: 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900', Icon: Clock },
  draft: { label: 'Draft', color: 'text-gray-600 bg-gray-50 dark:text-gray-400 dark:bg-gray-900', Icon: Clock },
  published: { label: 'Published', color: 'text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-950', Icon: CheckCircle2 },
  in_review: { label: 'In Review', color: 'text-purple-600 bg-purple-50 dark:text-purple-400 dark:bg-purple-950', Icon: AlertCircle },
  archived: { label: 'Archived', color: 'text-gray-500 bg-gray-100 dark:text-gray-500 dark:bg-gray-800', Icon: Clock },
  cancelled: { label: 'Cancelled', color: 'text-gray-500 bg-gray-100 dark:text-gray-500 dark:bg-gray-800', Icon: XCircle },
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
