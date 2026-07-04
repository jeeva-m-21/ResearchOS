import { create } from 'zustand'
import axios from 'axios'
import api from '../api/client'

interface User {
  id: string
  email: string
  name: string
  avatar_url: string | null
  created_at: string
}

interface Organization {
  organization_id: string
  organization_name: string
  organization_slug: string
  role: string
  joined_at: string
}

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: User | null
  organizations: Organization[]
  isLoading: boolean
  isAuthenticated: boolean

  login: (email: string, password: string, organization_id?: string) => Promise<void>
  logout: () => Promise<void>
  refreshAccessToken: () => Promise<string>
}

const authAxios = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
})

const getStoredItem = (key: string): string | null => {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(key)
}

const setStoredItem = (key: string, value: string | null) => {
  if (typeof window === 'undefined') return
  if (value === null) {
    localStorage.removeItem(key)
  } else {
    localStorage.setItem(key, value)
  }
}

export const useAuthStore = create<AuthState>()((set, get) => {
  const storedAccessToken = getStoredItem('accessToken')
  const storedRefreshToken = getStoredItem('refreshToken')

  if (storedAccessToken) {
    Promise.resolve().then(async () => {
      set({ isLoading: true })
      try {
        const [profileRes, orgsRes] = await Promise.all([
          api.get<User>('/auth/profile'),
          api.get<Organization[]>('/auth/organizations'),
        ])
        set({ user: profileRes.data, organizations: orgsRes.data, isAuthenticated: true })
      } catch {
        setStoredItem('accessToken', null)
        setStoredItem('refreshToken', null)
        set({ accessToken: null, refreshToken: null, isAuthenticated: false })
      } finally {
        set({ isLoading: false })
      }
    })
  }

  return {
    accessToken: storedAccessToken,
    refreshToken: storedRefreshToken,
    user: null,
    organizations: [],
    isLoading: !!storedAccessToken,
    isAuthenticated: !!storedAccessToken,

    login: async (email: string, password: string, organization_id?: string) => {
      set({ isLoading: true })
      try {
        const res = await authAxios.post('/auth/login', { email, password, organization_id })
        const { access_token, refresh_token } = res.data

        setStoredItem('accessToken', access_token)
        setStoredItem('refreshToken', refresh_token)

        set({ accessToken: access_token, refreshToken: refresh_token })

        const [profileRes, orgsRes] = await Promise.all([
          api.get<User>('/auth/profile'),
          api.get<Organization[]>('/auth/organizations'),
        ])

        set({
          user: profileRes.data,
          organizations: orgsRes.data,
          isAuthenticated: true,
        })
      } finally {
        set({ isLoading: false })
      }
    },

    logout: async () => {
      try {
        const { refreshToken } = get()
        if (refreshToken) {
          await authAxios.post('/auth/logout', { refresh_token: refreshToken })
        }
      } finally {
        setStoredItem('accessToken', null)
        setStoredItem('refreshToken', null)
        set({
          accessToken: null,
          refreshToken: null,
          user: null,
          organizations: [],
          isAuthenticated: false,
        })
      }
    },

    refreshAccessToken: async () => {
      const { refreshToken: storedRefreshToken } = get()
      if (!storedRefreshToken) {
        throw new Error('No refresh token available')
      }

      const res = await authAxios.post('/auth/refresh', {
        refresh_token: storedRefreshToken,
      })
      const { access_token, refresh_token } = res.data

      setStoredItem('accessToken', access_token)
      setStoredItem('refreshToken', refresh_token)

      set({ accessToken: access_token, refreshToken: refresh_token })

      return access_token
    },
  }
})
