"""
Global Crits 投票机制（增强版）- 分层治理架构 v2.0

版本: v2.1 (agora-core 0.1.0)
原始作者: 忒弥斯 (T-Mind) 🔮 + 家族协作
更新日期: 2026-03-20

核心机制:
1. 简单多数规则（2/3 通过）
2. 投票分裂处理（1-1-1 升级 T-Mind）
3. 异常处理（独立 try-except）
"""

from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import logging

from agora.agents.crits.global_crit import GlobalCrit, Vote, VoteDecision


class FinalDecision(Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


class VotingResult:
    """投票结果"""

    def __init__(
        self,
        votes: List[Vote],
        approve: int,
        reject: int,
        abstain: int,
        final_decision: FinalDecision,
        timestamp: datetime,
        errors: Optional[List[str]] = None,
    ):
        self.votes = votes
        self.approve = approve
        self.reject = reject
        self.abstain = abstain
        self.final_decision = final_decision
        self.timestamp = timestamp
        self.errors = errors or []

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def is_approved(self) -> bool:
        return self.final_decision == FinalDecision.APPROVED

    def is_rejected(self) -> bool:
        return self.final_decision == FinalDecision.REJECTED

    def is_escalated(self) -> bool:
        return self.final_decision == FinalDecision.ESCALATED

    def to_dict(self) -> Dict:
        return {
            "votes": [v.to_dict() for v in self.votes],
            "approve": self.approve,
            "reject": self.reject,
            "abstain": self.abstain,
            "final_decision": self.final_decision.value,
            "timestamp": self.timestamp.isoformat(),
            "errors": self.errors,
        }


class GlobalCritVoting:
    """
    Global Crits 投票机制

    - 3 个 Global Crits
    - 2/3 多数通过
    - 1-1-1 分裂升级 T-Mind
    """

    def __init__(self, crits: List[GlobalCrit]):
        if len(crits) != 3:
            raise ValueError(f"必须有 3 个 Global Crits，实际: {len(crits)}")
        self.crits = crits
        self.threshold = 2 / 3
        self.logger = logging.getLogger(__name__)

    def vote(self, decision: Dict) -> VotingResult:
        """执行投票"""
        votes: List[Vote] = []
        errors: List[str] = []

        for i, crit in enumerate(self.crits, start=1):
            try:
                vote = crit.review_decision(decision)
                votes.append(vote)
            except Exception as e:
                self.logger.error(f"Global Crit {i} 投票失败: {e}")
                errors.append(f"Global Crit {i}: {e}")
                votes.append(Vote(
                    crit_id=i,
                    decision=VoteDecision.ABSTAIN,
                    reasoning=f"投票异常: {e}",
                    timestamp=datetime.now(),
                    precedents_cited=[],
                ))

        approve = sum(1 for v in votes if v.decision == VoteDecision.APPROVE)
        reject = sum(1 for v in votes if v.decision == VoteDecision.REJECT)
        abstain = sum(1 for v in votes if v.decision == VoteDecision.ABSTAIN)

        if approve >= 2:
            final = FinalDecision.APPROVED
        elif reject >= 2:
            final = FinalDecision.REJECTED
        else:
            final = FinalDecision.ESCALATED

        return VotingResult(
            votes=votes,
            approve=approve,
            reject=reject,
            abstain=abstain,
            final_decision=final,
            timestamp=datetime.now(),
            errors=errors,
        )

    def get_voting_summary(self, result: VotingResult) -> str:
        summary = f"投票结果: {result.approve}-{result.reject}-{result.abstain}"
        if result.has_errors():
            summary += f" ⚠️ ({len(result.errors)} 个错误)"
        if result.is_approved():
            summary += " → ✅ 批准"
        elif result.is_rejected():
            summary += " → ❌ 拒绝"
        elif result.is_escalated():
            summary += " → ⬆️ 升级 T-Mind"
        return summary
