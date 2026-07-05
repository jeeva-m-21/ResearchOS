'use client'

import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useProjectStore } from '@/lib/store/project'
import { Plus } from 'lucide-react'

interface CreateProjectDialogProps {
  /** Optional trigger — defaults to a "+ Project" button */
  trigger?: React.ReactNode
  /** External open state control (optional) */
  open?: boolean
  /** External onOpenChange callback (optional) */
  onOpenChange?: (open: boolean) => void
  /** Called after the project is created and selected */
  onCreated?: () => void
}

export function CreateProjectDialog({ trigger, open: externalOpen, onOpenChange, onCreated }: CreateProjectDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false)
  const isControlled = externalOpen !== undefined
  const open = isControlled ? externalOpen : internalOpen
  const setOpen = isControlled ? onOpenChange ?? (() => {}) : setInternalOpen
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createAndSelectProject = useProjectStore((s) => s.createAndSelectProject)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Project name is required')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      await createAndSelectProject(name.trim(), description.trim() || undefined)
      setName('')
      setDescription('')
      setOpen(false)
      onCreated?.()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create project'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {!isControlled && (
        <DialogTrigger asChild>
          {trigger || (
            <Button variant="ghost" size="sm" className="w-full justify-start gap-2 px-2 text-sm">
              <Plus className="h-4 w-4" />
              New Project
            </Button>
          )}
        </DialogTrigger>
      )}
      <DialogContent className="sm:max-w-[425px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Create Project</DialogTitle>
            <DialogDescription>
              Projects contain experiments, notebooks, and papers. Give your project a name to
              get started.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <label htmlFor="project-name" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Name
              </label>
              <Input
                id="project-name"
                placeholder="e.g. LLM Fine-tuning Study"
                value={name}
                onChange={(e) => setName(e.target.value)}
                autoFocus
                required
              />
            </div>
            <div className="grid gap-2">
              <label htmlFor="project-description" className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
                Description (optional)
              </label>
              <textarea
                id="project-description"
                placeholder="Brief description of the project..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={3}
                className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
            {error && (
              <p className="text-sm text-destructive">{error}</p>
            )}
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
