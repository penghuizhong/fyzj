"use client"

import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react"
import { apiClient, UserResponse } from "@/lib/api"

interface AuthContextType {
  user: UserResponse | null
  isAuthenticated: boolean
  isLoading: boolean
  isAuthModalOpen: boolean
  authModalView: "login" | "register"
  showAuthModal: (view?: "login" | "register") => void
  hideAuthModal: () => void
  login: (username: string, password: string) => Promise<void>
  register: (username: string, password: string, email?: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)
  const [authModalView, setAuthModalView] = useState<"login" | "register">("login")

  useEffect(() => {
    const initAuth = async () => {
      const hasToken = apiClient.loadTokens()
      if (hasToken) {
        try {
          const userData = await apiClient.getMe()
          setUser(userData)
        } catch {
          apiClient.clearTokens()
        }
      }
      setIsLoading(false)
    }
    initAuth()
  }, [])

  const showAuthModal = (view: "login" | "register" = "login") => {
    setAuthModalView(view)
    setIsAuthModalOpen(true)
  }

  const hideAuthModal = () => {
    setIsAuthModalOpen(false)
  }

  const login = async (username: string, password: string) => {
    setIsLoading(true)
    try {
      await apiClient.login(username, password)
      const userData = await apiClient.getMe()
      setUser(userData)
      hideAuthModal()
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (
    username: string,
    password: string,
    email?: string
  ) => {
    setIsLoading(true)
    try {
      const userData = await apiClient.register(username, password, email)
      setUser(userData)
      hideAuthModal()
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    apiClient.clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        isAuthModalOpen,
        authModalView,
        showAuthModal,
        hideAuthModal,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
