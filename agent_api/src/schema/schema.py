from decimal import Decimal
from typing import Any, Literal, NotRequired

from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class AgentInfo(BaseModel):
    """关于可用代理的信息。"""

    key: str = Field(
        description="代理键名。",
        examples=["research-assistant"],
    )
    description: str = Field(
        description="代理的描述。",
        examples=["用于生成研究论文的研究助手。"],
    )


class ServiceMetadata(BaseModel):
    """服务的元数据，包括可用的代理和模型。"""

    agents: list[AgentInfo] = Field(
        description="可用代理列表。",
    )
    # 💡 核心修改 2：AllModelEnum 替换为普通的 str 列表
    models: list[str] = Field(
        description="可用的LLM模型列表。",
        examples=[["qwen-turbo", "deepseek-chat", "deepseek-v4-flash"]]
    )
    default_agent: str = Field(
        description="未指定时使用的默认代理。",
        examples=["research-assistant"],
    )
    # 💡 核心修改 3：默认模型也替换为 str
    default_model: str = Field(
        description="未指定时使用的默认模型。",
        examples=["deepseek-v4-flash"]
    )


class UserInput(BaseModel):
    """代理的基本用户输入。"""

    message: str = Field(
        description="用户输入到代理的消息。",
        examples=["裙装原型的制版方法?"],
    )
    # 💡 核心修改 4：彻底移除了 SerializeAsAny[AllModelEnum]，直接用 str
    model: str | None = Field(
        title="模型",
        description="代理使用的LLM模型。默认为服务设置中设置的默认模型。",
        default=None,
        examples=["deepseek-chat", "qwen-turbo"],
    )
    thread_id: str | None = Field(
        description="用于持久化和继续多轮对话的线程ID。",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    user_id: str | None = Field(
        description="用于跨多个线程持久化和继续对话的用户ID。",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    agent_config: dict[str, Any] = Field(
        description="传递给代理的额外配置。",
        default={},
        examples=[{"spicy_level": 0.8}],
    )


class StreamInput(UserInput):
    """用于流式传输代理响应的用户输入。"""

    stream_tokens: bool = Field(
        description="是否将LLM令牌流式传输到客户端。",
        default=True,
    )


class ToolCall(TypedDict):
    """表示调用工具的请求。"""

    name: str
    """要调用的工具名称。"""
    args: dict[str, Any]
    """工具调用的参数。"""
    id: str | None
    """与工具调用关联的标识符。"""
    type: NotRequired[Literal["tool_call"]]


class ChatMessage(BaseModel):
    """聊天中的消息。"""

    type: Literal["human", "ai", "tool", "custom"] = Field(
        description="消息的角色。",
        examples=["human", "ai", "tool", "custom"],
    )
    content: str = Field(
        description="消息的内容。",
        examples=["Hello, world!"],
    )
    tool_calls: list[ToolCall] = Field(
        description="消息中的工具调用。",
        default=[],
    )
    tool_call_id: str | None = Field(
        description="此消息正在响应的工具调用。",
        default=None,
        examples=["call_Jja7J89XsjrOLA5r!MEOW!SL"],
    )
    run_id: str | None = Field(
        description="消息的运行ID。",
        default=None,
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    response_metadata: dict[str, Any] = Field(
        description="响应元数据。例如：响应头、logprobs、令牌计数。",
        default={},
    )
    custom_data: dict[str, Any] = Field(
        description="自定义消息数据。",
        default={},
    )

    def pretty_repr(self) -> str:
        """获取消息的漂亮表示形式。"""
        base_title = self.type.title() + " Message"
        padded = " " + base_title + " "
        sep_len = (80 - len(padded)) // 2
        sep = "=" * sep_len
        second_sep = sep + "=" if len(padded) % 2 else sep
        title = f"{sep}{padded}{second_sep}"
        return f"{title}\n\n{self.content}"

    def pretty_print(self) -> None:
        """打印消息的漂亮表示形式。"""
        print(self.pretty_repr())  # noqa: T201


class Feedback(BaseModel):  # type: ignore[no-redef]
    """用于记录到LangSmith的运行反馈。"""

    run_id: str = Field(
        description="要记录反馈的运行ID。",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )
    key: str = Field(
        description="反馈键。",
        examples=["human-feedback-stars"],
    )
    score: float = Field(
        description="反馈分数。",
        examples=[0.8],
    )
    kwargs: dict[str, Any] = Field(
        description="传递给LangSmith的额外反馈参数。",
        default={},
        examples=[{"comment": "内联人工反馈"}],
    )


class FeedbackResponse(BaseModel):
    """反馈响应。"""

    status: Literal["success"] = "success"


class ChatHistoryInput(BaseModel):
    """用于检索聊天历史的输入。"""

    thread_id: str = Field(
        description="用于持久化和继续多轮对话的线程ID。",
        examples=["847c6285-8fc9-4560-a83f-4e6285809254"],
    )


class ChatHistory(BaseModel):
    """聊天历史。"""

    messages: list[ChatMessage]
