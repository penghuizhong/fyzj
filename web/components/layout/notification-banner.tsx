// components/layout/notification-banner.tsx
"use client"

import { useNotificationStore } from "@/lib/store/use-notification-store"
import { ArrowRight, X } from "lucide-react"
import Link from "next/link"

export function NotificationBanner() {
    const { content, tag, isVisible, link, closeNotification } = useNotificationStore()

    if (!isVisible) return null

    return (
        <div className="flex items-center gap-2 animate-in fade-in slide-in-from-top-4 duration-500">
            <Link href={link}>
                <div className="flex items-center bg-background/40 backdrop-blur-md border border-muted-foreground/30 hover:border-muted-foreground/50 transition-colors rounded-full pl-1.5 pr-4 py-1.5 cursor-pointer group">
                    <span className="bg-[#1f2f32] dark:bg-[#1a2b2e] text-[#4db8a6] px-3 py-1 rounded-full text-[11px] font-medium tracking-wide mr-3">
                        {tag}
                    </span>
                    <span className="text-sm text-foreground/90 mr-3">{content}</span>
                    <div className="w-[1px] h-4 bg-muted-foreground/30 mr-3"></div>
                    <span className="text-muted-foreground flex items-center text-sm group-hover:text-foreground transition-colors">
                        升级 <ArrowRight size={14} className="ml-1 opacity-80" />
                    </span>
                </div>
            </Link>

            {/* 手动关闭按钮 */}
            <button
                onClick={(e) => {
                    e.stopPropagation()
                    closeNotification()
                }}
                className="p-1 hover:bg-secondary rounded-full text-muted-foreground transition-colors"
            >
                <X size={14} />
            </button>
        </div>
    )
}