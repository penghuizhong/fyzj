"use client"

import { SessionProvider, signIn, signOut, useSession } from "next-auth/react"
import {
  createContext,
  useContext,
  useState,
  useEffect,
  ReactNode,
} from "react"

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
    await signIn("casdoor")
  }

  const logout = () => {
    signOut()
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
