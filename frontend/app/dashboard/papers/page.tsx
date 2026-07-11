'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FileText,
  Plus,
  Loader2,
  ExternalLink,
  Calendar,
  Clock,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { StatusBadge } from '@/components/ui/status-badge'
import { fetchPapers, createPaper, type Paper } from '@/lib/api/papers'

export default function PapersPage() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newAbstract, setNewAbstract] = useState('')
  const [newAuthors, setNewAuthors] = useState('')
  const [createError, setCreateError] = useState('')

  const { data: papers, isLoading } = useQuery({
    queryKey: ['papers'],
    queryFn: () => fetchPapers(),
  })

  const createMutation = useMutation({
    mutationFn: () => {
      const authorsJson = newAuthors
        ? JSON.stringify(newAuthors.split(',').map((a) => a.trim()).filter(Boolean))
        : undefined
      return createPaper(newTitle, newAbstract || undefined, authorsJson)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
      setShowCreate(false)
      setNewTitle('')
      setNewAbstract('')
      setNewAuthors('')
      setCreateError('')
    },
    onError: (err: Error) => setCreateError(err.message),
  })

  const handleCreate = () => {
    if (!newTitle.trim()) return
    setCreateError('')
    createMutation.mutate()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-6 w-6 text-foreground" />
          <h1 className="text-2xl font-bold text-foreground">Papers</h1>
        </div>
        <Dialog open={showCreate} onOpenChange={setShowCreate}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-1" />
              New Paper
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New Paper</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 pt-2">
              <div>
                <label className="text-sm font-medium">Title *</label>
                <Input
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="Paper title..."
                />
              </div>
              <div>
                <label className="text-sm font-medium">Authors (comma-separated)</label>
                <Input
                  value={newAuthors}
                  onChange={(e) => setNewAuthors(e.target.value)}
                  placeholder="Alice Smith, Bob Jones"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Abstract</label>
                <Textarea
                  value={newAbstract}
                  onChange={(e) => setNewAbstract(e.target.value)}
                  placeholder="Optional abstract..."
                  rows={3}
                />
              </div>
              {createError && (
                <p className="text-sm text-destructive">{createError}</p>
              )}
              <div className="flex justify-end gap-2">
                <Button variant="ghost" onClick={() => setShowCreate(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={handleCreate}
                  disabled={!newTitle.trim() || createMutation.isPending}
                >
                  {createMutation.isPending ? (
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  ) : (
                    <Plus className="h-4 w-4 mr-1" />
                  )}
                  Create
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Description */}
      <p className="text-muted-foreground">
        Compose and manage research papers with AI-assisted writing and citation management.
      </p>

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 bg-muted rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {/* Paper list */}
      {!isLoading && papers && papers.length > 0 ? (
        <div className="space-y-3">
          {papers.map((paper) => (
            <Link key={paper.id} href={`/dashboard/papers/${paper.id}`}>
              <div className="group rounded-xl bg-card p-5 shadow-sm border border-border hover:border-primary/30 hover:shadow-md transition-all cursor-pointer">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3">
                      <h3 className="text-base font-semibold text-foreground group-hover:text-primary transition-colors truncate">
                        {paper.title}
                      </h3>
                      <StatusBadge status={paper.status as any} />
                    </div>
                    {paper.abstract && (
                      <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                        {paper.abstract}
                      </p>
                    )}
                    <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                      {paper.authors && paper.authors.length > 0 && (
                        <span className="flex items-center gap-1">
                          {paper.authors.slice(0, 3).join(', ')}
                          {paper.authors.length > 3 ? ' et al.' : ''}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(paper.created_at).toLocaleDateString()}
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        v{paper.version}
                      </span>
                    </div>
                  </div>
                  <ExternalLink className="h-4 w-4 text-muted-foreground/40 group-hover:text-primary ml-3 shrink-0 mt-1" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : !isLoading ? (
        <div className="rounded-xl bg-card p-8 shadow-sm border border-border text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-primary/10 mb-3">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <p className="text-foreground font-medium">No papers yet</p>
          <p className="text-sm text-muted-foreground mt-1">
            Create your first paper to get started.
          </p>
          <Button className="mt-4" onClick={() => setShowCreate(true)}>
            <Plus className="h-4 w-4 mr-1" />
            New Paper
          </Button>
        </div>
      ) : null}
    </div>
  )
}
