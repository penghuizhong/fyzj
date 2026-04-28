"use client"

import { useAuth } from "@/lib/auth"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { signIn } from "next-auth/react" // 引入 Auth.js 的绝招

export function AuthModal() {
  const { isAuthModalOpen, hideAuthModal } = useAuth()

  return (
    <Dialog open={isAuthModalOpen} onOpenChange={hideAuthModal}>
      <DialogContent className="bg-zinc-900/95 backdrop-blur-xl border-zinc-800 text-white sm:max-w-[400px] rounded-2xl shadow-2xl p-8 text-center">

        <DialogHeader className="mb-6">
          <DialogTitle className="text-2xl font-bold tracking-wider">
            加入方圆智版
          </DialogTitle>
          <p className="text-zinc-400 text-sm mt-2">
            基于15年实战经验，为您打造AI制版新起点
          </p>
        </DialogHeader>

        {/* 核心改动：把复杂的表单，变成一个直接跳往 Casdoor 的大按钮 */}
        <div className="space-y-4">
          <Button
            onClick={() => signIn("casdoor")} // 一键呼叫 Casdoor 托管页
            className="w-full bg-primary text-primary-foreground hover:opacity-90 rounded-xl py-6 text-base font-semibold transition-all active:scale-[0.98]"
          >
            登录 / 注册
          </Button>
          <p className="text-xs text-zinc-500">
            点击将跳转至统一安全认证中心
          </p>
        </div>

      </DialogContent>
    </Dialog>
  )
}