// components/course/course-list.tsx
"use client"

import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"

const COURSE_LIST = [
    { id: 1, title: '西装领口高级工艺', desc: '掌握 2% 缩水率的核心换算，解决领口不服帖的工业级难题。', price: '¥299', tag: '高阶推荐' },
    { id: 2, title: '女装袖口收尖规程', desc: '从原型到成衣，15年打版实战经验总结。', price: '¥199', tag: '实战进阶' },
    { id: 3, title: '男裤立裆换算公式', desc: '告别死记硬背，一套公式吃透男裤立裆结构。', price: '¥99', tag: '基础必修' },
    { id: 4, title: '连袖结构与腋下折痕', desc: '处理连袖腋下堆量的独家几何切展方法。', price: '¥159', tag: '细节精讲' }
]

export function CourseList() {
    const router = useRouter()

    return (
        <div className="max-w-3xl mx-auto flex flex-col gap-6 animate-in fade-in duration-500">
            <div className="mb-6 pt-4">
                <h1 className="text-3xl font-bold tracking-tight">进阶课程</h1>
                <p className="text-muted-foreground mt-2">打磨 15 年的工业级经验，现已全面开放。</p>
            </div>
            {COURSE_LIST.map((course) => (
                <Card key={course.id} className="rounded-[2rem] border-muted/30 bg-secondary/30 hover:bg-secondary/60 transition-colors cursor-pointer border-t border-white/10 shadow-sm">
                    <CardHeader>
                        <div className="flex justify-between items-start">
                            <div className="text-xs font-medium text-muted-foreground mb-3 px-3 py-1 bg-background/50 rounded-full w-fit">
                                {course.tag}
                            </div>
                            <div className="text-2xl font-bold">{course.price}</div>
                        </div>
                        <CardTitle className="text-xl md:text-2xl leading-relaxed">{course.title}</CardTitle>
                        <CardDescription className="text-base mt-2">{course.desc}</CardDescription>
                    </CardHeader>
                    <CardFooter className="flex justify-end pt-2 pb-6 pr-6">
                        <Button
                            className="rounded-full px-6 bg-foreground text-background font-semibold"
                            onClick={() => router.push(`/course/${course.id}`)}
                        >
                            立即学习
                        </Button>
                    </CardFooter>
                </Card>
            ))}
        </div>
    )
}