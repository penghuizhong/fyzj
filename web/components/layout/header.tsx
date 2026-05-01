"use client"

import { useState, useEffect } from "react"
import { useTheme } from "next-themes"
import { Button } from "@/components/ui/button"
import { Moon, Sun, UserCircle, LogOut } from "lucide-react"
import { NotificationBanner } from "./notification-banner"
import { useAuth } from "@/lib/auth"

export function Header() {
    const { setTheme, theme } = useTheme()
    const { isAuthenticated, user, showAuthModal, logout } = useAuth()
    const [mounted, setMounted] = useState(false)

    useEffect(() => setMounted(true), [])

    return (
        <div className="absolute top-0 left-0 right-0 flex flex-col items-center pt-6 z-40 pointer-events-none">
            <div className="pointer-events-auto flex flex-col items-center">
                <nav className="flex justify-center gap-6 md:gap-8 text-[15px] font-medium text-muted-foreground mb-4">
                    <span className="text-foreground cursor-pointer">发现</span>
                    <span className="hover:text-foreground cursor-pointer transition-colors">时尚</span>
                    <span className="hover:text-foreground cursor-pointer transition-colors">课程</span>
                    <span className="hover:text-foreground cursor-pointer transition-colors">工具</span>
                    <span className="hover:text-foreground cursor-pointer transition-colors">我们</span>
                </nav>
                <NotificationBanner />
            </div>
        </div>
    )
}
