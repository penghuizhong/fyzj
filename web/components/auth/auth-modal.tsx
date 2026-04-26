"use client"

import { useState } from "react"
import { useAuth } from "@/lib/auth"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription, // 1. 新增引入 Description
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { LoginForm } from "@/components/auth/login-form"
import { RegisterForm } from "@/components/auth/register-form"
import { CheckCircle2 } from "lucide-react"
import { VisuallyHidden } from "@radix-ui/react-visually-hidden" // 2. 新增引入隐藏组件

export function AuthModal() {
  const { isAuthModalOpen, hideAuthModal } = useAuth()
  const [view, setView] = useState<"login" | "register">("login")
  const [registerSuccess, setRegisterSuccess] = useState(false)

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      hideAuthModal()
      setTimeout(() => {
        setView("login")
        setRegisterSuccess(false)
      }, 200)
    }
  }

  return (
    <Dialog open={isAuthModalOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="bg-zinc-900/95 backdrop-blur-xl border-zinc-800 text-white sm:max-w-[420px] rounded-2xl shadow-2xl p-6">

        {/* 核心修复：添加对读屏软件可见但视觉隐藏的 Description，完美消灭警告 */}
        <VisuallyHidden>
          <DialogDescription>
            请登录或注册您的方圆智版账号，以体验AI辅助服装制版功能。
          </DialogDescription>
        </VisuallyHidden>

        <DialogHeader className="mb-2">
          <DialogTitle className="text-center text-xl font-bold tracking-wider">
            {registerSuccess ? "操作成功" : view === "login" ? "欢迎回来" : "加入方圆智版"}
          </DialogTitle>
        </DialogHeader>

        {registerSuccess ? (
          // 注册成功状态：加入了微动画，提升工业质感
          <div className="flex flex-col items-center gap-4 py-8 animate-in fade-in zoom-in-95 duration-300">
            <CheckCircle2 className="h-16 w-16 text-green-500" />
            <h3 className="text-xl font-semibold">账号创建成功！</h3>
            <p className="text-zinc-400 text-center text-sm">
              您的专属AI制版工作台已准备就绪
            </p>
            <Button
              onClick={() => handleOpenChange(false)}
              className="mt-4 w-full bg-primary text-primary-foreground hover:opacity-90 rounded-xl py-6 text-base font-semibold transition-all active:scale-[0.98]"
            >
              进入工作台
            </Button>
          </div>
        ) : (
          <>
            {/* 顶部 Tab 切换区：调整了暗黑模式的色彩对比度，使其更像真实的拨动开关 */}
            <div className="flex gap-1 rounded-xl bg-zinc-800/60 p-1 mb-6">
              <button
                onClick={() => setView("login")}
                className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${view === "login"
                    ? "bg-zinc-700 text-white shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700/50"
                  }`}
              >
                登录
              </button>
              <button
                onClick={() => setView("register")}
                className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${view === "register"
                    ? "bg-zinc-700 text-white shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-700/50"
                  }`}
              >
                注册
              </button>
            </div>

            {/* 表单渲染区：加入了平滑的切页动画 */}
            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
              {view === "login" ? (
                <LoginForm embedded />
              ) : (
                <RegisterForm
                  embedded
                  onSuccess={() => setRegisterSuccess(true)}
                />
              )}
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}