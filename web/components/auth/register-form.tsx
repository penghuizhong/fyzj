"use client"

import { useState } from "react"
import { useAuth } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Eye, EyeOff, AlertCircle } from "lucide-react" // 新增 AlertCircle 图标

export function RegisterForm() {
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)

  // 新增：专门用来存报错信息的变量
  const [errorMessage, setErrorMessage] = useState("")

  const { register, showAuthModal, isLoading } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage("") // 每次提交前先清空旧错误

    if (password !== confirmPassword) {
      setErrorMessage("两次输入的密码不一致，请重新检查")
      return
    }

    try {
      await register(username, password, email)
      // 注册成功可以保留弹窗，或者换成更优雅的提示，这里先跳回登录
      showAuthModal("login")
    } catch (err) {
      // 抛弃 alert()，把错误信息显示在界面上
      setErrorMessage("注册失败：该账号可能已被占用，请更换账号名称")
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">创建账号</h1>
        <p className="text-sm text-muted-foreground">基于15年实战经验，为您打造AI制版新起点</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* ... 前面的 账号、邮箱、密码、确认密码 的 Input 代码保持完全不变 ... */}

        {/* 只需在账号名称这块保留即可，为了节省篇幅我省略了输入框的重复代码，您保留原样即可 */}
        <div className="space-y-2">
          <Label htmlFor="reg-username" className="text-foreground/80">账号名称</Label>
          <Input
            id="reg-username"
            placeholder="建议使用实名或工号"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            className="bg-background border-input rounded-xl"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="reg-email" className="text-foreground/80">邮箱 (可选)</Label>
          <Input
            id="reg-email"
            type="email"
            placeholder="用于找回密码"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="bg-background border-input rounded-xl"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="reg-password" className="text-foreground/80">设置密码</Label>
          <div className="relative">
            <Input
              id="reg-password"
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="请输入密码"
              className="bg-background border-input rounded-xl pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirm-password" className="text-foreground/80">确认密码</Label>
          <div className="relative">
            <Input
              id="confirm-password"
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="请再次输入密码"
              className="bg-background border-input rounded-xl pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          </div>
        </div>

        {/* 新增：优雅的红色错误提示框 */}
        {errorMessage && (
          <div className="flex items-center gap-2 text-sm text-red-500 bg-red-500/10 p-3 rounded-lg border border-red-500/20">
            <AlertCircle size={16} />
            <p>{errorMessage}</p>
          </div>
        )}

        <Button
          type="submit"
          className="w-full bg-primary text-primary-foreground hover:opacity-90 rounded-xl py-6 text-base font-semibold transition-all shadow-md active:scale-[0.98]"
          disabled={isLoading}
        >
          {isLoading ? "正在为您开通..." : "注册并开始使用"}
        </Button>
      </form>

      <div className="text-center text-sm">
        <span className="text-muted-foreground">已有账号？</span>{" "}
        <button
          onClick={() => showAuthModal("login")}
          className="text-primary hover:underline font-medium transition-all"
        >
          返回登录
        </button>
      </div>
    </div>
  )
}