"use client"

import { SessionProvider, useSession, signIn, signOut } from "next-auth/react"
import type { Session } from "next-auth"
// 👉 1. 记得引入 useState
import { createContext, useContext, useEffect, useState, ReactNode } from "react"
import { apiClient, setUnauthorizedHandler } from "@/lib/api"
import { toast } from "sonner"

interface AuthContextType {
  user: {
    id?: string
    name?: string | null
    email?: string | null
    image?: string | null
  } | null
  isAuthenticated: boolean
  isLoading: boolean
  login: () => Promise<void>
  logout: () => Promise<void>
  // 👉 2. 增加弹窗相关的类型定义
  isAuthModalOpen: boolean
  showAuthModal: () => void
  hideAuthModal: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

function AuthProviderContent({ children }: { children: ReactNode }) {
  const { data: session, status } = useSession()

  // 👉 3. 增加弹窗的 State
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false)
  const showAuthModal = () => setIsAuthModalOpen(true)
  const hideAuthModal = () => setIsAuthModalOpen(false)

  // accessToken 同步到 apiClient
  useEffect(() => {
    if (session?.accessToken) {
      apiClient.setToken(session.accessToken)
    } else {
      apiClient.clearToken()
    }
  }, [session?.accessToken])

  // 👉 4. 修改 401 拦截逻辑：不再强行 signOut 跳转，而是清空 token 并弹窗提醒
  useEffect(() => {
    setUnauthorizedHandler(() => {
      console.error("触发了 401 拦截！")
      apiClient.clearToken()
      toast.error("登录状态已过期，请重新登录")
      showAuthModal() // 弹出你定制的 AuthModal
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const isLoading = status === "loading"
  const isAuthenticated = status === "authenticated"
  const user = session?.user ?? null

  const login = async () => {
    await signIn("casdoor")
  }

  const logout = async () => {
    apiClient.clearToken()
    await signOut({ callbackUrl: "/" })
  }

  return (
    // 👉 5. 将弹窗状态和方法暴露出去
    <AuthContext.Provider value={{
      user, isAuthenticated, isLoading, login, logout,
      isAuthModalOpen, showAuthModal, hideAuthModal
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export function AuthProvider({ children, session }: { children: ReactNode; session: Session | null }) {
  return (
    <SessionProvider session={session}>
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