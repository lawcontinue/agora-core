"""
Global Crit（宪法法院）- 分层治理架构 v2.0

版本: agora-core 0.1.0
原始作者: 忒弥斯 (T-Mind) 🔮
验收: 家族全员（5/5 赞成，Crit A- 90/100）
"""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from .analyzer import DecisionAnalyzer


class VoteDecision(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"


class Vote:
    """投票结果"""

    def __init__(
        self,
        crit_id: int,
        decision: VoteDecision,
        reasoning: str,
        timestamp: datetime,
        precedents_cited: Optional[List[str]] = None,
    ):
        self.crit_id = crit_id
        self.decision = decision
        self.reasoning = reasoning
        self.timestamp = timestamp
        self.precedents_cited = precedents_cited or []

    def to_dict(self) -> Dict:
        return {
            "crit_id": self.crit_id,
            "decision": self.decision.value,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "precedents_cited": self.precedents_cited,
        }


class GlobalCrit:
    """
    Global Crit（宪法法院）

    职责:
    1. 审查决策（跨域冲突）
    2. 检索先例
    3. 投票决策
    """

    def __init__(self, crit_id: int):
        if crit_id not in (1, 2, 3):
            raise ValueError(f"crit_id 必须是 1, 2, 或 3，实际: {crit_id}")
        self.crit_id = crit_id
        self.name = f"Global Crit {crit_id}"
        self.analyzer = DecisionAnalyzer(crit_id)

    def review_decision(
        self,
        decision: Dict,
        precedents: Optional[List[Dict]] = None,
    ) -> Vote:
        if precedents is None:
            precedents = self.search_precedents(decision)

        analysis = self.analyze(decision, precedents)

        return Vote(
            crit_id=self.crit_id,
            decision=analysis["decision"],
            reasoning=analysis["reasoning"],
            timestamp=datetime.now(),
            precedents_cited=[p["decision_id"] for p in precedents],
        )

    def search_precedents(self, decision: Dict) -> List[Dict]:
        # Placeholder — agora-core 不含先例存储
        return []

    def analyze(self, decision: Dict, precedents: List[Dict]) -> Dict:
        analysis = self.analyzer.analyze(decision, precedents)
        decision_map = {
            "approve": VoteDecision.APPROVE,
            "reject": VoteDecision.REJECT,
            "abstain": VoteDecision.ABSTAIN,
        }
        return {
            "decision": decision_map.get(analysis["decision"], VoteDecision.ABSTAIN),
            "reasoning": analysis["reasoning"],
            "confidence": analysis["confidence"],
        }

    def __repr__(self) -> str:
        return f"GlobalCrit(id={self.crit_id})"
