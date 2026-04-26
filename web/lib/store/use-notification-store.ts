// lib/store/use-notification-store.ts
import { create } from 'zustand'

interface NotificationState {
    content: string        // 通知文字内容
    isVisible: boolean     // 是否显示
    tag: string            // 标签文字，如 "New" 或 "Hot"
    link: string           // 点击跳转的链接
    // 行为
    setNotification: (content: string, tag?: string, link?: string) => void
    closeNotification: () => void
}

export const useNotificationStore = create<NotificationState>((set) => ({
    content: "服装结构设计系统课程已上线...", // 初始默认值
    isVisible: true,
    tag: "New",
    link: "/course",

    setNotification: (content, tag = "New", link = "/course") =>
        set({ content, tag, link, isVisible: true }),

    closeNotification: () => set({ isVisible: false }),
}))