'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAuthStore } from '@/lib/store/auth'
import { useProjectStore } from '@/lib/store/project'
import { ThemeToggle } from '@/components/theme-toggle'
import { CreateProjectDialog } from '@/components/projects/CreateProjectDialog'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import { Separator } from '@/components/ui/separator'
import {
  MessageSquare,
  BarChart3,
  FlaskConical,
  BookOpen,
  Search,
  FileText,
  Menu,
  ChevronDown,
  LogOut,
  Building2,
  Plus,
  Beaker,
  NotebookIcon,
  Command,
  Settings,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Home', icon: MessageSquare },
  { href: '/dashboard/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/dashboard/experiments', label: 'Experiments', icon: FlaskConical },
  { href: '/dashboard/notebooks', label: 'Notebooks', icon: BookOpen },
  { href: '/dashboard/papers', label: 'Papers', icon: FileText },
  { href: '/dashboard/search', label: 'Search', icon: Search },
  { href: '/dashboard/settings', label: 'Settings', icon: Settings },
]

function NavLinks({ className, onNavClick }: { className?: string; onNavClick?: () => void }) {
  const pathname = usePathname()

  return (
    <nav className={cn('space-y-1', className)}>
      {navItems.map((item) => {
        const Icon = item.icon
        const isActive = item.href === '/dashboard'
          ? pathname === '/dashboard'
          : pathname === item.href || pathname.startsWith(item.href + '/')
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onNavClick}
            className={cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all relative',
              isActive
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            {isActive && (
              <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-full bg-primary" />
            )}
            <Icon className={cn('h-4 w-4', isActive ? 'text-primary' : '')} />
            {item.label}
          </Link>
        )
      })}
    </nav>
  )
}

function UserSection({ onNavClick }: { onNavClick?: () => void }) {
  const { user, logout } = useAuthStore()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  const initials = user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'

  return (
    <div className="space-y-2">
      <Separator />
      <div className="flex items-center gap-3 px-3 py-2">
        <Avatar className="h-8 w-8">
          <AvatarFallback className="bg-primary text-primary-foreground text-xs">
            {initials}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{user?.name || user?.email}</p>
          <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
        </div>
      </div>
      <button
        onClick={handleLogout}
        className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
      >
        <LogOut className="h-4 w-4" />
        Sign out
      </button>
    </div>
  )
}

