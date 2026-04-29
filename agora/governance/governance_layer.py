"""
治理层（Governance Layer）- 分层治理架构 v2.1

版本: agora-core 0.1.0
原始作者: 忒弥斯 (T-Mind) 🔮 + 家族协作
实施: Code 💻

工作流:
1. 操作风险分级（P0/P1/P2）
2. Local Crits 审查
3. Global Crits 投票
4. T-Mind 最终决策（1-1-1 分裂时）
"""

import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

from agora.agents.crits.local_crit import LocalCrit, ReviewResult, ReviewDecision
from agora.agents.crits.global_crit import GlobalCrit
from agora.governance.voting import GlobalCritVoting, FinalDecision
from agora.governance.operation_classifier import OperationClassifier, RiskLevel
from agora.governance.operation_trust import TrustManager
from agora.governance.hitl_escalation import HITLEscalation

logger = logging.getLogger(__name__)


class GovernanceStage(Enum):
    LOCAL_REVIEW = "local_review"
    GLOBAL_VOTING = "global_voting"
    TMIND_DECISION = "tmind_decision"
    COMPLETED = "completed"


@dataclass
class GovernanceResult:
    approved: bool
    stage: GovernanceStage
    local_reviews: Dict
    global_votes: Optional[Dict]
    tmind_decision: Optional[Dict]
    decision_id: str
    reasoning: str
    token_cost: int
    duration_ms: float

    def to_dict(self) -> Dict:
        return asdict(self)


