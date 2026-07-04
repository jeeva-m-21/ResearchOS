# ResearchOS UI Design System

## Overview

ResearchOS is a research operating system for AI/ML researchers. The UI must feel **scientific, precise, and premium** — like Vercel meets a research lab. Every pixel communicates rigor, clarity, and speed.

---

## Design Philosophy

### Core Principles

1. **Scientific Precision** — Clean lines, generous whitespace, restrained color. The interface disappears, letting data and code speak.

2. **Vercel/Geist DNA** — Minimal aesthetic, high contrast, geometric shapes, subtle shadows, sharp typography. Dark and light themes with equal care.

3. **Motion with Purpose** — Every animation explains a transition; nothing moves purely for decoration. Page transitions, sidebar collapses, modal entrances all use `cubic-bezier(0.16, 1, 0.3, 1)`.

4. **Developer-First** — Dense information density when needed (data tables, metric charts), but spacious when composing (notebooks, papers). Keyboard shortcuts everywhere.

5. **Consistent Rhythm** — 4px base unit. 8px inside groups, 16px between groups, 32px between sections. Every component snaps to the grid.

---

## Color System

### Light Theme

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-primary` | `#ffffff` | Page background |
| `--bg-secondary` | `#fafafa` | Sidebar, card alt |
| `--bg-tertiary` | `#f5f5f5` | Hover states, code blocks |
| `--border` | `#e5e5e5` | Default borders, dividers |
| `--border-strong` | `#d4d4d4` | Active borders, focus |
| `--text-primary` | `#171717` | Headings, primary content |
| `--text-secondary` | `#737373` | Body text, meta |
| `--text-tertiary` | `#a3a3a3` | Placeholder, disabled |
| `--accent-blue` | `#0066ff` | Links, active nav, primary CTAs |
| `--accent-green` | `#059669` | Success, active experiments |
| `--accent-red` | `#dc2626` | Errors, failures |
| `--accent-amber` | `#d97706` | Warnings, paused |
| `--accent-purple` | `#7c3aed` | AI features, notebooks |

### Dark Theme

| Token | Value |
|-------|-------|
| `--bg-primary` | `#0a0a0a` |
| `--bg-secondary` | `#111111` |
| `--bg-tertiary` | `#1a1a1a` |
| `--border` | `#1f1f1f` |
| `--border-strong` | `#2a2a2a` |
| `--text-primary` | `#fafafa` |
| `--text-secondary` | `#a3a3a3` |
| `--text-tertiary` | `#525252` |

### Semantic Colors

| State | Color | Icon + Text |
|-------|-------|-------------|
| Running | `--accent-green` | Play circle + "Running" |
| Paused | `--accent-amber` | Pause circle + "Paused" |
| Failed | `--accent-red` | X circle + "Failed" |
| Completed | `--accent-blue` | Check circle + "Completed" |
| AI-Powered | `--accent-purple` | Sparkles icon |

---

## Typography

### Font Stack

```css
--font-sans: 'Geist', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
--font-mono: 'Geist Mono', 'Fira Code', 'JetBrains Mono', monospace;
```

### Type Scale (headings)

| Token | Size | Weight | Line Height | Tracking | Usage |
|-------|------|--------|-------------|----------|-------|
| `text-hero` | 72px | 600 | 0.95 | -2% | Landing hero only |
| `text-display` | 48px | 600 | 1.1 | -1.5% | Page titles |
| `text-h1` | 32px | 600 | 1.2 | -1% | Section headers |
| `text-h2` | 24px | 600 | 1.3 | -0.5% | Card titles |
| `text-h3` | 20px | 600 | 1.4 | 0 | Subsection titles |
| `text-base` | 14px | 400 | 1.5 | 0 | Body text |
| `text-sm` | 13px | 400 | 1.4 | 0 | Meta, labels |
| `text-xs` | 12px | 400 | 1.3 | 0 | Captions, timestamps |
| `text-code` | 13px | 400 | 1.5 | 0 | Inline code |

### Font Weights

- 400: Body, labels, meta
- 500: Buttons, active nav items
- 600: Headings, card titles

---

## Spacing System

### Base Unit: 4px

```
space-1:  4px    (micro)
space-2:  8px    (tight group)
space-3:  12px   (input padding)
space-4:  16px   (standard)
space-5:  20px   (section gap)
space-6:  24px   (card padding)
space-8:  32px   (between sections)
space-10: 40px   (page padding)
space-16: 64px   (hero spacing)
```

### Layout Principles

- Max content width: 1200px (centered)
- Sidebar width: 240px (collapsed: 56px)
- Cards: 24px padding, 16px when tight
- Data tables: 12px cell padding

---

## Animation System

### Motion Tokens

