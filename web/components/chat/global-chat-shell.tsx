"use client"

import { useState, useRef, useEffect } from "react"
import { apiClient, ChatMessage } from "@/lib/api" // 使用您提供的 ApiClient
import { ChatInput } from "./chat-input"
import { ScrollArea } from "@/components/ui/scroll-area"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { X } from "lucide-react"
import { useAuth } from "@/lib/auth"

export function GlobalChatShell() {
    const [messages, setMessages] = useState<ChatMessage[]>([])
    const [input, setInput] = useState("")
    const [isStreaming, setIsStreaming] = useState(false)
    const scrollRef = useRef<HTMLDivElement>(null)
    const { isAuthenticated, showAuthModal } = useAuth()

    useEffect(() => { scrollRef.current?.scrollIntoView({ behavior: "smooth" }) }, [messages])

    const handleSend = async () => {
        if (!isAuthenticated) {
            showAuthModal('login')
            return
        }

        if (!input.trim() || isStreaming) return
        const userMsg = input; setInput(""); setIsStreaming(true)

        // 1. 先把用户的消息和AI的空位占好
        setMessages(prev => [...prev, { type: 'human', content: userMsg }, { type: 'ai', content: '' }])

        try {
            // 2. 调用您 apiClient 里的 stream 方法
            const stream = apiClient.stream({
                message: userMsg,
                stream_tokens: true
            }, "rag-assistant")

            let fullAIContent = ""
            for await (const event of stream) {
                if (event.type === 'token') {
                    fullAIContent += event.content
                    // 3. 实时更新最后一条消息的内容（打字机效果）
                    setMessages(prev => {
                        const newMsgs = [...prev]
                        newMsgs[newMsgs.length - 1].content = fullAIContent
                        return newMsgs
                    })
                }
            }
        } catch (error) {
            console.error("对话失败", error)
        } finally {
            setIsStreaming(false)
        }
    }

    return (
        <>
            {messages.length > 0 && (
                <div className="absolute inset-0 z-30 bg-background/60 backdrop-blur-md px-4 pt-24 pb-40 animate-in fade-in duration-300">
                    <button onClick={() => setMessages([])} className="absolute top-8 right-8 p-3 rounded-full bg-secondary/50 hover:bg-secondary transition-all z-50">
                        <X size={22} />
                    </button>

                    <ScrollArea className="h-full max-w-3xl mx-auto">
                        <div className="flex flex-col gap-6">
                            {messages.map((msg, i) => (
                                <div key={i} className={`flex ${msg.type === 'human' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`p-4 px-6 rounded-[2rem] max-w-[85%] prose dark:prose-invert shadow-sm ${msg.type === 'human' ? 'bg-secondary' : 'bg-card border border-border'
                                        }`}>
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                                    </div>
                                </div>
                            ))}
                            <div ref={scrollRef} />
                        </div>
                    </ScrollArea>
                </div>
            )}

            <div className="absolute bottom-8 left-0 right-0 w-full max-w-3xl mx-auto px-4 z-40">
                <ChatInput value={input} onChange={setInput} onSend={handleSend} isStreaming={isStreaming} />
            </div>
        </>
    )
}