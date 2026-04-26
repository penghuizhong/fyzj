# OVERVIEW
LangGraph AI agent implementations with a registry, lazy loading, and prompt injection safeguarding.

# WHERE TO LOOK

| Concern | File | Key Export |
|---|---|---|
| Agent registry & loader | `agents.py` | `agents`, `get_agent()`, `load_agent()`, `DEFAULT_AGENT` |
| Simple chatbot | `chatbot.py` | `chatbot` (Pregel via `@entrypoint`) |
| RAG knowledge retrieval | `rag_assistant.py` | `rag_assistant` (CompiledStateGraph) |
| Lazy loading base class | `lazy_agent.py` | `LazyLoadingAgent` |
| Prompt injection detection | `safeguard.py` | `Safeguard`, `SafeguardOutput`, `SafetyAssessment` |
| Agent tools | `tools.py` | `database_search` |

# CONVENTIONS

- **Agent registry pattern** — every agent is registered in `agents.py` as `Agent(description=..., graph_like=...)` keyed by string ID. The default is `"rag-assistant"`.
- **Two agent construction styles** — `@entrypoint` functions (chatbot) return `Pregel`; `StateGraph(...).compile()` (rag_assistant) returns `CompiledStateGraph`. Both are accepted as `AgentGraph`.
- **Lazy loading** — agents that need async setup (DB connections, MCP clients) subclass `LazyLoadingAgent`. They must implement `async load()` which sets `self._graph`. Consumers call `await load_agent(id)` before `get_agent(id)`.
- **Safeguard gate** — rag_assistant inserts a `guard_input` → `check_safety` conditional edge before model invocation. Unsafe input routes to `block_unsafe_content` → `END`; safe input proceeds to the model node.
- **Remaining steps guard** — `acall_model` checks `state["remaining_steps"] < 2` and returns a fallback message when tool calls can't complete, preventing infinite loops.
- **Tool binding** — tools are defined with `@tool` decorator in `tools.py`, collected into a list, and bound to the model via `model.bind_tools(tools)`.
- **Model resolution** — all nodes call `get_model(config["configurable"].get("model", settings.DEFAULT_MODEL))` so the caller can override the model per-request.
- **Reserved config keys** — `thread_id`, `user_id`, and `model` are reserved in `config["configurable"]` and must not be overridden by agents.

# ANTI-PATTERNS

- **Calling `get_agent()` without `load_agent()` on a lazy agent** — raises `RuntimeError`. Always `await load_agent(id)` first during startup.
- **Overriding reserved config keys** — `thread_id`, `user_id`, `model` are reserved. Agents must not set these in configurable.
- **Direct model invocation without safeguard** — the rag_assistant always routes through `guard_input`. Any new agent that processes user input must include the safeguard check; bypassing it is an anti-pattern.
- **Hardcoding model names** — use `get_model()` with config override, not `ChatOpenAI(...)` directly.
- **Creating new `Safeguard()` instances per message in long-lived graphs** — instantiate once; the model is stateless but construction has overhead.
- **Returning raw tool output to users** — always let the model node synthesize tool results. The system prompt instructs the model to cite sources, not dump raw matches.

# NOTES

- `DEFAULT_AGENT = "rag-assistant"` — the chatbot is available but not the default. Route to it explicitly with `agent_id="chatbot"`.
- `Safeguard` is gated by `settings.ENABLE_SAFEGUARD` and `settings.DASHSCOPE_API_KEY`. When disabled or missing, it short-circuits to `SafetyAssessment.SAFE`.
- `SafetyAssessment` has three states: `SAFE`, `UNSAFE`, `ERROR`. `ERROR` from parse failures is treated as safe in `check_safety` (falls through to the default case).
- The safeguard prompt is in Chinese (`safeguard_instructions`); the English original is preserved in comments.
- `tools.py` uses LlamaIndex (`VectorStoreIndex`, `PGVectorStore`, `DashScopeEmbedding`) for RAG retrieval, not LangChain's PGVector. Embedding dimension must match the ingestion (`embed_dim=1024`).
- `database_search` creates a new DB + embedding connection per call. For high-throughput deployments, consider pooling or caching the retriever.
- Agent system prompts include the current date (`current_date`) and citation formatting instructions.