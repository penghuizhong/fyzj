"use client"

import { SessionProvider, signOut, useSession } from "next-auth/react"
import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react"
import { apiClient, setUnauthorizedHandler } from "@/lib/api"

interface AuthContextType {
  user: any | null
  isAuthenticated: boolean
  isLoading: boolean
  isAuthModalOpen: boolean
  authModalView: "login" | "register"
  showAuthModal: (view?: "login" | "register") => void
  hideAuthModal: () => void
  login: () => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function AuthProviderContent({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession()
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)
  const [authModalView, setAuthModalView] = useState<"login" | "register">("login")

  useEffect(() => {
    if (session?.accessToken) {
      apiClient.setTokens(session.accessToken, session.refreshToken ?? "")
    } else {
      apiClient.clearTokens()
    }
  }, [session])

  // 注册全局401处理器，当API返回401时自动打开登录弹窗
  useEffect(() => {
    setUnauthorizedHandler(() => {
      showAuthModal("login")
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const isLoading = status === "loading"
  const isAuthenticated = status === "authenticated"
  const user = session?.user || null

  const showAuthModal = (view: "login" | "register" = "login") => {
    setAuthModalView(view)
    setIsAuthModalOpen(true)
  }

  const hideAuthModal = () => {
    setIsAuthModalOpen(false)
  }

  const login = async () => {
    showAuthModal("login")
  }

  const logout = () => {
    signOut()
    apiClient.clearTokens()
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        isAuthModalOpen,
        authModalView,
        showAuthModal,
        hideAuthModal,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function AuthProvider({ children }: { children: ReactNode }) {
  return (
    <SessionProvider>
      <AuthProviderContent>{children}</AuthProviderContent>
    </SessionProvider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
