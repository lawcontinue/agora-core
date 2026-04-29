"""
Agora Agent 基类 — 抽象接口（不绑定任何运行时）

作者: 忒弥斯 (T-Mind) 🔮
版本: agora-core 0.1.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class AgentErrorCode(Enum):
    UNKNOWN = "UNKNOWN"
    TIMEOUT = "TIMEOUT"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass
class AgentResponse:
    """Agent 响应"""
    content: str
    confidence: float
    reasoning: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    error_code: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: str = ""

    def is_success(self) -> bool:
        return self.error is None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "metadata": self.metadata,
            "error": self.error,
            "error_code": self.error_code,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
        }


class BaseAgent(ABC):
    """
    Agent 基类（抽象接口）

    子类必须实现:
    - think(): 同步思考
    - think_async(): 异步思考
    - get_capabilities(): 返回能力列表
    """

    def __init__(self, agent_id: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id or self.__class__.__name__
        self.config = config or {}

    @property
    def name(self) -> str:
        return self.agent_id

    @abstractmethod
    def think(self, query: str, context: Dict[str, Any]) -> AgentResponse:
        """同步思考并生成响应"""
        ...

    @abstractmethod
    async def think_async(self, query: str, context: Dict[str, Any]) -> AgentResponse:
        """异步思考并生成响应"""
        ...

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """获取能力列表"""
        ...
