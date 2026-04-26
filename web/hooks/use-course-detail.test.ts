import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { useCourseDetail } from './use-course-detail'
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

describe('useCourseDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns loading true initially when authenticated', () => {
    vi.mocked(apiClient.getCourses).mockReturnValue(new Promise(() => {}))
    const { result } = renderHook(() => useCourseDetail('course-1', true))
    expect(result.current.loading).toBe(true)
    expect(result.current.course).toBeNull()
    expect(result.current.error).toBeNull()
  })

  it('fetches and returns matching course', async () => {
    vi.mocked(apiClient.getCourses).mockResolvedValue(mockCoursesResponse)
    const { result } = renderHook(() => useCourseDetail('course-1', true))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.course).toEqual(mockCourse)
    expect(result.current.error).toBeNull()
  })

  it('sets error when course not found', async () => {
    vi.mocked(apiClient.getCourses).mockResolvedValue(mockCoursesResponse)
    const { result } = renderHook(() => useCourseDetail('nonexistent', true))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.course).toBeNull()
    expect(result.current.error).toBe('课程未找到')
  })

  it('sets error when API call fails', async () => {
    vi.mocked(apiClient.getCourses).mockRejectedValue(new Error('Network error'))
    const { result } = renderHook(() => useCourseDetail('course-1', true))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.course).toBeNull()
    expect(result.current.error).toBe('Network error')
  })

  it('does not fetch when not authenticated', () => {
    const { result } = renderHook(() => useCourseDetail('course-1', false))
    expect(result.current.loading).toBe(false)
    expect(apiClient.getCourses).not.toHaveBeenCalled()
  })

  it('does not fetch when courseId is empty', () => {
    const { result } = renderHook(() => useCourseDetail('', true))
    expect(result.current.loading).toBe(false)
    expect(apiClient.getCourses).not.toHaveBeenCalled()
  })

  it('uses fallback error message when error has no message', async () => {
    vi.mocked(apiClient.getCourses).mockRejectedValue(new Error())
    const { result } = renderHook(() => useCourseDetail('course-1', true))

    await waitFor(() => expect(result.current.loading).toBe(false))

    expect(result.current.error).toBe('加载失败')
  })
})