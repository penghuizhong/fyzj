"use client"

import { useState, useEffect } from "react"
import { apiClient, CourseResponse } from "@/lib/api"

export function useCourseDetail(courseId: string, isAuthenticated: boolean) {
  const [course, setCourse] = useState<CourseResponse | null>(null)
  const [loading, setLoading] = useState(isAuthenticated && !!courseId)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isAuthenticated || !courseId) {
      return
    }

    let cancelled = false

    apiClient
      .getCourses()
      .then((data) => {
        if (cancelled) return
        const found = data.items.find((c) => c.id === courseId)
        if (found) {
          setCourse(found)
        } else {
          setError("课程未找到")
        }
      })
      .catch((err) => {
        if (cancelled) return
        setError(err.message || "加载失败")
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [courseId, isAuthenticated])

  return { course, loading, error }
}