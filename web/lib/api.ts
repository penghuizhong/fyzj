const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001"

// 全局 401 处理器，由 AuthProvider 注册
let globalUnauthorizedHandler: (() => void) | null = null

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  globalUnauthorizedHandler = handler
}

// ── 类型定义（与后端 schema.py 对齐）─────────────────────────────────────────

export interface UserInput {
  message: string
  model?: string
  thread_id?: string
  // user_id 已删除：后端从 JWT sub 字段自动取
  agent_config?: Record<string, unknown>
}

export interface StreamInput extends UserInput {
  stream_tokens?: boolean
}

export interface ChatMessage {
  type: "human" | "ai" | "tool" | "custom"
  content: string
  tool_calls?: unknown[]
  tool_call_id?: string | null
  run_id?: string | null
  response_metadata?: Record<string, unknown>
  custom_data?: Record<string, unknown>
}

export interface StreamEvent {
  type: "message" | "token" | "error"
  content: ChatMessage | string
}

export interface AgentInfo {
  key: string
  description: string
}

export interface ServiceMetadata {
  agents: AgentInfo[]
  models: string[]
  default_agent: string
  default_model: string
}

export interface Feedback {
  run_id: string
  key: string
  score: number                        // 0.0 ~ 1.0
  kwargs?: Record<string, unknown>
}

export interface ChatHistoryInput {
  thread_id: string
}

export interface ChatHistory {
  messages: ChatMessage[]
}

// ── ApiClient ─────────────────────────────────────────────────────────────────

class ApiClient {
  private baseUrl: string
  private accessToken: string | null = null

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  setToken(accessToken: string): void {
    this.accessToken = accessToken
  }

  clearToken(): void {
    this.accessToken = null
  }

  private buildHeaders(extra: Record<string, string> = {}): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...extra,
    }
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`
    }
    return headers
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: this.buildHeaders(options.headers as Record<string, string>),
    })

    if (response.status === 401) {
      globalUnauthorizedHandler?.()
      return new Promise(() => { }) as Promise<T>
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // ── 后端现有接口 ────────────────────────────────────────────────────────────

  /** GET /api/agent/info — 获取服务元数据 */
  async getInfo(): Promise<ServiceMetadata> {
    return this.request<ServiceMetadata>("/api/agent/info")
  }

  /** POST /api/agent/{agentId}/invoke — 同步对话 */
  async invoke(
    input: UserInput,
    agentId: string = "rag-assistant"
  ): Promise<ChatMessage> {
    return this.request<ChatMessage>(`/api/agent/${agentId}/invoke`, {
      method: "POST",
      body: JSON.stringify(input),
    })
  }

  /** POST /api/agent/feedback — 提交反馈 */
  async feedback(input: Feedback): Promise<void> {
    return this.request<void>("/api/agent/feedback", {
      method: "POST",
      body: JSON.stringify(input),
    })
  }

  /** POST /api/agent/history — 获取会话历史 */
  async history(input: ChatHistoryInput): Promise<ChatHistory> {
    return this.request<ChatHistory>("/api/agent/history", {
      method: "POST",
      body: JSON.stringify(input),
    })
  }

  /** POST /api/agent/{agentId}/stream — SSE 流式对话 */
  async *stream(
    input: StreamInput,
    agentId: string = "rag-assistant"
  ): AsyncGenerator<StreamEvent, void, unknown> {
    const response = await fetch(
      `${this.baseUrl}/api/agent/${agentId}/stream`,
      {
        method: "POST",
        headers: this.buildHeaders(),
        body: JSON.stringify(input),
      }
    )

    if (response.status === 401) {
      globalUnauthorizedHandler?.()
      return
    }

    if (!response.ok) {
      throw new Error(`Stream error: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error("No response body")

    const decoder = new TextDecoder()
    let buffer = ""

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          const data = line.slice(6)
          if (data === "[DONE]") return

          try {
            const parsed = JSON.parse(data)
            if (parsed.type === "message" && parsed.content) {
              yield { type: "message", content: parsed.content } as StreamEvent
            } else if (parsed.type === "token" && parsed.content) {
              yield { type: "token", content: parsed.content } as StreamEvent
            } else if (parsed.type === "error") {
              yield { type: "error", content: parsed.content } as StreamEvent
            }
          } catch {
            // 跳过无法解析的行
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }
}

export const apiClient = new ApiClient()