```css
--ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
--ease-in-out: cubic-bezier(0.76, 0, 0.24, 1);
--duration-fast: 150ms;
--duration-normal: 200ms;
--duration-slow: 300ms;
```

### When to Animate

| Element | Duration | Easing | Trigger |
|---------|----------|--------|---------|
| Page transitions | 300ms | ease-out-expo | Route change |
| Sidebar expand/collapse | 200ms | ease-out-expo | Toggle |
| Modal/dialog | 200ms | ease-out-expo | Open/close |
| Dropdown menu | 150ms | ease-out-expo | Hover/click |
| Hover state | 100ms | ease-out-expo | :hover |
| Skeleton loader | pulse 1.5s | linear | Data loading |
| Notification toast | 300ms + 3s | ease-out-expo | + auto-dismiss |
| Progress bar | 500ms | ease-in-out | Upload/execute |

### Implementation

Use **`tailwindcss-animate`** for CSS-based animations and **`framer-motion`** for complex orchestrated transitions (page transitions, staggered list items, shared layout animations).

---

## Component Design Patterns

### Cards (Geist-Inspired)

```tsx
<div className="rounded-lg border bg-card p-6 shadow-sm">
  {/* card content */}
</div>
```

- Border: `1px solid var(--border)`
- Radius: `8px` (lg: `12px`, sm: `6px`)
- Shadow: `0 1px 2px rgba(0,0,0,0.04)`
- Hover: `shadow-md, border-strong`

### Data Tables

```tsx
<table className="w-full text-sm">
  <thead>
    <tr className="border-b text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
      <th className="py-3 px-4">Name</th>
    </tr>
  </thead>
  <tbody>
    <tr className="border-b last:border-0 hover:bg-accent/50 transition-colors">
      <td className="py-3 px-4">Value</td>
    </tr>
  </tbody>
</table>
```

### Status Badges

```tsx
<span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium
  bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-400">
  <span className="h-1.5 w-1.5 rounded-full bg-current" />
  Running
</span>
```

The dot indicates state without needing color-only communication.

### Buttons (Geist-Variant)

| Variant | Style |
|---------|-------|
| Primary | `bg-foreground text-background` |
| Secondary | `bg-background border text-foreground` |
| Ghost | `text-foreground hover:bg-accent` |
| Destructive | `bg-red-600 text-white` |
| Icon | `h-9 w-9 p-0` |

### Forms

- Label above input (not placeholder-only)
- Input: 40px height, 12px padding, 6px radius
- Focus ring: `ring-2 ring-blue-600 ring-offset-2 ring-offset-background`
- Error state: red border + error text below
- Helper text: 12px, muted, below input

### Navigation

- Sidebar: 240px width, with section labels, collapsed variant with icons only
- Active state: subtle blue background tint + blue text
- Section dividers: 1px border with subtle label
- Topbar: 56px height, breadcrumbs, global search, user menu

---

## Page-by-Page Redesign

### 1. Landing Page (`/`)

**Vibe**: Clean, scientific, with animated geometric background

- Full-viewport hero with centered content
- Gradient accent on the word "ResearchOS" (blue → purple)
- Subtle grid/particle background (CSS-only, no canvas)
- Animated feature cards that stagger in on scroll
- Floating "cytoscape" graph visualization as background decoration
- CTA buttons: "Start Researching" (primary) + "View Docs" (ghost)
- Footer with minimal links

### 2. Auth (`/login`, `/signup`)

**Vibe**: Centered card, minimal, Geist-like

- Full-viewport centered card (max-w-sm)
- No sidebar, no nav
- Logo + tagline at top
- Clean form with floating labels (not placeholder)
- Social auth buttons (Google, GitHub — gray border, icons)
- Divider with "or continue with"
- Bottom link to toggle login/signup
- Error messages inline below inputs
- Loading state: button shows spinner, disabled

### 3. Dashboard (`/dashboard`)

**Vibe**: Metrics overview, command-center

- **Stats Row**: 4 cards in a row — Active Experiments, Total Runs, Notebooks, Papers
  - Each card: large number, small label, subtle icon top-right
  - Animated counter on load
- **Recent Activity**: Timeline list of recent events (experiments started, metrics logged)
  - Each item: icon + text + "3 min ago"
  - Time-grouped (Today, Yesterday, This Week)
- **Quick Actions**: "New Experiment", "New Notebook", "Ask AI" buttons
- **What's Next**: AI-generated suggestions for next research steps

### 4. Experiments (`/dashboard/experiments`)

**Vibe**: Data-heavy, precise, filterable

- **List View** (default):
  - Sortable table: Name, Status, Runs, Last Run, Tags, Created
  - Row hover: subtle bg change, action buttons appear
  - Status: colored dot + label
  - Empty state: "No experiments yet. Start your first one."
