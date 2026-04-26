"use client"
import { useState } from "react"
import { apiClient } from "@/lib/api"
import { FocusMode } from "@/components/focus-selector"
import { ChatMessage } from "@/components/chat-response"

export function useChat(isAuthenticated: boolean, showAuthModal: (action: 'login' | 'register') => void, focusMode?: FocusMode | null) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [input, setInput] = useState("")

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return

    if (!isAuthenticated) {
      showAuthModal('login')
      return
    }

    const userMessage = input.trim()
    setInput("")
    setMessages(prev => [...prev, { role: "user", content: userMessage }])
    setIsStreaming(true)

    try {
      const stream = apiClient.stream({ 
        message: userMessage, 
        stream_tokens: true,
        agent_config: focusMode ? { focus_mode: focusMode } : undefined
      })
      let aiMessage = ""

      for await (const chunk of stream) {
        if (chunk.content) {
          aiMessage += chunk.content
          setMessages(prev => {
            const newMessages = [...prev]
            const lastMsg = newMessages[newMessages.length - 1]
            if (lastMsg && lastMsg.role === 'ai') {
              lastMsg.content = aiMessage
            } else {
              newMessages.push({ role: "ai", content: aiMessage })
            }
            return newMessages
          })
        }
      }
    } catch {
      setMessages(prev => [...prev, {
        role: "ai",
        content: "抱歉，发生了错误。请稍后重试。"
      }])
    } finally {
      setIsStreaming(false)
    }
  }

  return { messages, isStreaming, input, setInput, handleSend }
}
