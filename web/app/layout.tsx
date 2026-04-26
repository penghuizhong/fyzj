// app/layout.tsx
import { GeistSans } from 'geist/font/sans';
import { GeistMono } from 'geist/font/mono';
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import Sidebar from "@/components/ui/sidebar";
import { Header } from "@/components/layout/header";
import { GlobalChatShell } from "@/components/chat/global-chat-shell";
import { AuthProvider } from "@/lib/auth"
import { AuthModal } from "@/components/auth/auth-modal"

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={`${GeistSans.variable} ${GeistMono.variable} antialiased flex h-screen overflow-hidden`}>
        <AuthProvider>
          <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
            {/* 1. 左侧固定侧边栏 */}
            <Sidebar />

            {/* 2. 右侧主容器 */}
            <div className="flex-1 flex flex-col relative bg-background overflow-hidden">
              <Header />

              {/* 动态内容区 */}
              <main className="flex-1 overflow-y-auto pt-24 pb-32">
                {children}
              </main>
              <AuthModal />

              {/* 3. 全局常驻对话壳 (内含 ChatInput 和消息展示逻辑) */}
              <GlobalChatShell />
            </div>
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  );
}