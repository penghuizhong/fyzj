"use client"
import { useState, useEffect } from "react"
import { apiClient, CourseResponse } from "@/lib/api"

export function useCourses(isAuthenticated: boolean) {
  const [courses, setCourses] = useState<CourseResponse[]>([])
  const [coursesLoading, setCoursesLoading] = useState(isAuthenticated)

  useEffect(() => {
    if (!isAuthenticated) {
      return
    }

    apiClient.getCourses()
      .then(data => setCourses(data.items))
      .catch(console.error)
      .finally(() => setCoursesLoading(false))
  }, [isAuthenticated])

  return { courses, coursesLoading }
}
