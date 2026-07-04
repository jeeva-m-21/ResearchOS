'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAuthStore } from '@/lib/store/auth'
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
  LayoutDashboard,
  FlaskConical,
  BookOpen,
  Search,
  FileText,
  Menu,
  ChevronDown,
  LogOut,
  Building2,
} from 'lucide-react'

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/experiments', label: 'Experiments', icon: FlaskConical },
  { href: '/dashboard/notebooks', label: 'Notebooks', icon: BookOpen },
  { href: '/dashboard/papers', label: 'Papers', icon: FileText },
  { href: '/dashboard/search', label: 'Search', icon: Search },
]

const pageTitles: Record<string, string> = {
  '/dashboard': 'Dashboard',
  '/dashboard/experiments': 'Experiments',
  '/dashboard/notebooks': 'Notebooks',
  '/dashboard/papers': 'Papers',
  '/dashboard/search': 'Search',
}

function getPageTitle(pathname: string): string {
  // Exact match first
  if (pageTitles[pathname]) return pageTitles[pathname]
  // Prefix match (e.g. /dashboard/experiments/123)
  const prefix = '/' + pathname.split('/').slice(1, 3).join('/')
  if (pageTitles[prefix]) return pageTitles[prefix]
  return 'Dashboard'
}

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
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <Icon className="h-4 w-4" />
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
        <Button variant="ghost" className="relative h-9 w-9 rounded-full">
          <Avatar className="h-9 w-9">
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

function SidebarContent({ onNavClick }: { onNavClick?: () => void }) {
  return (
    <div className="flex h-full flex-col">
      {/* Logo + Org */}
      <div className="p-4 border-b">
        <Link href="/dashboard" className="text-lg font-bold" onClick={onNavClick}>
          ResearchOS
        </Link>
        <div className="mt-2">
          <OrgSwitcher />
        </div>
      </div>

      {/* Nav links */}
      <div className="flex-1 p-3">
        <NavLinks onNavClick={onNavClick} />
      </div>

      {/* User */}
      <div className="p-3">
        <UserSection onNavClick={onNavClick} />
      </div>
    </div>
  )
}

function DashboardShell({ children }: { children: React.ReactNode }) {
  const [sheetOpen, setSheetOpen] = useState(false)
  const pathname = usePathname()
  const pageTitle = getPageTitle(pathname)

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
        {/* Topbar */}
        <header className="sticky top-0 z-20 bg-background border-b">
          <div className="flex items-center justify-between px-4 md:px-6 h-14">
            <div className="flex items-center gap-3">
              {/* Mobile spacer for hamburger */}
              <div className="md:hidden w-9" />
              <h1 className="text-lg font-semibold">{pageTitle}</h1>
            </div>
            <div className="flex items-center gap-2">
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
