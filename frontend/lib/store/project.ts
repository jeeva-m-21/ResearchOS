import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { type Project, fetchProjects } from '@/lib/api/projects'

interface ProjectState {
  /** All projects the user has access to */
  projects: Project[]
  /** Currently selected project ID */
  currentProjectId: string | null
  /** Whether projects are being loaded */
  isLoading: boolean
  /** Error message if loading failed */
  error: string | null

  /** Load projects from the API */
  loadProjects: () => Promise<void>
  /** Switch the active project */
  setCurrentProject: (projectId: string) => void
  /** Get the current project object */
  getCurrentProject: () => Project | null
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set, get) => ({
      projects: [],
      currentProjectId: null,
      isLoading: false,
      error: null,

      loadProjects: async () => {
        const { currentProjectId } = get()
        set({ isLoading: true, error: null })
        try {
          const projects = await fetchProjects()
          // If we have no current project set, default to the first one
          const firstProjectId = projects[0]?.id ?? null
          set({
            projects,
            currentProjectId: currentProjectId ?? firstProjectId,
            isLoading: false,
          })
        } catch (err: unknown) {
          const message =
            err instanceof Error ? err.message : 'Failed to load projects'
          set({ error: message, isLoading: false })
        }
      },

      setCurrentProject: (projectId: string) => {
        set({ currentProjectId: projectId })
      },

      getCurrentProject: () => {
        const { projects, currentProjectId } = get()
        if (!currentProjectId) return null
        return projects.find((p) => p.id === currentProjectId) ?? null
      },
    }),
    {
      name: 'researchos-project-store',
      partialize: (state) => ({ currentProjectId: state.currentProjectId }),
    },
  ),
)
