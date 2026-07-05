import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { type Project, createProject as apiCreateProject, fetchProjects } from '@/lib/api/projects'

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
  /** Create a new project and switch to it */
  createAndSelectProject: (name: string, description?: string) => Promise<Project>
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

      createAndSelectProject: async (name: string, description?: string) => {
        const result = await apiCreateProject(name, description)
        // Reload projects to get the full list with the new project
        const projects = await fetchProjects()
        const newProject = projects.find((p) => p.id === result.id) ?? {
          id: result.id,
          name: result.name,
          description: result.description,
          visibility: 'private',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        set({ projects, currentProjectId: newProject.id })
        return newProject
      },
    }),
    {
      name: 'researchos-project-store',
      partialize: (state) => ({ currentProjectId: state.currentProjectId }),
    },
  ),
)
