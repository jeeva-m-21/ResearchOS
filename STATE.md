# STATE.md

## Current Sprint: Premium UI — Dark Mode + Ambient Background + Landing Page

**Goal**: Add dark mode toggle, animated 3D fluid backgrounds, and a Vercel-grade landing page.

### Plan
1. Install `next-themes` + create ThemeProvider/ThemeToggle — DONE
2. Create aurora gradient background (parallax + mouse tracking) — DONE
3. Create floating orbs background (framer-motion animated blobs) — DONE
4. Add 3D tilt card effects (mouse tracking + spring physics) — DONE
5. Update globals.css with smooth theme transitions + new keyframes — DONE
6. Rewrite landing page with premium hero section — DONE

### In Progress
- (none)

### Done
- Installed `next-themes` for persistent dark/light mode
- Created `components/theme-toggle.tsx` — animated sun/moon toggle with framer-motion rotation
- Created `components/background/aurora-background.tsx` — 3-layer CSS aurora with mouse parallax tracking, variant color themes (blue/purple/green/neutral), configurable speed and opacity
- Created `components/background/floating-orbs.tsx` — animated blurred gradient orbs with random drift, size/color/duration, mixed color variants
- Created `hooks/use-mouse-position.ts` — RAF-throttled viewport mouse tracker + element-relative tracker with normalized center coordinates (-1 to 1)
- Created `components/ui/tilt-card.tsx` — 3D tilt on hover using framer-motion springs, configurable tilt degree/perspective/scale, optional glare spotlight
- Updated `globals.css`:
  - Added smooth theme transitions on `*` (background, border, color, box-shadow 0.3s)
  - Excluded animation classes from theme transition to prevent jank
  - Added `@keyframes auroraDrift`, `gradientRotate`, `float`, `glowPulse`
  - Added `.animate-float`, `.animate-glow-pulse` utility classes
- Updated `lib/providers.tsx` to wrap with `<ThemeProvider>` (attribute="class", defaultTheme="system")
- Updated `app/layout.tsx`:
  - Added `suppressHydrationWarning` on `<html>` (required by next-themes)
  - Added `AuroraBackground` (blue variant, speed 0.8, opacity 0.35) — always active
  - Added `FloatingOrbs` (5 orbs, mixed variant) — always active
- Rewrote `app/page.tsx` (landing page):
  - Premium nav bar with `ThemeToggle` + sign in/get started links
  - Hero section: badge ("Where AI research meets velocity"), gradient title (`.text-gradient-primary`), animated subtitle, dual CTAs with shadow effects
  - Stats bar (10K+ experiments, 500+ researchers, 40K+ hours saved)
  - Feature cards with `TiltCard` 3D hover, gradient hover borders, staggered `framer-motion` entrance
  - Bottom CTA card with `bg-grid` overlay
  - Footer with copyright and links

### Files Created
- `components/theme-toggle.tsx`
- `components/background/aurora-background.tsx`
- `components/background/floating-orbs.tsx`
- `hooks/use-mouse-position.ts`
- `components/ui/tilt-card.tsx`

### Files Modified
- `lib/providers.tsx` — added ThemeProvider wrapping
- `app/layout.tsx` — added background components + suppressHydrationWarning
- `app/globals.css` — added theme transitions, 4 new keyframes, animate-float, animate-glow-pulse
- `app/page.tsx` — complete rewrite with premium design

### Verification
- All 6 pages return 200 (/, /login, /signup, /dashboard, /dashboard/experiments, /dashboard/experiments/new)
- CSS contains all new keyframes and utility classes
- No compilation errors

### Next Steps
- Add `ThemeToggle` to dashboard shell (sidebar/topbar)
- Polish page transitions with `AnimatePresence` (route change animations)
- Apply TiltCard to experiment cards in dashboard

### Blocked
- (none)
