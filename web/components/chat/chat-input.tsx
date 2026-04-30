// components/chat/chat-input.tsx
"use client"

import { useState, useEffect, useRef } from "react"
import { ArrowUp, Plus, Mic, Paperclip, Image as ImageIcon, Lightbulb, Square } from "lucide-react"

interface ChatInputProps {
    value: string
    onChange: (val: string) => void
    onSend: () => void
    isStreaming?: boolean
    onStop?: () => void
}

export function ChatInput({ value, onChange, onSend, isStreaming, onStop }: ChatInputProps) {
    const [showMenu, setShowMenu] = useState(false)
    const [isThinking, setIsThinking] = useState(false)
    const menuRef = useRef<HTMLDivElement>(null)
    const plusBtnRef = useRef<HTMLButtonElement>(null)

    // 点击外部关闭悬浮菜单
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (
                menuRef.current && !menuRef.current.contains(e.target as Node) &&
                plusBtnRef.current && !plusBtnRef.current.contains(e.target as Node)
            ) {
                setShowMenu(false)
            }
        }
        document.addEventListener("mousedown", handleClickOutside)
        return () => document.removeEventListener("mousedown", handleClickOutside)
    }, [])

    return (
        <div className="relative w-full max-w-3xl mx-auto drop-shadow-xl">
            {/* 悬浮菜单 */}
            {showMenu && (
                <div ref={menuRef} className="absolute bottom-full left-0 mb-3 w-[260px] bg-popover rounded-[1.5rem] p-2 shadow-2xl border border-border z-50 animate-in fade-in slide-in-from-bottom-2 duration-200">
                    <div className="flex flex-col">
                        {/* ⚠️ 注意：所有不负责提交的按钮，必须明确加上 type="button"，防止误触发表单提交 */}
                        <button type="button" className="flex items-center gap-3 px-3 py-3 hover:bg-muted rounded-xl transition-colors text-left group">
                            <Paperclip className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                            <span className="text-[15px] font-medium text-foreground/80 group-hover:text-foreground transition-colors">添加照片和文件</span>
                        </button>

                        <div className="h-[1px] bg-border mx-3 my-1" />

                        <button type="button" className="flex items-center gap-3 px-3 py-3 hover:bg-muted rounded-xl transition-colors text-left group">
                            <ImageIcon className="h-5 w-5 text-muted-foreground group-hover:text-foreground transition-colors" />
                            <span className="text-[15px] font-medium text-foreground/80 group-hover:text-foreground transition-colors">创建图片</span>
                        </button>

                        <button
                            type="button"
                            onClick={() => setIsThinking(!isThinking)}
                            className="flex items-center gap-3 px-3 py-3 hover:bg-muted rounded-xl transition-colors text-left group"
                        >
                            <Lightbulb className={`h-5 w-5 transition-colors ${isThinking ? 'text-[#4db8a6]' : 'text-muted-foreground group-hover:text-foreground'}`} />
                            <span className="text-[15px] font-medium text-foreground/80 group-hover:text-foreground transition-colors">思考一下</span>
                        </button>
                    </div>
                </div>
            )}

            {/* ✅ 核心优化：将包裹层改为 form，原生支持 PC 回车和移动端软键盘的"前往/发送"键 */}
            <form
                onSubmit={(e) => {
                    e.preventDefault() // 阻止表单默认的刷新页面行为
                    if (!isStreaming && value.trim()) {
                        onSend()
                    }
                }}
                className="flex items-center w-full bg-background rounded-[2rem] pl-2 pr-2.5 py-2 border border-input transition-all focus-within:ring-1 focus-within:ring-ring"
            >
                <button
                    type="button"
                    ref={plusBtnRef}
                    onClick={() => setShowMenu(!showMenu)}
                    className={`p-3 transition-colors rounded-full ${showMenu ? 'text-foreground bg-accent' : 'text-muted-foreground hover:text-accent-foreground hover:bg-accent/50'}`}
                >
                    <Plus className={`h-6 w-6 stroke-[1.5] transition-transform duration-300 ${showMenu ? 'rotate-45' : 'rotate-0'}`} />
                </button>

                <input
                    className="flex-1 bg-transparent border-none shadow-none focus:outline-none text-[16px] px-2 text-foreground placeholder:text-muted-foreground disabled:opacity-50"
                    placeholder="有问题，尽管问"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    disabled={isStreaming}
                // 🗑️ 删除了 onKeyDown，因为现在由外层的 form onSubmit 统一接管了
                />

                <button type="button" className="p-3 text-muted-foreground hover:text-foreground transition-colors rounded-full disabled:opacity-50" disabled={isStreaming}>
                    <Mic className="h-[22px] w-[22px] stroke-[1.5]" />
                </button>

                {isStreaming ? (
                    <button
                        type="button"
                        onClick={onStop}
                        className="ml-1 h-11 w-11 min-w-[44px] rounded-full flex items-center justify-center bg-destructive text-destructive-foreground hover:opacity-90 transition-all duration-300 shadow-md"
                    >
                        <Square className="h-5 w-5 fill-current" />
                    </button>
                ) : (
                    <button
                        type="submit" // ✅ 发送按钮指定为 submit 类型
                        disabled={!value.trim()}
                        className={`ml-1 h-11 w-11 min-w-[44px] rounded-full flex items-center justify-center transition-all duration-300 ${value.trim()
                            ? 'bg-primary text-primary-foreground hover:scale-105 shadow-md'
                            : 'bg-muted text-muted-foreground cursor-not-allowed opacity-80'
                            }`}
                    >
                        <ArrowUp className="h-6 w-6 stroke-[2.5]" />
                    </button>
                )}
            </form>
        </div>
    )
}