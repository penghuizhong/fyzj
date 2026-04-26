"use client"

import { useState } from "react"
import { useAuth } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function LoginForm() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const { login, showAuthModal, isLoading } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await login(username, password)
    } catch (err) {
      alert("登录失败，请检查账号密码")
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">欢迎回来</h1>
        <p className="text-sm text-muted-foreground">输入您的账号以进入方圆智版</p>
      </div>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="username" className="text-foreground/80">账号</Label>
          <Input
            id="username"
            placeholder="请输入账号"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="bg-background border-input focus:ring-ring"
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password text-foreground/80">密码</Label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="bg-background border-input focus:ring-ring"
          />
        </div>
        <Button type="submit" className="w-full bg-primary text-primary-foreground hover:opacity-90" disabled={isLoading}>
          {isLoading ? "正在登录..." : "立即登录"}
        </Button>
      </form>
      <div className="text-center text-sm">
        <span className="text-muted-foreground">没有账号？</span>{" "}
        <button
          onClick={() => showAuthModal("register")}
          className="text-primary hover:underline font-medium"
        >
          立即注册
        </button>
      </div>
    </div>
  )
}