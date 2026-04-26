import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useCourses } from './use-courses'
import { apiClient } from '@/lib/api'

vi.mock('@/lib/api', () => ({
  apiClient: {
    getCourses: vi.fn(),
  },
}))

const mockCourse = {
  id: 'course-1',
  title: '打版高级工艺进阶',
  description: '拆解行业内最核心的打版机密',
  price: '¥299',
  tag: '进阶',
  created_at: '2024-01-01',
}

const mockCoursesResponse = {
  total: 1,
  items: [mockCourse],
  skip: 0,
  limit: 10,
}

describe('useCourses', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns empty courses and not loading when not authenticated', () => {
    const { result } = renderHook(() => useCourses(false))
    expect(result.current.courses).toEqual([])
    expect(result.current.coursesLoading).toBe(false)
    expect(apiClient.getCourses).not.toHaveBeenCalled()
  })

  it('fetches courses when authenticated', async () => {
    vi.mocked(apiClient.getCourses).mockResolvedValue(mockCoursesResponse)
    const { result } = renderHook(() => useCourses(true))

    await waitFor(() => expect(result.current.coursesLoading).toBe(false))

    expect(result.current.courses).toEqual([mockCourse])
  })

  it('sets loading state during fetch', async () => {
    vi.mocked(apiClient.getCourses).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCourses(true))

    expect(result.current.coursesLoading).toBe(true)
    expect(result.current.courses).toEqual([])
  })

  it('handles API error gracefully', async () => {
    vi.mocked(apiClient.getCourses).mockRejectedValue(new Error('Network error'))
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { result } = renderHook(() => useCourses(true))

    await waitFor(() => expect(result.current.coursesLoading).toBe(false))

    expect(result.current.courses).toEqual([])
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })
})