'use client'

import { useCallback, useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ArrowLeft,
  FileText,
  Save,
  Loader2,
  RefreshCw,
  BookOpen,
  Hash,
  Calendar,
  User,
  Tag,
  Globe,
  ExternalLink,
  Trash2,
  Plus,
  Play,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  fetchPaper,
  fetchCitations,
  updatePaper,
  deletePaper,
  addCitation,
  deleteCitation,
  type Paper,
  type Citation,
} from '@/lib/api/papers'
import { StatusBadge } from '@/components/ui/status-badge'
import dynamic from 'next/dynamic'

// Dynamically import CodeMirror to avoid SSR issues
const CodeMirror = dynamic(
  () => import('@uiw/react-codemirror').then((mod) => mod.default),
  { ssr: false, loading: () => <div className="h-64 bg-muted rounded-lg animate-pulse" /> }
)

// ---------- Info card ----------

function InfoCard({ icon: Icon, label, value, sub }: { icon: React.ElementType; label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-xl bg-card p-4 shadow-sm border border-border">
      <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className="text-sm font-medium text-foreground break-all">{value}</p>
      {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
    </div>
  )
}

// ---------- Citation row ----------

function CitationRow({ citation, paperId, onDelete }: { citation: Citation; paperId: string; onDelete: () => void }) {
  return (
    <div className="group flex items-start justify-between p-3 rounded-lg border border-border bg-card hover:bg-accent/50 transition-all">
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground truncate">
          [{citation.citation_key}] {citation.title}
        </p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {citation.authors?.slice(0, 3).join(', ')}{citation.authors?.length > 3 ? ' et al.' : ''} ({citation.year})
          {citation.venue ? ` — ${citation.venue}` : ''}
        </p>
      </div>
      <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 shrink-0 ml-2" onClick={onDelete}>
        <Trash2 className="h-4 w-4 text-destructive" />
      </Button>
    </div>
  )
}

// ---------- Page ----------

export default function PaperDetailPage() {
  const params = useParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const paperId = params.id as string

  // Editable fields
  const [title, setTitle] = useState('')
  const [abstract, setAbstract] = useState('')
  const [status, setStatus] = useState('draft')
  const [authorsStr, setAuthorsStr] = useState('')
  const [doi, setDoi] = useState('')
  const [arxivId, setArxivId] = useState('')
  const [latexContent, setLatexContent] = useState('')
  const [hasChanges, setHasChanges] = useState(false)
  const [saveError, setSaveError] = useState('')

  // New citation form
  const [newCiteKey, setNewCiteKey] = useState('')
  const [newCiteTitle, setNewCiteTitle] = useState('')
  const [newCiteAuthors, setNewCiteAuthors] = useState('')
  const [newCiteYear, setNewCiteYear] = useState(new Date().getFullYear().toString())
  const [showAddCitation, setShowAddCitation] = useState(false)

  // Fetch paper
  const { data: paper, isLoading, isError } = useQuery({
    queryKey: ['paper', paperId],
    queryFn: () => fetchPaper(paperId),
    enabled: !!paperId,
  })

  // Initialize form fields from fetched data
  useEffect(() => {
    if (paper) {
      setTitle(paper.title)
      setAbstract(paper.abstract ?? '')
      setStatus(paper.status)
      setAuthorsStr(Array.isArray(paper.authors) ? paper.authors.join(', ') : '')
      setDoi(paper.doi ?? '')
      setArxivId(paper.arxiv_id ?? '')
      setLatexContent(paper.latex_content ?? '')
      setHasChanges(false)
    }
  }, [paper])

  // Save mutation
  const saveMutation = useMutation({
    mutationFn: async () => {
      const data: Record<string, string> = {}
      if (title !== paper?.title) data.title = title
      if (abstract !== (paper?.abstract ?? '')) data.abstract = abstract
      if (status !== paper?.status) data.status = status
      const authorsJson = authorsStr ? JSON.stringify(authorsStr.split(',').map((a) => a.trim()).filter(Boolean)) : '[]'
      data.authors = authorsJson
      if (doi !== (paper?.doi ?? '')) data.doi = doi
      if (arxivId !== (paper?.arxiv_id ?? '')) data.arxiv_id = arxivId
      if (latexContent !== (paper?.latex_content ?? '')) data.latex_content = latexContent
      return updatePaper(paperId, data)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['paper', paperId] })
      queryClient.invalidateQueries({ queryKey: ['papers'] })
      setHasChanges(false)
      setSaveError('')
    },
    onError: (err: Error) => {
      setSaveError(err.message)
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => deletePaper(paperId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['papers'] })
      router.push('/dashboard/papers')
    },
    onError: (err: Error) => setSaveError(err.message),
  })

  // Add citation mutation
  const addCiteMutation = useMutation({
    mutationFn: () =>
      addCitation(
        paperId,
        newCiteKey,
        newCiteTitle,
        parseInt(newCiteYear),
        undefined,
        newCiteAuthors ? JSON.stringify(newCiteAuthors.split(',').map((a) => a.trim())) : undefined,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['citations', paperId] })
      setNewCiteKey('')
      setNewCiteTitle('')
      setNewCiteAuthors('')
      setNewCiteYear(new Date().getFullYear().toString())
      setShowAddCitation(false)
    },
    onError: (err: Error) => setSaveError(err.message),
  })

  // Remove citation
  const removeCiteMutation = useMutation({
    mutationFn: (citationId: string) => deleteCitation(paperId, citationId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['citations', paperId] }),
  })

  // Fetch citations
  const { data: citations } = useQuery({
    queryKey: ['citations', paperId],
    queryFn: () => fetchCitations(paperId),
    enabled: !!paperId,
  })

  const trackChange = useCallback(() => { setHasChanges(true) }, [])

  // Loading
  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-32 bg-muted rounded-lg animate-pulse" />
        <div className="h-8 w-64 bg-muted rounded-lg animate-pulse" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 bg-muted rounded-xl animate-pulse" />
          ))}
        </div>
        <div className="h-64 bg-muted rounded-lg animate-pulse" />
      </div>
    )
  }

  // Error
  if (isError || !paper) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back
        </Button>
        <div className="rounded-xl bg-destructive/10 p-4 border border-destructive/20">
          <p className="text-sm text-destructive">Paper not found.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Back button */}
      <div>
        <Button variant="ghost" size="sm" onClick={() => router.push('/dashboard/papers')}>
          <ArrowLeft className="h-4 w-4 mr-1" /> Back to Papers
        </Button>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <div className="rounded-xl p-3 bg-blue-100 dark:bg-blue-900/30 shrink-0">
            <FileText className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div className="min-w-0 flex-1">
            <Input
              value={title}
              onChange={(e) => { setTitle(e.target.value); trackChange() }}
              className="text-2xl font-bold border-0 px-0 bg-transparent focus-visible:ring-0 focus-visible:border-b focus-visible:border-primary h-auto pb-1"
            />
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Select value={status} onValueChange={(v) => { setStatus(v); trackChange() }}>
            <SelectTrigger className="w-[130px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="in_review">In Review</SelectItem>
              <SelectItem value="published">Published</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              queryClient.invalidateQueries({ queryKey: ['paper', paperId] })
              queryClient.invalidateQueries({ queryKey: ['citations', paperId] })
            }}
          >
            <RefreshCw className="h-4 w-4 mr-1" />
            Refresh
          </Button>
          <Button size="sm" onClick={() => saveMutation.mutate()} disabled={!hasChanges || saveMutation.isPending}>
            {saveMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            ) : (
              <Save className="h-4 w-4 mr-1" />
            )}
            Save
          </Button>
        </div>
      </div>

      {/* Error messages */}
      {saveError && (
        <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive border border-destructive/20">
          {saveError}
        </div>
      )}

      {/* Info cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <InfoCard
          icon={Calendar}
          label="Created"
          value={new Date(paper.created_at).toLocaleDateString()}
          sub={`v${paper.version}`}
        />
        <InfoCard icon={Hash} label="Status" value={status.charAt(0).toUpperCase() + status.slice(1)} />
        <InfoCard
          icon={User}
          label="Authors"
          value={authorsStr || '—'}
        />
        <div className="rounded-xl bg-card p-4 shadow-sm border border-border">
          <div className="flex items-center gap-2 text-xs text-muted-foreground mb-1">
            <Globe className="h-3.5 w-3.5" />
            Identifiers
          </div>
          <div className="flex flex-col gap-0.5">
            {doi && (
              <a href={`https://doi.org/${doi}`} target="_blank" rel="noopener noreferrer"
                 className="text-xs text-primary hover:underline flex items-center gap-1">
                DOI: {doi} <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {arxivId && (
              <a href={`https://arxiv.org/abs/${arxivId}`} target="_blank" rel="noopener noreferrer"
                 className="text-xs text-primary hover:underline flex items-center gap-1">
                arXiv: {arxivId} <ExternalLink className="h-3 w-3" />
              </a>
            )}
            {!doi && !arxivId && <span className="text-xs text-muted-foreground">None</span>}
          </div>
        </div>
      </div>

      {/* DOI + arXiv inline edit */}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <Label htmlFor="doi">DOI</Label>
          <Input
            id="doi"
            value={doi}
            onChange={(e) => { setDoi(e.target.value); trackChange() }}
            placeholder="10.1234/example"
          />
        </div>
        <div>
          <Label htmlFor="arxiv">arXiv ID</Label>
          <Input
            id="arxiv"
            value={arxivId}
            onChange={(e) => { setArxivId(e.target.value); trackChange() }}
            placeholder="2401.00001"
          />
        </div>
      </div>

      {/* Abstract */}
      <div>
        <Label htmlFor="abstract">Abstract</Label>
        <Textarea
          id="abstract"
          value={abstract}
          onChange={(e) => { setAbstract(e.target.value); trackChange() }}
          placeholder="Paper abstract..."
          rows={4}
        />
      </div>

      {/* LaTeX editor */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <Label className="flex items-center gap-2">
            <FileText className="h-4 w-4" />
            LaTeX Source
          </Label>
          <span className="text-xs text-muted-foreground">
            {latexContent.length} characters
          </span>
        </div>
        <div className="border border-border rounded-lg overflow-hidden">
          <CodeMirror
            value={latexContent}
            onChange={(val: string) => { setLatexContent(val); trackChange() }}
            height="400px"
            theme="dark"
            basicSetup={{
              lineNumbers: true,
              highlightActiveLineGutter: true,
              highlightActiveLine: true,
              foldGutter: true,
              autocompletion: true,
              bracketMatching: true,
              indentOnInput: true,
            }}
            placeholder="\documentclass{article}\n\usepackage{amsmath}\n\n\begin{document}\n\title{Your Paper Title}\n\maketitle\n\n\section{Introduction}\n\n% Write your paper here...\n\n\end{document}"
          />
        </div>
        <p className="text-xs text-muted-foreground mt-1">
          Write your paper in LaTeX format. Use the Compile button to generate a PDF preview.
        </p>
      </div>

      {/* Citations */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Citations ({citations?.length ?? 0})
          </h2>
          <Button size="sm" variant="outline" onClick={() => setShowAddCitation(!showAddCitation)}>
            <Plus className="h-4 w-4 mr-1" />
            Add Citation
          </Button>
        </div>

        {showAddCitation && (
          <div className="rounded-xl bg-card p-4 shadow-sm border border-border mb-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="citeKey" className="text-xs">Citation Key</Label>
                <Input
                  id="citeKey"
                  value={newCiteKey}
                  onChange={(e) => setNewCiteKey(e.target.value)}
                  placeholder="author2024title"
                  size={1}
                />
              </div>
              <div>
                <Label htmlFor="citeYear" className="text-xs">Year</Label>
                <Input
                  id="citeYear"
                  value={newCiteYear}
                  onChange={(e) => setNewCiteYear(e.target.value)}
                  placeholder="2024"
                  size={1}
                />
              </div>
            </div>
            <div>
              <Label htmlFor="citeTitle" className="text-xs">Title</Label>
              <Input
                id="citeTitle"
                value={newCiteTitle}
                onChange={(e) => setNewCiteTitle(e.target.value)}
                placeholder="Paper title..."
              />
            </div>
            <div>
              <Label htmlFor="citeAuthors" className="text-xs">Authors (comma-separated)</Label>
              <Input
                id="citeAuthors"
                value={newCiteAuthors}
                onChange={(e) => setNewCiteAuthors(e.target.value)}
                placeholder="Alice Smith, Bob Jones"
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button variant="ghost" size="sm" onClick={() => setShowAddCitation(false)}>Cancel</Button>
              <Button
                size="sm"
                onClick={() => addCiteMutation.mutate()}
                disabled={!newCiteKey || !newCiteTitle || addCiteMutation.isPending}
              >
                {addCiteMutation.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Plus className="h-4 w-4 mr-1" />}
                Add
              </Button>
            </div>
          </div>
        )}

        {citations && citations.length > 0 ? (
          <div className="space-y-2">
            {citations.map((c) => (
              <CitationRow
                key={c.id}
                citation={c}
                paperId={paperId}
                onDelete={() => removeCiteMutation.mutate(c.id)}
              />
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-card p-6 shadow-sm border border-border text-center">
            <BookOpen className="h-8 w-8 text-muted-foreground/40 mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No citations yet. Add your first citation.</p>
          </div>
        )}
      </div>

      {/* Danger zone */}
      <div className="rounded-xl border border-destructive/20 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-foreground">Delete this paper</p>
            <p className="text-xs text-muted-foreground">This action cannot be undone.</p>
          </div>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => {
              if (window.confirm('Are you sure you want to delete this paper?')) {
                deleteMutation.mutate()
              }
            }}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <Trash2 className="h-4 w-4 mr-1" />}
            Delete
          </Button>
        </div>
      </div>
    </div>
  )
}
