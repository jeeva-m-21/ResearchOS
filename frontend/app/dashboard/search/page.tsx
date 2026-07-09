'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import {
  Search,
  Loader2,
  X,
  Clock,
  ArrowRight,
  Lightbulb,
  FlaskConical,
  FileText,
  Database,
  Cpu,
  BookOpen,
  User,
  MessageSquareQuote,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  searchResults,
  fetchSuggestions,
  NODE_TYPES,
  type SearchResult,
  type SearchResponse,
  type SuggestionResult,
} from '@/lib/api/search'

function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value)

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(timer)
  }, [value, delay])

  return debouncedValue
}

function getNodeIcon(nodeType: string) {
  const icons: Record<string, typeof Lightbulb> = {
    idea: Lightbulb,
    hypothesis: Lightbulb,
    experiment: FlaskConical,
    paper: FileText,
    dataset: Database,
    model: Cpu,
    notebook: BookOpen,
    person: User,
    insight: MessageSquareQuote,
  }
  return icons[nodeType] || Search
}

function getNodeColor(nodeType: string): string {
  const colors: Record<string, string> = {
    idea: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    hypothesis: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    experiment: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    paper: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    dataset: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    model: 'bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400',
    notebook: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400',
    person: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-400',
  }
  return colors[nodeType] || 'bg-muted text-muted-foreground'
}