function OrgSwitcher() {
  const { organizations } = useAuthStore()
  const currentOrg = organizations[0]

  if (!currentOrg) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="w-full justify-between px-2 h-auto py-1.5">
          <div className="flex items-center gap-2 min-w-0">
            <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
            <span className="text-sm font-medium truncate">
              {currentOrg.organization_name}
            </span>
          </div>
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {organizations.map((org) => (
          <DropdownMenuItem key={org.organization_id} className="flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            <div className="flex flex-col">
              <span>{org.organization_name}</span>
              <span className="text-xs text-muted-foreground">{org.role}</span>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// ─── Project Selector ───────────────────────────────────────────────────────

function ProjectSelector() {
  const { projects, currentProjectId, setCurrentProject } = useProjectStore()
  const currentProject = projects.find((p) => p.id === currentProjectId)

  if (!currentProject) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="flex items-center gap-1.5 px-2 h-8 text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
        >
          <Building2 className="h-3.5 w-3.5 shrink-0" />
          <span className="hidden sm:inline max-w-[120px] truncate">{currentProject.name}</span>
          <span className="sm:hidden">{currentProject.name}</span>
          <ChevronDown className="h-3 w-3 shrink-0 opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        {projects.map((project) => (
          <DropdownMenuItem
            key={project.id}
            onClick={() => setCurrentProject(project.id)}
            className={cn(
              'flex items-center gap-2',
              project.id === currentProjectId && 'bg-accent font-medium',
            )}
          >
            <Building2 className="h-4 w-4" />
            <div className="flex flex-col">
              <span>{project.name}</span>
              {project.description && (
                <span className="text-xs text-muted-foreground truncate max-w-[180px]">
                  {project.description}
                </span>
              )}
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// ─── Quick Create ────────────────────────────────────────────────────────────

function QuickCreate() {
  const router = useRouter()
  const [dialogOpen, setDialogOpen] = useState(false)

  return (
    <>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            size="sm"
            className="h-8 gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
          >
            <Plus className="h-3.5 w-3.5" />
            <span className="hidden sm:inline text-xs">New</span>
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-48">
          <DropdownMenuItem onClick={() => router.push('/dashboard/experiments')}>
            <Beaker className="mr-2 h-4 w-4" />
            New Experiment
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => router.push('/dashboard/notebooks')}>
            <NotebookIcon className="mr-2 h-4 w-4" />
            New Notebook
          </DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem onSelect={(e) => { e.preventDefault(); setDialogOpen(true) }}>
            <Building2 className="mr-2 h-4 w-4" />
            New Project
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
      <CreateProjectDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
    </>
  )
}

// ─── Top Search ──────────────────────────────────────────────────────────────

function TopSearch() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [focused, setFocused] = useState(false)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/dashboard/search?q=${encodeURIComponent(query.trim())}`)
    }
  }

  // Cmd+K / Ctrl+K hotkey
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        document.getElementById('topbar-search-input')?.focus()
      }
    },
    [],
  )

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  return (
    <form onSubmit={handleSubmit} className="relative w-full max-w-[200px] lg:max-w-[280px]">
      <div
        className={cn(
          'relative flex items-center rounded-lg border transition-all',
          focused
            ? 'border-ring ring-1 ring-ring'
            : 'border-border bg-muted/50 hover:bg-accent/50',
        )}
      >
        <Search className="absolute left-2.5 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
        <input
          id="topbar-search-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          placeholder="Search..."
          className="w-full bg-transparent py-1.5 pl-8 pr-8 text-xs outline-none placeholder:text-muted-foreground/60"
        />
        <kbd className="absolute right-2 hidden sm:inline-flex items-center gap-0.5 rounded border border-border bg-background px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
          <Command className="h-2.5 w-2.5" />
          K
        </kbd>
      </div>
    </form>
  )
}

// ─── User Menu (top-right) ───────────────────────────────────────────────────

function UserMenu() {
  const { user, logout } = useAuthStore()
  const router = useRouter()

  const handleLogout = async () => {
    await logout()
    router.push('/login')
  }

  const initials = user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || '?'

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="relative h-8 w-8 rounded-full">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-primary text-primary-foreground text-xs">
              {initials}
            </AvatarFallback>
          </Avatar>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <div className="flex items-center gap-2 px-2 py-1.5">
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-primary text-primary-foreground text-xs">
              {initials}
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-col">
            <p className="text-sm font-medium">{user?.name || 'User'}</p>
            <p className="text-xs text-muted-foreground">{user?.email}</p>
          </div>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
          <LogOut className="mr-2 h-4 w-4" />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// ─── Sidebar Content ─────────────────────────────────────────────────────────

function SidebarContent({ onNavClick }: { onNavClick?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      {/* Logo + Org */}
      <div className="p-4 border-b">
        <Link href="/dashboard" className="flex items-center gap-2 text-lg font-bold" onClick={onNavClick}>
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary shadow-sm">
            <span className="text-xs font-bold text-primary-foreground">R</span>
          </div>
          ResearchOS
        </Link>
        <div className="mt-2">
          <OrgSwitcher />
        </div>
      </div>

      {/* Nav links */}
      <div className="flex-1 p-3 pt-4">
        <NavLinks onNavClick={onNavClick} />
      </div>

      {/* User */}
      <div className="p-3">
        <UserSection onNavClick={onNavClick} />
      </div>
    </div>
  )
}

// ─── Dashboard Shell ─────────────────────────────────────────────────────────

function DashboardShell({ children }: { children: React.ReactNode }) {
  const [sheetOpen, setSheetOpen] = useState(false)
  const { loadProjects, projects } = useProjectStore()
  const { isAuthenticated } = useAuthStore()

  // Load projects when authenticated
  useEffect(() => {
    if (isAuthenticated && projects.length === 0) {
      loadProjects()
    }
  }, [isAuthenticated, projects.length, loadProjects])

  return (
    <div className="flex min-h-screen bg-muted/30">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0 bg-background border-r z-30">
        <SidebarContent />
      </aside>

      {/* Mobile sheet */}
      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="md:hidden absolute top-3 left-3 z-40">
            <Menu className="h-5 w-5" />
            <span className="sr-only">Open menu</span>
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="p-0 w-64">
          <SidebarContent onNavClick={() => setSheetOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Main content area */}
      <div className="md:pl-64 flex flex-col flex-1">
        {/* Topbar — Colab/Kaggle inspired */}
        <header className="sticky top-0 z-20 bg-background/95 backdrop-blur-sm border-b">
          <div className="flex items-center justify-between px-4 md:px-6 h-14 gap-2">
            {/* Left: project selector */}
            <div className="flex items-center gap-2 min-w-0">
              {/* Mobile spacer for hamburger */}
              <div className="md:hidden w-9" />
              <ProjectSelector />
              <span className="hidden sm:inline text-xs text-muted-foreground/50 mx-0.5">/</span>
            </div>

            {/* Right: quick-create, search, theme, user */}
            <div className="flex items-center gap-2">
              <QuickCreate />
              <TopSearch />
              <ThemeToggle className="h-8 w-8 border-0 shadow-none hover:bg-accent" />
              <UserMenu />
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 md:p-6">{children}</main>
      </div>
    </div>
  )
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <DashboardShell>{children}</DashboardShell>
    </ProtectedRoute>
  )
}
