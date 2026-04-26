import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { useChat } from './use-chat'
import { apiClient } from '@/lib/api'

vi.mock('@/lib/api', () => ({
  apiClient: {
    stream: vi.fn(),
  },
}))

describe('useChat', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns initial state with empty messages and not streaming', () => {
    const showAuthModal = vi.fn()
    const { result } = renderHook(() => useChat(false, showAuthModal))
    expect(result.current.messages).toEqual([])
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.input).toBe('')
  })

  it('calls showAuthModal when sending message while not authenticated', async () => {
    const showAuthModal = vi.fn()
    const { result } = renderHook(() => useChat(false, showAuthModal))

    act(() => {
      result.current.setInput('Hello')
    })

    await act(async () => {
      await result.current.handleSend()
    })

    expect(showAuthModal).toHaveBeenCalledWith('login')
    expect(result.current.messages).toEqual([])
  })

  it('adds user message and streams AI response when authenticated', async () => {
    const showAuthModal = vi.fn()

    async function* mockStreamGenerator() {
      yield { type: 'message', content: '你好' }
      yield { type: 'message', content: '！' }
    }

    vi.mocked(apiClient.stream).mockImplementation(() => mockStreamGenerator())

    const { result } = renderHook(() => useChat(true, showAuthModal))

    act(() => {
      result.current.setInput('你好')
    })

    await act(async () => {
      await result.current.handleSend()
    })

    await waitFor(() => expect(result.current.messages.length).toBe(2))
    expect(result.current.messages[0]).toEqual({ role: 'user', content: '你好' })
    expect(result.current.messages[1]).toEqual({ role: 'ai', content: '你好！' })
    expect(result.current.isStreaming).toBe(false)
  })

  it('adds error message when stream throws', async () => {
    const showAuthModal = vi.fn()

    async function* mockStreamError() {
      throw new Error('Network error')
    }

    vi.mocked(apiClient.stream).mockImplementation(() => mockStreamError())

    const { result } = renderHook(() => useChat(true, showAuthModal))

    act(() => {
      result.current.setInput('Hello')
    })

    await act(async () => {
      await result.current.handleSend()
    })

    await waitFor(() => expect(result.current.isStreaming).toBe(false))
    const lastMessage = result.current.messages[result.current.messages.length - 1]
    expect(lastMessage).toEqual({
      role: 'ai',
      content: '抱歉，发生了错误。请稍后重试。',
    })
  })
})