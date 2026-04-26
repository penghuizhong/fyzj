// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

export interface UserInput {
  message: string
  model?: string
  thread_id?: string
  user_id?: string
  agent_config?: Record<string, unknown>
}

export interface StreamInput extends UserInput {
  stream_tokens?: boolean
}

export interface StreamEvent {
  type: 'message' | 'token' | 'error'
  content: ChatMessage | string
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

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface UserResponse {
  id: string
  username: string
  email: string
  is_active: boolean
  is_superuser: boolean
  created_at: string
  roles: string[]
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

export interface CourseResponse {
  id: string
  title: string
  description: string
  price: string
  tag: string
  created_at: string
}

export interface CourseListResponse {
  total: number
  items: CourseResponse[]
  skip: number
  limit: number
}

class ApiClient {
  private baseUrl: string
  private accessToken: string | null
  private refreshToken: string | null
  private refreshPromise: Promise<TokenResponse> | null = null

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
    this.accessToken = null
    this.refreshToken = null
  }

  setTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken
    this.refreshToken = refreshToken
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", accessToken)
      localStorage.setItem("refresh_token", refreshToken)
    }
  }

  clearTokens(): void {
    this.accessToken = null
    this.refreshToken = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
    }
  }

  loadTokens(): boolean {
    if (typeof window !== "undefined") {
      this.accessToken = localStorage.getItem("access_token")
      this.refreshToken = localStorage.getItem("refresh_token")
      return !!this.accessToken
    }
    return false
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retry = true
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) || {}),
    }

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (response.status === 401 && retry && this.refreshToken) {
      try {
        await this.performRefresh()
        return this.request(endpoint, options, false)
      } catch {
        this.clearTokens()
        throw new Error("Session expired. Please login again.")
      }
    }

    if (response.status === 401) {
      throw new Error("Unauthorized")
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    return response.json()
  }

  private async performRefresh(): Promise<TokenResponse> {
    if (this.refreshPromise) {
      return this.refreshPromise
    }

    this.refreshPromise = (async () => {
      try {
        if (!this.refreshToken) {
          throw new Error("No refresh token available")
        }
        const data = await this.request<TokenResponse>("/auth/refresh", {
          method: "POST",
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        }, false)
        this.setTokens(data.access_token, data.refresh_token)
        return data
      } finally {
        this.refreshPromise = null
      }
    })()

    return this.refreshPromise
  }

  async login(username: string, password: string): Promise<TokenResponse> {
    const data = await this.request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    })
    this.setTokens(data.access_token, data.refresh_token)
    return data
  }

  async register(
    username: string,
    password: string,
    email?: string
  ): Promise<UserResponse> {
    return this.request<UserResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, ...(email ? { email } : {}), password }),
    })
  }

  async doRefreshToken(): Promise<TokenResponse> {
    if (!this.refreshToken) {
      throw new Error("No refresh token available")
    }
    const data = await this.request<TokenResponse>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: this.refreshToken }),
    })
    this.setTokens(data.access_token, data.refresh_token)
    return data
  }

  async getInfo(): Promise<ServiceMetadata> {
    return this.request<ServiceMetadata>("/info")
  }

  async getMe(): Promise<UserResponse> {
    return this.request<UserResponse>("/auth/me")
  }

  async getCourses(): Promise<CourseListResponse> {
    return this.request<CourseListResponse>("/courses/")
  }

  async invoke(
    input: UserInput,
    agentId: string = "rag-assistant"
  ): Promise<ChatMessage> {
    return this.request<ChatMessage>(`/${agentId}/invoke`, {
      method: "POST",
      body: JSON.stringify(input),
    })
  }

  async *stream(
    input: StreamInput,
    agentId: string = "rag-assistant"
  ): AsyncGenerator<StreamEvent, void, unknown> {
    const url = `${this.baseUrl}/${agentId}/stream`
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    }

    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`
    }

    const response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(input),
    })

    if (!response.ok) {
      throw new Error(`Stream error: ${response.status}`)
    }

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error("No response body")
    }

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
          if (line.startsWith("data: ")) {
            const data = line.slice(6)
            if (data === "[DONE]") {
              return
            }
            try {
              const parsed = JSON.parse(data)
              if (parsed.type === "message" && parsed.content) {
                yield { type: 'message', content: parsed.content } as StreamEvent
              } else if (parsed.type === "token" && parsed.content) {
                yield { type: 'token', content: parsed.content } as StreamEvent
              } else if (parsed.type === "error") {
                yield { type: 'error', content: parsed.content } as StreamEvent
              }
            } catch {
              // Ignore malformed JSON
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }
}

export const apiClient = new ApiClient()