'use client'

import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/lib/store/auth'
import api from '@/lib/api/client'
import Link from 'next/link'
import {
  FlaskConical,
  BookOpen,
  FileText,
  Loader2,
  Plus,
  ArrowRight,
  Activity,
  GitCommit,
  TrendingUp,
  Clock,
  Sparkles,
  Play,
  CheckCircle2,
  XCircle,
  AlertCircle,
  BarChart3,
  Users,
  Zap,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

// ---------- helpers ----------

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d ago`
  return new Date(dateStr).toLocaleDateString()
}

// ---------- data fetching ----------

async function fetchExperimentsCount(): Promise<number> {
  try {
    const res = await api.get('/v1/experiments/')
    return Array.isArray(res.data) ? res.data.length : 0
  } catch { return 0 }
}

async function fetchNotebooksCount(): Promise<number> {
  try {
    const res = await api.get('/v1/notebooks/')
    return Array.isArray(res.data) ? res.data.length : 0
  } catch { return 0 }
}

// ---------- mini components ----------

function StatCard({
  title,
  value,
  icon: Icon,
  href,
  trend,
  subtitle,
}: {
  title: string
  value: number | string
  icon: React.ElementType
  href: string
  trend?: string
  subtitle?: string
}) {
  return (
    <Link href={href}>
      <div className="group rounded-xl bg-card p-5 shadow-sm border border-border hover:shadow-md hover:border-primary/20 transition-all duration-200">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{title}</p>
            <p className="text-3xl font-bold tracking-tight text-foreground">{value}</p>
            {(trend || subtitle) && (
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                {trend && <TrendingUp className="h-3 w-3 text-emerald-500" />}
                {trend || subtitle}
              </p>
            )}
          </div>
          <div className="rounded-xl bg-primary/5 p-3 group-hover:bg-primary/10 transition-colors">
            <Icon className="h-5 w-5 text-primary" />
          </div>
        </div>
      </div>
    </Link>
  )
}

function ActivityFeed() {
  // For MVP, show static recent activity based on what we know
  // In production, this would come from the events API
  const activities = [
    {
      icon: Play,
      iconBg: 'bg-blue-100 dark:bg-blue-900/30',
      iconColor: 'text-blue-600 dark:text-blue-400',
      text: 'Started tracking experiments with ResearchOS',
      time: '2 days ago',
    },
    {
      icon: BookOpen,
      iconBg: 'bg-indigo-100 dark:bg-indigo-900/30',
      iconColor: 'text-indigo-600 dark:text-indigo-400',
      text: 'Created your first notebook',
      time: '2 days ago',
    },
  ]

  return (
    <div className="rounded-xl bg-card p-5 shadow-sm border border-border">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Activity className="h-4 w-4 text-muted-foreground" />
          Recent Activity
        </h2>
        <span className="text-xs text-muted-foreground">Live</span>
      </div>
      <div className="space-y-3">
        {activities.map((a, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className={`rounded-lg p-2 ${a.iconBg}`}>
              <a.icon className={`h-3.5 w-3.5 ${a.iconColor}`} />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-foreground">{a.text}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{a.time}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function QuickActions() {
  return (
    <div className="rounded-xl bg-card p-5 shadow-sm border border-border">
      <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
        <Zap className="h-4 w-4 text-muted-foreground" />
        Quick Actions
      </h2>
      <div className="grid grid-cols-2 gap-3">
        <Link
          href="/dashboard/experiments"
          className="flex flex-col items-center justify-center rounded-xl border border-border bg-background p-4 hover:border-primary/30 hover:bg-primary/5 transition-all group"
        >
          <FlaskConical className="h-5 w-5 text-primary mb-2" />
          <span className="text-sm font-medium text-foreground">New Experiment</span>
          <span className="text-xs text-muted-foreground mt-0.5">Track runs & metrics</span>
        </Link>
        <Link
          href="/dashboard/notebooks"
          className="flex flex-col items-center justify-center rounded-xl border border-border bg-background p-4 hover:border-primary/30 hover:bg-primary/5 transition-all group"
        >
          <BookOpen className="h-5 w-5 text-indigo-500 mb-2" />
          <span className="text-sm font-medium text-foreground">New Notebook</span>
          <span className="text-xs text-muted-foreground mt-0.5">Document research</span>
        </Link>
      </div>
    </div>
  )
}

function RunningExperiments() {
  // In production, this would query for experiments with status="running"
  return (
    <div className="rounded-xl bg-card p-5 shadow-sm border border-border">
      <h2 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
        <Activity className="h-4 w-4 text-emerald-500" />
        Running Now
      </h2>
      <div className="rounded-lg border border-border bg-muted/30 p-6 text-center">
        <Play className="h-8 w-8 text-muted-foreground/30 mx-auto mb-2" />
        <p className="text-sm text-muted-foreground">No experiments running</p>
        <p className="text-xs text-muted-foreground/60 mt-1">
          Start a run from any experiment to see it here in real-time.
        </p>
        <Link
          href="/dashboard/experiments"
          className="inline-flex items-center gap-1 mt-3 text-xs font-medium text-primary hover:text-primary/80 transition-colors"
        >
          View experiments <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  )
}

function ResearchTips() {
  const tips = [
    {
      icon: FlaskConical,
      text: 'Use experiment runs to track different hyperparameter configurations',
    },
    {
      icon: BookOpen,
      text: 'Create notebooks to document your research process with executable blocks',
    },
    {
      icon: BarChart3,
      text: 'Log metrics to visualize training progress and compare runs',
    },
  ]

  return (
    <div className="rounded-xl bg-gradient-to-br from-primary/5 to-primary/0 p-5 shadow-sm border border-primary/10">
      <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
        <Sparkles className="h-4 w-4 text-primary" />
        Research Tips
      </h2>
      <div className="space-y-3">
        {tips.map((tip, i) => (
          <div key={i} className="flex items-start gap-3">
            <div className="rounded-lg bg-primary/10 p-1.5 mt-0.5">
              <tip.icon className="h-3.5 w-3.5 text-primary" />
            </div>
            <p className="text-sm text-muted-foreground leading-relaxed">{tip.text}</p>
          </div>
        ))}
      </div>
    </div>
  )
}

function ResearchHubHeader() {
  const { user } = useAuthStore()
  const hour = new Date().getHours()
  let greeting = 'Good evening'
  if (hour < 12) greeting = 'Good morning'
  else if (hour < 17) greeting = 'Good afternoon'

  return (
    <div>
      <div className="flex items-center gap-3">
        <div className="rounded-xl bg-primary/10 p-2.5">
          <Sparkles className="h-5 w-5 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">
            {greeting}{user?.name ? `, ${user.name.split(' ')[0]}` : ''}
          </h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Your research command center
          </p>
        </div>
      </div>
    </div>
  )
}

// ---------- page ----------

export default function DashboardHome() {
  const { user, organizations } = useAuthStore()

  const { data: experimentsCount, isLoading: loadingExperiments } = useQuery({
    queryKey: ['experiments-count'],
    queryFn: fetchExperimentsCount,
    retry: 1,
    staleTime: 30000,
  })

  const { data: notebooksCount, isLoading: loadingNotebooks } = useQuery({
    queryKey: ['notebooks-count'],
    queryFn: fetchNotebooksCount,
    retry: 1,
    staleTime: 30000,
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <ResearchHubHeader />

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          title="Experiments"
          value={loadingExperiments ? '...' : (experimentsCount ?? 0)}
          icon={FlaskConical}
          href="/dashboard/experiments"
          subtitle="Track and compare"
        />
        <StatCard
          title="Notebooks"
          value={loadingNotebooks ? '...' : (notebooksCount ?? 0)}
          icon={BookOpen}
          href="/dashboard/notebooks"
          subtitle="Document research"
        />
        <StatCard
          title="Papers"
          value={0}
          icon={FileText}
          href="/dashboard/papers"
          subtitle="Coming soon"
        />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Left column — activity + status */}
        <div className="md:col-span-2 space-y-4">
          <RunningExperiments />
          <ActivityFeed />
        </div>

        {/* Right column — quick actions + tips */}
        <div className="space-y-4">
          <QuickActions />

          {organizations.length > 0 && (
            <div className="rounded-xl bg-card p-5 shadow-sm border border-border">
              <h2 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                Organization
              </h2>
              {organizations.map((org) => (
                <div key={org.organization_id} className="flex items-center justify-between py-2">
                  <div>
                    <p className="text-sm font-medium text-foreground">{org.organization_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {org.organization_slug} &middot; {org.role}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}

          <ResearchTips />
        </div>
      </div>
    </div>
  )
}
