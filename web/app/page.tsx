// app/page.tsx
"use client"

import { Button } from "@/components/ui/button"

export default function Home() {
  return (
    <div className="h-full flex flex-col items-center justify-center px-4 animate-in fade-in duration-1000">
      <div className="w-full max-w-3xl flex flex-col items-center gap-6 text-center">
        <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
          方圆智版 <span className="text-muted-foreground font-light">AI</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-md">
          基于15年实战经验，为您提供工业级极简打版计算方案。
        </p>

        <div className="flex flex-wrap justify-center gap-4 mt-8">
          {['🧮 自动放量计算', '📏 领口结构推导', '📘 进阶实战课程'].map(item => (
            <Button key={item} variant="outline" className="rounded-full px-6 py-5 bg-background/50 hover:scale-105 transition-transform">
              {item}
            </Button>
          ))}
        </div>
      </div>
    </div>
  )
}