- **Grid View** (toggle):
  - Cards with status badge, metric preview
  - Compact, dense
- **Filters**: Status dropdown, date range, tag search
- **Create Dialog**: Modal with name, description, tags, params
  - Clean form, Geist-aligned inputs
  - Tags: autocomplete from existing tags
- **Detail Page** (`/dashboard/experiments/[id]`):
  - Header: name, status badge, edit button
  - Tab layout: Overview | Runs | Metrics | Artifacts
  - Overview: description, params table, hypothesis link
  - Runs: list with status, duration, metrics summary
  - Metrics: Recharts area chart, multi-series, zoomable
  - Real-time update via polling

### 5. Notebooks (`/dashboard/notebooks`)

**Vibe**: Code editor meets Notion

- **List View**: Cards with block type count, last edited, branch indicator
- **Editor** (`/dashboard/notebooks/[id]`):
  - Block-based layout with drag handles (TipTap)
  - Block types: Markdown, Code (Python/Rust/SQL), Mermaid, LaTeX
  - Code blocks: monospace, syntax highlighting, line numbers
  - Run button per code block + inline output below
  - Top bar: branch selector, commit message, run all
  - Minimap on the right (scroll position indicator)
  - Command palette (Cmd+K): "Add markdown block", "Run all", "Add python block"

### 6. Papers (`/dashboard/papers`)

**Vibe**: Academic, typography-forward

- **List View**: Cards with title, author, status, citations count
- **Editor** (`/dashboard/papers/[id]`):
  - Section-based layout (blocks)
  - Citation manager sidebar
  - Export buttons: PDF, LaTeX, Markdown
  - AI assistant panel: "Write abstract", "Suggest citations"

### 7. Search (`/dashboard/search`)

**Vibe**: Spotlight/Alfred-like

- **Search Bar**: Full-width, large, auto-focused on navigation
- **Results**: Grouped by type (Experiments, Notebooks, Papers, etc.)
- **Filters**: Type chips below search bar
- **Keyboard Navigation**: Up/down arrows, Enter to select
- **Empty State**: "No results found. Try a different query."
- **Highlighting**: Matched terms in bold/yellow
- **Recent Searches**: Below search bar, clearable

### 8. AI Assistant

**Vibe**: ChatGPT meets IDE

- **Panel** (slide from right or full page):
  - Chat interface with message bubbles
  - User messages: right-aligned, blue bg
  - AI messages: left-aligned, card style with agent icon
  - Tool calls: expandable, shows "Searching experiments..." etc.
  - Suggested prompts: chips below input
  - Input: multi-line, with Send button, Cmd+Enter shortcut
  - Context pills above input: "Analyzing: experiment X"

---

## Empty States

Every list page has a deliberate empty state:

```tsx
<div className="flex flex-col items-center justify-center py-16">
  <div className="rounded-full bg-accent p-4 mb-4">
    <Icon className="h-8 w-8 text-muted-foreground" />
  </div>
  <h3 className="text-lg font-semibold">No experiments yet</h3>
  <p className="text-sm text-muted-foreground mt-1 mb-4">
    Create your first experiment to start tracking ML runs.
  </p>
  <Button>Create Experiment</Button>
</div>
```

---

## Loading States

- **Skeleton cards**: Gray pulsing rectangles matching card shape
- **Skeleton table**: Pulsing rows (5 rows, matching columns)
- **Spinner**: Custom SVG spinner, 20px, with rotation animation
- **Page skeleton**: Full-page skeleton with header + content area pulses
- **Button loading**: Inline spinner icon, disabled, shows "Saving…"

---

## Responsive Behavior

| Breakpoint | Layout |
|------------|--------|
| > 1200px | Full sidebar + content |
| 768-1200px | Collapsed sidebar (icons only) |
| < 768px | Bottom nav, sheet sidebar |

---

## Implementation Roadmap

### Phase 1: Foundation
1. Install Geist fonts + framer-motion
2. Rebuild globals.css with design tokens
3. Create animation utility components (motion-variants.ts, AnimatedContainer)
4. Create shared layout components (PageHeader, DataTable, StatusBadge, EmptyState, Skeleton)

### Phase 2: Shell
5. Redesign landing page
6. Redesign login/signup
7. Redesign dashboard shell (sidebar, topbar, user menu)

### Phase 3: Feature Pages
8. Experiments CRUD with premium UI
9. Notebooks list + editor
10. Papers list + editor
11. Search UI
12. AI Assistant panel

### Phase 4: Polish
13. Dark mode
14. Page transitions (framer-motion AnimatePresence)
15. Keyboard shortcuts
16. Responsive adjustments