class GovernanceLayer:
    """
    治理层

    职责:
    1. Local Crits 审查
    2. Global Crits 投票
    3. T-Mind 最终决策
    4. 决策日志
    """

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger("agora.governance")

        self.classifier = OperationClassifier()
        self.trust_manager = TrustManager()
        self.hitl = HITLEscalation()

        self.local_crits: Dict[str, LocalCrit] = {}
        self.global_crits: List[GlobalCrit] = [GlobalCrit(i) for i in range(1, 4)]
        self.voting = GlobalCritVoting(self.global_crits)

        self.decision_log_path = Path(
            self.config.get("decision_log_path", "/tmp/agora_decisions.jsonl")
        )
        self.decision_log_path.parent.mkdir(parents=True, exist_ok=True)

    def register_local_crit(self, crit: LocalCrit):
        self.local_crits[crit.name] = crit

    def review_decision(self, decision: Dict, enable_governance: bool = True) -> GovernanceResult:
        start = time.time()
        decision_id = f"DEC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if not enable_governance:
            return GovernanceResult(
                approved=True, stage=GovernanceStage.COMPLETED,
                local_reviews={}, global_votes=None, tmind_decision=None,
                decision_id=decision_id, reasoning="治理层未启用",
                token_cost=0, duration_ms=(time.time() - start) * 1000,
            )

        # 操作风险分级
        risk = self.classifier.classify(decision)
        logger.info(f"[{decision_id}] Risk: {risk.level.value}")

        if risk.level == RiskLevel.P0:
            category = risk.matched_category or "unknown"
            can_auto, trust_score = self.trust_manager.check_trust(category)
            if not can_auto:
                result = GovernanceResult(
                    approved=False, stage=GovernanceStage.COMPLETED,
                    local_reviews={"risk": {"level": "P0", "category": category, "trust_score": trust_score}},
                    global_votes=None, tmind_decision=None,
                    decision_id=decision_id,
                    reasoning=f"P0 需人工确认 (信任分={trust_score}，需 ≥3)",
                    token_cost=0, duration_ms=(time.time() - start) * 1000,
                )
                self._log_decision(result)
                return result

        # Local Crits
        local_result = self._local_review(decision, decision_id)

        if local_result["has_p0_issues"]:
            result = GovernanceResult(
                approved=False, stage=GovernanceStage.LOCAL_REVIEW,
                local_reviews=local_result["reviews"],
                global_votes=None, tmind_decision=None,
                decision_id=decision_id, reasoning=local_result["p0_summary"],
                token_cost=local_result["token_cost"],
                duration_ms=(time.time() - start) * 1000,
            )
            self._log_decision(result)
            return result

        if local_result["has_conflicts"]:
            global_result = self._global_voting(decision, decision_id)

            if global_result["final_decision"] == FinalDecision.ESCALATED:
                tmind = self._tmind_decision(decision, decision_id, local_result, global_result)
                result = GovernanceResult(
                    approved=tmind["approved"], stage=GovernanceStage.TMIND_DECISION,
                    local_reviews=local_result["reviews"],
                    global_votes=global_result, tmind_decision=tmind,
                    decision_id=decision_id, reasoning=tmind["reasoning"],
                    token_cost=local_result["token_cost"],
                    duration_ms=(time.time() - start) * 1000,
                )
            else:
                approved = global_result["final_decision"] == FinalDecision.APPROVED
                result = GovernanceResult(
                    approved=approved, stage=GovernanceStage.GLOBAL_VOTING,
                    local_reviews=local_result["reviews"],
                    global_votes=global_result, tmind_decision=None,
                    decision_id=decision_id, reasoning=global_result["reasoning"],
                    token_cost=local_result["token_cost"],
                    duration_ms=(time.time() - start) * 1000,
                )
        else:
            result = GovernanceResult(
                approved=True, stage=GovernanceStage.LOCAL_REVIEW,
                local_reviews=local_result["reviews"],
                global_votes=None, tmind_decision=None,
                decision_id=decision_id, reasoning=local_result["reasoning"],
                token_cost=local_result["token_cost"],
                duration_ms=(time.time() - start) * 1000,
            )

        self._log_decision(result)
        return result

    def _local_review(self, decision: Dict, decision_id: str) -> Dict:
        reviews = {}
        has_p0 = False
        has_conflicts = False
        token_cost = 0
        p0_list = []

        for name, crit in self.local_crits.items():
            try:
                r = crit.review(decision)
                reviews[name] = r.to_dict()
                token_cost += r.token_cost
                if r.decision == ReviewDecision.REJECT:
                    if "P0" in r.reasoning or "p0" in r.reasoning:
                        has_p0 = True
                        p0_list.append({"crit": name, "reason": r.reasoning})
                    else:
                        has_conflicts = True
            except Exception as e:
                reviews[name] = {"error": str(e), "decision": "error"}

        if not self.local_crits:
            return {"reviews": {}, "has_p0_issues": False, "has_conflicts": False, "token_cost": 0, "reasoning": "无 Local Crits"}

        summary = f"发现 {len(p0_list)} 个 P0 问题" if has_p0 else ("有冲突，升级 Global" if has_conflicts else "全部批准")
        return {
            "reviews": reviews, "has_p0_issues": has_p0, "has_conflicts": has_conflicts,
            "token_cost": token_cost, "p0_summary": summary,
            "reasoning": f"Local Crits: {summary}",
        }

    def _global_voting(self, decision: Dict, decision_id: str) -> Dict:
        try:
            result = self.voting.vote(decision)
            return {
                "final_decision": result.final_decision,
                "votes": [v.to_dict() for v in result.votes],
                "approve": result.approve, "reject": result.reject, "abstain": result.abstain,
                "reasoning": f"Global Crits: {result.final_decision.value}",
                "token_cost": 15000, "errors": result.errors,
            }
        except Exception as e:
            return {
                "final_decision": FinalDecision.ESCALATED, "votes": [],
                "approve": 0, "reject": 0, "abstain": 0,
                "reasoning": f"投票失败: {e}", "token_cost": 0, "errors": [str(e)],
            }

    def _tmind_decision(self, decision: Dict, decision_id: str, local: Dict, global_r: Dict) -> Dict:
        return {
            "approved": True,
            "reasoning": "T-Mind 最终决策：批准（简化实现）",
            "token_cost": 0,
            "timestamp": datetime.now().isoformat(),
        }

    def _log_decision(self, result: GovernanceResult):
        try:
            entry = {
                "decision_id": result.decision_id,
                "timestamp": datetime.now().isoformat(),
                "approved": result.approved,
                "stage": result.stage.value,
                "reasoning": result.reasoning,
            }
            with open(self.decision_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")
