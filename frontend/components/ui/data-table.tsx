'use client'

import { cn } from '@/lib/utils'
import { motion } from 'framer-motion'
import { staggerContainer, fadeInUp } from '@/lib/hooks/use-motion'
import { Loader2 } from 'lucide-react'

export interface Column<T> {
  key: string
  header: string
  cell: (item: T) => React.ReactNode
  className?: string
  sortable?: boolean
}

interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyExtractor: (item: T) => string
  onRowClick?: (item: T) => void
  isLoading?: boolean
  emptyState?: React.ReactNode
  className?: string
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  isLoading,
  emptyState,
  className,
}: DataTableProps<T>) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    )
  }

  if (!data.length) {
    return emptyState ? <>{emptyState}</> : null
  }

  return (
    <div className={cn('rounded-lg border overflow-hidden', className)}>
      <motion.table
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="w-full text-sm"
      >
        <thead>
          <tr className="border-b bg-muted/50">
            {columns.map((col) => (
              <th
                key={col.key}
                className={cn(
                  'py-3 px-4 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider',
                  col.className,
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((item) => (
            <motion.tr
              key={keyExtractor(item)}
              variants={fadeInUp}
              className={cn(
                'border-b last:border-0 transition-colors',
                onRowClick && 'cursor-pointer hover:bg-accent/50',
              )}
              onClick={() => onRowClick?.(item)}
            >
              {columns.map((col) => (
                <td key={col.key} className={cn('py-3 px-4', col.className)}>
                  {col.cell(item)}
                </td>
              ))}
            </motion.tr>
          ))}
        </tbody>
      </motion.table>
    </div>
  )
}
