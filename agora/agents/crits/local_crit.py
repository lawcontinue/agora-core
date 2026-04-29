"""
Local Crit（领域专家）- 分层治理架构 v2.0

版本: agora-core 0.1.0
原始作者: 忒弥斯 (T-Mind) 🔮
"""

from datetime import datetime
from typing import Dict, Optional
from enum import Enum


class ReviewDecision(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class ReviewResult:
    """审查结果"""

    def __init__(
        self,
        agent_name: str,
        decision: ReviewDecision,
        reasoning: str,
        timestamp: datetime,
        token_cost: int = 0,
    ):
        self.agent_name = agent_name
        self.decision = decision
        self.reasoning = reasoning
        self.timestamp = timestamp
        self.token_cost = token_cost

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "decision": self.decision.value,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "token_cost": self.token_cost,
        }


class LocalCrit:
    """
    Local Crit（领域专家）

    子类可以覆盖 _analyze() 实现自定义审查逻辑。
    """

    def __init__(
        self,
        name: str,
        role: str,
        timeout: int = 900,
        token_cost: int = 1000,
    ):
        self.name = name
        self.role = role
        self.timeout = timeout
        self.token_cost = token_cost

    def review(self, task: Dict) -> ReviewResult:
        if not self._validate_task(task):
            return ReviewResult(
                agent_name=self.name,
                decision=ReviewDecision.REJECT,
                reasoning="任务验证失败",
                timestamp=datetime.now(),
                token_cost=0,
            )

        analysis = self._analyze(task)
        cost = self.token_cost if analysis["decision"] == ReviewDecision.REJECT else 0
        return ReviewResult(
            agent_name=self.name,
            decision=analysis["decision"],
            reasoning=analysis["reasoning"],
            timestamp=datetime.now(),
            token_cost=cost,
        )

    def _validate_task(self, task: Dict) -> bool:
        required = ["task_id", "description", "agent"]
        return all(f in task for f in required)

    def _analyze(self, task: Dict) -> Dict:
        return {
            "decision": ReviewDecision.APPROVE,
            "reasoning": f"{self.name} 审查通过",
            "confidence": 0.8,
        }

    def can_override(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"LocalCrit(name={self.name}, role={self.role})"
