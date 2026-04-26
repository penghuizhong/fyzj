"use client"

import { useTheme } from "next-themes"
import { useSyncExternalStore } from "react"
import { UserResponse } from "@/lib/api"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Sun, Moon, User, LogOut, BookOpen } from "lucide-react"

interface NavbarProps {
  user: UserResponse | null
  isAuthenticated: boolean
  onLogout: () => void
  onShowAuth: (action: "login" | "register") => void
  onNavigateCourse: () => void
}

export function Navbar({
  user,
  isAuthenticated,
  onLogout,
  onShowAuth,
  onNavigateCourse,
}: NavbarProps) {
  const { setTheme, theme } = useTheme()
  const mounted = useSyncExternalStore(
    () => () => { },
    () => true,
    () => false
  )

  return (
    <header
      role="banner"
      className="absolute top-0 w-full p-4 flex justify-between items-center z-50 bg-gradient-to-b from-background/90 to-transparent"
    >
      <span className="tracking-widest font-medium text-foreground">
        方圆智版
      </span>

      <div className="flex items-center gap-2">
        <button
          aria-label="切换主题"
          className="rounded-full bg-background/50 backdrop-blur-md border border-border/50 h-9 w-9 inline-flex items-center justify-center hover:bg-accent transition-colors"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {mounted ? (
            theme === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )
          ) : (
            <span className="opacity-0">·</span>
          )}
        </button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              aria-label="用户菜单"
              className="h-8 w-8 rounded-full flex items-center justify-center bg-muted hover:bg-accent transition-colors"
            >
              {isAuthenticated && user?.username ? (
                <Avatar size="sm">
                  <AvatarFallback className="text-xs font-medium">
                    {user.username[0].toUpperCase()}
                  </AvatarFallback>
                </Avatar>
              ) : (
                <User className="h-4 w-4 text-muted-foreground" />
              )}
            </button>
          </DropdownMenuTrigger>

          <DropdownMenuContent align="end" className="w-48">
            {isAuthenticated ? (
              <>
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{user?.username}</span>
                    <span className="text-xs text-muted-foreground">
                      {user?.email || "未设置邮箱"}
                    </span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onNavigateCourse}>
                  <BookOpen className="mr-2 h-4 w-4" />
                  我的课程
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={onLogout} variant="destructive">
                  <LogOut className="mr-2 h-4 w-4" />
                  退出登录
                </DropdownMenuItem>
              </>
            ) : (
              <DropdownMenuItem onClick={() => onShowAuth("login")}>
                <User className="mr-2 h-4 w-4" />
                登录 / 注册
              </DropdownMenuItem>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}