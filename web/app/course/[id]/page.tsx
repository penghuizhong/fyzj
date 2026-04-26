"use client"

import { useParams, useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth"
import { useCourseDetail } from "@/hooks/use-course-detail"
import { Navbar } from "@/components/navbar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { PlayCircle, ArrowLeft } from "lucide-react"

export default function CourseDetailPage() {
  const params = useParams()
  const router = useRouter()
  const courseId = params.id as string
  const { user, isAuthenticated, isLoading: authLoading, logout, showAuthModal } = useAuth()
  const { course, loading, error } = useCourseDetail(courseId, isAuthenticated)

  const handleNavigateCourse = () => {
    router.push("/")
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <Navbar
          user={null}
          isAuthenticated={false}
          onLogout={logout}
          onShowAuth={showAuthModal}
          onNavigateCourse={handleNavigateCourse}
        />
        <div className="max-w-3xl mx-auto px-6 pt-24">
          <Skeleton className="h-8 w-48 mb-8" />
          <Skeleton className="h-12 w-3/4 mb-4" />
          <Skeleton className="h-64 w-full rounded-3xl" />
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <Navbar
          user={null}
          isAuthenticated={false}
          onLogout={logout}
          onShowAuth={showAuthModal}
          onNavigateCourse={handleNavigateCourse}
        />
        <div className="max-w-3xl mx-auto px-6 pt-24 flex flex-col items-center justify-center gap-6">
          <div className="text-center space-y-3">
            <h2 className="text-2xl font-bold tracking-tight">请先登录</h2>
            <p className="text-muted-foreground">登录后即可查看课程详情</p>
          </div>
          <Button
            onClick={() => showAuthModal("login")}
            className="rounded-full px-8 bg-primary text-primary-foreground font-semibold"
          >
            登录 / 注册
          </Button>
          <button
            onClick={() => router.push("/")}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← 返回首页
          </button>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <Navbar
          user={user}
          isAuthenticated={isAuthenticated}
          onLogout={logout}
          onShowAuth={showAuthModal}
          onNavigateCourse={handleNavigateCourse}
        />
        <div className="max-w-3xl mx-auto px-6 pt-24">
          <button
            onClick={() => router.push("/")}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors mb-8 inline-flex items-center gap-1"
          >
            <ArrowLeft className="h-4 w-4" /> 方圆智版
          </button>
          <div className="flex flex-col gap-4 animate-in fade-in duration-500">
            <Skeleton className="h-6 w-20 rounded-full" />
            <Skeleton className="h-14 w-3/4" />
            <Skeleton className="h-[300px] w-full rounded-3xl mt-4" />
            <Skeleton className="h-4 w-full mt-6" />
            <Skeleton className="h-4 w-5/6" />
            <Skeleton className="h-4 w-4/6" />
            <Skeleton className="h-10 w-32 rounded-full mt-4" />
          </div>
        </div>
      </div>
    )
  }

  if (error || !course) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <Navbar
          user={user}
          isAuthenticated={isAuthenticated}
          onLogout={logout}
          onShowAuth={showAuthModal}
          onNavigateCourse={handleNavigateCourse}
        />
        <div className="max-w-3xl mx-auto px-6 pt-24 flex flex-col items-center justify-center gap-6">
          <div className="text-center space-y-3">
            <h2 className="text-2xl font-bold tracking-tight">课程未找到</h2>
            <p className="text-muted-foreground">{error || "该课程不存在或已被移除"}</p>
          </div>
          <button
            onClick={() => router.push("/")}
            className="text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← 返回方圆智版
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar
        user={user}
        isAuthenticated={isAuthenticated}
        onLogout={logout}
        onShowAuth={showAuthModal}
        onNavigateCourse={handleNavigateCourse}
      />

      <div className="max-w-3xl mx-auto px-6 pt-24 pb-16">
        <button
          onClick={() => router.push("/")}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors mb-8 inline-flex items-center gap-1"
        >
          <ArrowLeft className="h-4 w-4" /> 方圆智版
        </button>

        <div className="flex flex-col gap-6 animate-page-in">
          {course.tag && (
            <Badge variant="secondary" className="w-fit rounded-full text-xs">
              {course.tag}
            </Badge>
          )}

          <h1 className="text-3xl md:text-5xl font-bold tracking-tight leading-tight">
            {course.title}
          </h1>

          <div className="w-full aspect-video bg-muted/30 border border-muted rounded-3xl mt-2 flex flex-col items-center justify-center cursor-pointer hover:bg-muted/50 transition-colors group">
            <PlayCircle className="h-16 w-16 text-muted-foreground group-hover:scale-110 transition-transform duration-300" />
            <span className="mt-4 text-muted-foreground font-medium">视频即将上线</span>
          </div>

          <div className="mt-4 prose prose-neutral dark:prose-invert max-w-none">
            <p className="text-lg leading-relaxed text-muted-foreground">
              {course.description}
            </p>
          </div>

          <div className="flex items-center gap-6 mt-4">
            {course.price && (
              <span className="text-2xl font-bold">{course.price}</span>
            )}
            <Button
              className="rounded-full px-8 bg-primary text-primary-foreground font-semibold hover:bg-primary/90"
              size="lg"
            >
              开始学习
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}