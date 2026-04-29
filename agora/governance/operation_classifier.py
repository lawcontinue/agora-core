"""
操作分级器（Operation Classifier）- Default-deny P0 操作

版本: agora-core 0.1.0
原始作者: 家族研讨会 #37 决议，Code 💻 + Crit ⚖️
"""

import re
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


@dataclass
class OperationRisk:
    level: RiskLevel
    matched_pattern: Optional[str] = None
    matched_category: Optional[str] = None
    default_action: str = "allow"
    requires_audit: bool = False
    reasoning: str = ""


@dataclass
class RiskPattern:
    pattern: str
    category: str
    level: RiskLevel
    use_regex: bool = False


# 默认 P0 模式
_DEFAULT_P0_PATTERNS = [
    RiskPattern("delete", "data_destruction", RiskLevel.P0),
    RiskPattern("drop", "data_destruction", RiskLevel.P0),
    RiskPattern("rm -rf", "data_destruction", RiskLevel.P0),
    RiskPattern("force", "force_operation", RiskLevel.P0),
    RiskPattern("override", "config_override", RiskLevel.P0),
    RiskPattern("sudo", "privilege_escalation", RiskLevel.P0),
]

_DEFAULT_P1_PATTERNS = [
    RiskPattern("deploy", "deployment", RiskLevel.P1),
    RiskPattern("publish", "release", RiskLevel.P1),
    RiskPattern("merge", "code_merge", RiskLevel.P1),
    RiskPattern("push", "git_push", RiskLevel.P1),
]


class OperationClassifier:
    """操作分级器"""

    def __init__(self, patterns: Optional[List[RiskPattern]] = None):
        self.p0_patterns = []
        self.p1_patterns = []
        for p in (patterns or (_DEFAULT_P0_PATTERNS + _DEFAULT_P1_PATTERNS)):
            if p.level == RiskLevel.P0:
                self.p0_patterns.append(p)
            elif p.level == RiskLevel.P1:
                self.p1_patterns.append(p)

    def classify(self, decision: Dict) -> OperationRisk:
        desc = str(decision.get("description", "")) + " " + str(decision.get("action", ""))
        desc_lower = desc.lower()

        for p in self.p0_patterns:
            if (p.use_regex and re.search(p.pattern, desc_lower)) or (not p.use_regex and p.pattern in desc_lower):
                return OperationRisk(
                    level=RiskLevel.P0,
                    matched_pattern=p.pattern,
                    matched_category=p.category,
                    default_action="deny",
                    requires_audit=True,
                    reasoning=f"匹配 P0 模式: {p.pattern} (category={p.category})",
                )

        for p in self.p1_patterns:
            if (p.use_regex and re.search(p.pattern, desc_lower)) or (not p.use_regex and p.pattern in desc_lower):
                return OperationRisk(
                    level=RiskLevel.P1,
                    matched_pattern=p.pattern,
                    matched_category=p.category,
                    default_action="allow",
                    requires_audit=True,
                    reasoning=f"匹配 P1 模式: {p.pattern} (category={p.category})",
                )

        return OperationRisk(
            level=RiskLevel.P2,
            default_action="allow",
            reasoning="未匹配任何风险模式，默认 P2",
        )
