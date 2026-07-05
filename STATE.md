# STATE.md

## Current Sprint: Project-Level Context + Kaggle-Inspired Topbar

**Goal**: Make "project" the main organizational level and add a Colab/Kaggle-inspired topbar with project selector, quick-create, and search.

### Plan
1. Add `GET /v1/projects/` backend endpoint — DONE
2. Create `lib/api/projects.ts` + `lib/store/project.ts` — DONE
3. Redesign topbar with project selector + quick-create + theme toggle + search — DONE
4. Wire project context into experiments/notebooks API (remove hardcoded project_id) — DONE
5. Run tsc + build + verify — DONE

### In Progress
- (none)

### Done

#### Backend
- `backend/src/api/routes/projects.py`: `GET /v1/projects/` lists projects for current org; `GET /v1/projects/{id}` gets a single project
- Registered `/v1/projects` router in `main.py`

#### Frontend
- `lib/api/projects.ts`: `Project` type + `fetchProjects()` / `fetchProject()` API calls
- `lib/store/project.ts`: Zustand store with `zustand/middleware/persist` — loads projects on auth, defaults to first project, persists `currentProjectId` in localStorage
- `lib/api/experiments.ts`: Removed `TEST_PROJECT_ID` constant, uses `useProjectStore.getState().currentProjectId` via `getProjectId()` helper
- `lib/api/notebooks.ts`: Same pattern — dynamic project_id from store

#### Topbar Redesign (`app/dashboard/layout.tsx`)
- **ProjectSelector**: Dropdown in the top-left showing all user projects; switch context with one click
- **QuickCreate**: "+ New" button with dropdown for "New Experiment" / "New Notebook"
- **TopSearch**: Search bar moved from sidebar to topbar with Cmd+K hotkey; elegant focus ring + hover states
- **ThemeToggle**: Integrated from existing `components/theme-toggle.tsx` — resized to 32x32 to match topbar
- **UserMenu**: Compact 32x32 avatar dropdown
- **Layout**: Sticky topbar with `backdrop-blur-sm` for glassmorphism effect; responsive (mobile hamburger preserved)

### Next Steps
- Add project creation UI (dialog)
- Add project detail page (dashboard scoped to project)
- Add "all projects" view in dashboard