function TypeFilterChip({
  type,
  selected,
  onClick,
}: {
  type: (typeof NODE_TYPES)[number]
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-medium transition-colors border ${
        selected
          ? 'bg-primary text-primary-foreground border-primary'
          : 'bg-card text-muted-foreground border-border hover:border-foreground/30 hover:text-foreground'
      }`}
    >
      {type.label}
      {selected && <X className="ml-1 h-3 w-3" />}
    </button>
  )
}

function SearchResultCard({ result }: { result: SearchResult }) {
  const Icon = getNodeIcon(result.node_type)
  const colorClass = getNodeColor(result.node_type)

  return (
    <Link
      href={
        result.node_type === 'experiment'
          ? `/dashboard/experiments/${result.id}`
          : result.node_type === 'notebook'
            ? `/dashboard/notebooks/${result.id}`
            : '#'
      }
      className="block"
    >
      <div className="rounded-xl bg-card p-5 shadow-sm border border-border hover:shadow-md hover:border-foreground/20 transition-all cursor-pointer">
        <div className="flex items-start gap-3">
          <div className={`rounded-lg p-2 ${colorClass}`}>
            <Icon className="h-4 w-4" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-foreground truncate">{result.title}</h3>
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium shrink-0 ${colorClass}`}>
                {result.node_type}
              </span>
            </div>
            {result.description && (
              <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                {result.description}
              </p>
            )}
            <div className="flex items-center gap-3 mt-2">
              <span className="text-xs text-muted-foreground">
                Relevance: {(result.score * 100).toFixed(0)}%
              </span>
              <ArrowRight className="h-3 w-3 text-muted-foreground" />
            </div>
          </div>
        </div>
      </div>
    </Link>
  )
}

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [selectedTypes, setSelectedTypes] = useState<string[]>([])
  const [offset, setOffset] = useState(0)
  const [showSuggestions, setShowSuggestions] = useState(false)
  const [suggestions, setSuggestions] = useState<SuggestionResult[]>([])
  const inputRef = useRef<HTMLInputElement>(null)
  const suggestionsRef = useRef<HTMLDivElement>(null)
  const debouncedQuery = useDebounce(query, 300)
  const debouncedSuggestQuery = useDebounce(query, 150)
  const limit = 10

  // Fetch autocomplete suggestions
  useEffect(() => {
    if (debouncedSuggestQuery.trim().length < 1) {
      setSuggestions([])
      return
    }
    let cancelled = false
    fetchSuggestions(debouncedSuggestQuery).then((data) => {
      if (!cancelled) {
        setSuggestions(data)
        setShowSuggestions(data.length > 0)
      }
    })
    return () => { cancelled = true }
  }, [debouncedSuggestQuery])

  // Search query
  const {
    data: searchData,
    isLoading,
    isError,
    error,
    isFetching,
  } = useQuery<SearchResponse>({
    queryKey: ['search', debouncedQuery, selectedTypes, offset, limit],
    queryFn: () =>
      searchResults({
        q: debouncedQuery,
        types: selectedTypes.length > 0 ? selectedTypes : undefined,
        limit,
        offset,
      }),
    enabled: debouncedQuery.trim().length > 0,
  })

  const handleTypeToggle = useCallback((type: string) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    )
    setOffset(0)
  }, [])

  const handleClear = useCallback(() => {
    setQuery('')
    setOffset(0)
    setSelectedTypes([])
    inputRef.current?.focus()
  }, [])

  const totalPages = searchData ? Math.ceil(searchData.total / limit) : 0
  const currentPage = Math.floor(offset / limit) + 1

  // Close suggestions on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(e.target as Node) &&
        inputRef.current &&
        !inputRef.current.contains(e.target as Node)
      ) {
        setShowSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Search className="h-6 w-6 text-foreground" />
        <h1 className="text-2xl font-bold text-foreground">Search</h1>
      </div>
      <p className="text-muted-foreground -mt-4">
        Semantic and keyword search across all your research assets.
      </p>

      {/* Search input */}
      <div className="relative" ref={suggestionsRef}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value)
              setOffset(0)
            }}
            onFocus={() => {
              if (suggestions.length > 0) setShowSuggestions(true)
            }}
            placeholder="Search research assets... (e.g., transformer, reinforcement learning)"
            className="w-full rounded-xl border border-border bg-card py-3.5 pl-10 pr-10 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent transition-all"
            autoComplete="off"
          />
          {query && (
            <button
              onClick={handleClear}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Suggestions dropdown */}
        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-50 mt-1 w-full rounded-xl bg-card border border-border shadow-lg p-1">
            {suggestions.map((suggestion) => {
              const Icon = getNodeIcon(suggestion.node_type)
              return (
                <button
                  key={suggestion.id}
                  onClick={() => {
                    setQuery(suggestion.title)
                    setShowSuggestions(false)
                    setOffset(0)
                  }}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-accent transition-colors text-left"
                >
                  <Icon className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                  <span className="flex-1 truncate">{suggestion.title}</span>
                  <span className="text-[10px] uppercase text-muted-foreground bg-muted rounded px-1.5 py-0.5 shrink-0">
                    {suggestion.node_type}
                  </span>
                </button>
              )
            })}
          </div>
        )}
      </div>

      {/* Type filters */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground font-medium mr-1">Filter by type:</span>
        {NODE_TYPES.map((type) => (
          <TypeFilterChip
            key={type.value}
            type={type}
            selected={selectedTypes.includes(type.value)}
            onClick={() => handleTypeToggle(type.value)}
          />
        ))}
        {selectedTypes.length > 0 && (
          <button
            onClick={() => setSelectedTypes([])}
            className="text-xs text-muted-foreground hover:text-foreground ml-1 underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {/* Results info bar */}
      {searchData && (
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Clock className="h-3.5 w-3.5" />
          <span>
            Found {searchData.total} result{searchData.total !== 1 ? 's' : ''} for &ldquo;{searchData.query}&rdquo; in{' '}
            {searchData.took_ms}ms
          </span>
          {isFetching && !isLoading && (
            <Loader2 className="h-3 w-3 animate-spin ml-1" />
          )}
        </div>
      )}

      {/* Error state */}
      {isError && (
        <div className="rounded-xl bg-destructive/10 p-4 border border-destructive/20">
          <p className="text-sm text-destructive">
            Search failed: {(error as Error)?.message || 'Unknown error'}
          </p>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty state — no query */}
      {!isLoading && !searchData && !query.trim() && (
        <div className="rounded-xl bg-card p-12 shadow-sm border border-border text-center">
          <Search className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-foreground">Search across your research</h3>
          <p className="text-muted-foreground mt-1 max-w-md mx-auto">
            Type a query above to search across experiments, notebooks, papers, datasets, and more.
            Uses hybrid search combining semantic similarity with keyword matching.
          </p>
        </div>
      )}

      {/* Empty state — no results */}
      {!isLoading && searchData && searchData.results.length === 0 && query.trim() && (
        <div className="rounded-xl bg-card p-12 shadow-sm border border-border text-center">
          <Search className="h-12 w-12 text-muted-foreground/40 mx-auto mb-3" />
          <h3 className="text-lg font-medium text-foreground">No results found</h3>
          <p className="text-muted-foreground mt-1">
            No results for &ldquo;{query}&rdquo;. Try a different search term or adjust your filters.
          </p>
        </div>
      )}

      {/* Results list */}
      {searchData && searchData.results.length > 0 && (
        <>
          <div className="space-y-3">
            {searchData.results.map((result) => (
              <SearchResultCard key={result.id} result={result} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setOffset((prev) => Math.max(0, prev - limit))}
                disabled={offset === 0}
              >
                Previous
              </Button>
              <span className="text-sm text-muted-foreground px-3">
                Page {currentPage} of {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setOffset((prev) => prev + limit)}
                disabled={offset + limit >= searchData.total}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
