# STATE.md

## Current Sprint: Project-Level Context + Kaggle-Inspired Topbar

**Goal**: Make "project" the main organizational level and add a Colab/Kaggle-inspired topbar with project selector, quick-create, and search.

### Plan
1. Add `GET /v1/projects/` backend endpoint — DONE
2. Create `lib/api/projects.ts` + `lib/store/project.ts` — DONE
3. Redesign topbar with project selector + quick-create + theme toggle + search — DONE
4. Wire project context into experiments/notebooks API (remove hardcoded project_id) — DONE
5. Add `POST /v1/projects/` for project creation — DONE
6. Create CreateProjectDialog component — DONE
7. Scope dashboard stats to current project — DONE
8. Run tsc + build + verify — DONE

### In Progress
- (none)

### Done

#### Backend
- `projects.py` router: `GET /v1/projects/` (list), `GET /v1/projects/{id}` (get), `POST /v1/projects/` (create)
- Registered `/v1/projects` router in `main.py`

#### Frontend Project System
- `lib/api/projects.ts`: `Project` type + `fetchProjects()` / `fetchProject()` / `createProject()` API calls
- `lib/store/project.ts`: Zustand store with `persist` middleware; auto-loads projects on auth, defaults to first project, remembers selection; includes `createAndSelectProject()` action
- `lib/api/experiments.ts`: `fetchExperiments()` now accepts optional `projectId` param; `fetchExperimentsCount()` passes it through
- `lib/api/notebooks.ts`: Same pattern — dynamic `project_id` from store

#### CreateProjectDialog (`components/projects/CreateProjectDialog.tsx`)
- Dialog with name + description fields, validation, loading/error states
- Supports both controlled (`open`/`onOpenChange`) and uncontrolled (internal state) modes
- Wired into topbar QuickCreate dropdown via "New Project" option

#### Topbar Redesign (`app/dashboard/layout.tsx`)
- **ProjectSelector**: Dropdown in top-left showing all user projects; switch context
- **QuickCreate**: `+ New` button with dropdown for "New Experiment" / "New Notebook" / "New Project"
- **TopSearch**: Cmd+K hotkey, focus ring, glassmorphism backdrop
- **ThemeToggle**: Compact 32×32
- **UserMenu**: Compact 32×32 avatar dropdown

#### Project-Scoped Dashboard
- `app/dashboard/page.tsx`: Stats cards show counts for current project; header shows project name
- `app/dashboard/experiments/page.tsx`: Experiments query scoped to current project via store
- `app/dashboard/notebooks/page.tsx`: Notebooks query scoped to current project via store

### Next Steps
- Add project detail page (dedicated view per project)
- Add "all projects" view in dashboard when multiple projects exist
- RunningNow / ActivityFeed on dashboard to show project-specific data
