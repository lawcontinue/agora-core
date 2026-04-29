"""
Global Crit 决策分析器 - 分层治理架构 v2.0

版本: agora-core 0.1.0
原始作者: 忒弥斯 (T-Mind) 🔮 + 家族协作

差异性机制:
- Crit 1: 保守（temperature 0.3）
- Crit 2: 平衡（temperature 0.7）
- Crit 3: 创新（temperature 1.0）
"""

from typing import Dict, List, Optional
from enum import Enum


class AnalysisLevel(Enum):
    LEVEL1_RULES = "level1_rules"
    LEVEL2_PRECEDENT = "level2_precedent"
    LEVEL3_LLM = "level3_llm"


class P0IssueType(Enum):
    SECURITY_VULNERABILITY = "security_vulnerability"
    PRIVACY_VIOLATION = "privacy_violation"
    COMPLIANCE_RISK = "compliance_risk"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CRITICAL_DEPENDENCY = "critical_dependency"


# P0 关键词检测规则
_P0_RULES = [
    (["删除", "delete", "drop", "rm"], P0IssueType.CRITICAL_DEPENDENCY),
    (["安全", "漏洞", "vulnerability", "exploit"], P0IssueType.SECURITY_VULNERABILITY),
    (["隐私", "privacy", "personal data"], P0IssueType.PRIVACY_VIOLATION),
    (["合规", "compliance", "regulation"], P0IssueType.COMPLIANCE_RISK),
    (["资源耗尽", "OOM", "exhaustion"], P0IssueType.RESOURCE_EXHAUSTION),
]


class DecisionAnalyzer:
    """
    Global Crit 决策分析器

    Level 1: 规则快速检查（无 LLM 调用）
    差异性通过不同的分析倾向实现
    """

    def __init__(self, crit_id: int):
        self.crit_id = crit_id
        self.temperature = {1: 0.3, 2: 0.7, 3: 1.0}.get(crit_id, 0.7)

    def analyze(self, decision: Dict, precedents: List[Dict]) -> Dict:
        """
        分析决策（纯规则引擎）

        Returns:
            {"decision": "approve"|"reject"|"abstain", "reasoning": str, "confidence": float, "level": AnalysisLevel}
        """
        desc = str(decision.get("description", "")) + " " + str(decision.get("action", ""))

        # Level 1: P0 关键词检测
        p0_issues = []
        for keywords, issue_type in _P0_RULES:
            if any(kw in desc.lower() for kw in keywords):
                p0_issues.append(issue_type)

        # 差异性分析
        if p0_issues:
            if self.crit_id == 1:
                # 保守：发现 P0 关键词即拒绝
                return {
                    "decision": "reject",
                    "reasoning": f"[保守分析] 检测到高风险关键词: {[e.value for e in p0_issues]}",
                    "confidence": 0.95,
                    "level": AnalysisLevel.LEVEL1_RULES,
                    "p0_issues": [e.value for e in p0_issues],
                }
            elif self.crit_id == 2:
                # 平衡：标记但倾向弃权
                return {
                    "decision": "abstain",
                    "reasoning": f"[平衡分析] 发现风险关键词，需更多上下文: {[e.value for e in p0_issues]}",
                    "confidence": 0.6,
                    "level": AnalysisLevel.LEVEL1_RULES,
                    "p0_issues": [e.value for e in p0_issues],
                }
            else:
                # 创新：可能批准但提醒风险
                return {
                    "decision": "approve",
                    "reasoning": f"[创新分析] 关键词匹配但可接受风险: {[e.value for e in p0_issues]}",
                    "confidence": 0.5,
                    "level": AnalysisLevel.LEVEL1_RULES,
                    "p0_issues": [e.value for e in p0_issues],
                }

        # 无风险关键词：全部批准
        return {
            "decision": "approve",
            "reasoning": f"[Crit {self.crit_id}] 规则检查通过，未发现风险",
            "confidence": 0.9,
            "level": AnalysisLevel.LEVEL1_RULES,
            "p0_issues": [],
        }
