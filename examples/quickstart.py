#!/usr/bin/env python3
"""
Agora-core Quickstart — 3 Agent 投票 + 一票否决演示

版本: agora-core 0.1.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agora.governance.governance_layer import GovernanceLayer
from agora.agents.crits.local_crit import LocalCrit, ReviewDecision


# --- 自定义 Local Crit（模拟一票否决）---
class VetoCrit(LocalCrit):
    """模拟一个总是否决的 Crit"""

    def __init__(self):
        super().__init__(name="VetoCrit", role="veto_officer")

    def _analyze(self, task):
        return {
            "decision": ReviewDecision.REJECT,
            "reasoning": "P0 安全风险：检测到不可信操作，行使一票否决权",
            "confidence": 1.0,
        }


class ApproveCrit(LocalCrit):
    """总是批准的 Crit"""

    def __init__(self):
        super().__init__(name="ApproveCrit", role="approver")

    def _analyze(self, task):
        return {
            "decision": ReviewDecision.APPROVE,
            "reasoning": "操作符合所有标准",
            "confidence": 0.95,
        }


# --- 场景 1：正常批准 ---
def demo_normal_approval():
    print("=" * 60)
    print("📋 场景 1: 正常操作 — Local Crits 全部批准")
    print("=" * 60)

    gov = GovernanceLayer()
    gov.register_local_crit(ApproveCrit())

    decision = {
        "task_id": "TASK_001",
        "description": "更新 README 文档",
        "agent": "Code",
        "action": "update docs",
    }

    result = gov.review_decision(decision)
    print(f"决策 ID: {result.decision_id}")
    print(f"阶段: {result.stage.value}")
    print(f"结果: {'✅ 批准' if result.approved else '❌ 拒绝'}")
    print(f"理由: {result.reasoning}")
    print()


# --- 场景 2：一票否决 ---
def demo_veto():
    print("=" * 60)
    print("🛡️ 场景 2: 一票否决 — VetoCrit 检测到 P0 风险")
    print("=" * 60)

    gov = GovernanceLayer()
    gov.register_local_crit(ApproveCrit())
    gov.register_local_crit(VetoCrit())

    decision = {
        "task_id": "TASK_002",
        "description": "删除生产数据库",
        "agent": "Admin",
        "action": "delete production database",
    }

    result = gov.review_decision(decision)
    print(f"决策 ID: {result.decision_id}")
    print(f"阶段: {result.stage.value}")
    print(f"结果: {'✅ 批准' if result.approved else '❌ 拒绝'}")
    print(f"理由: {result.reasoning}")
    print()

    # 打印各 Crit 投票详情
    for name, review in result.local_reviews.items():
        print(f"  {name}: {review.get('decision', '?')} — {review.get('reasoning', '')}")
    print()


# --- 场景 3：Global Crits 投票分裂 ---
def demo_split_vote():
    print("=" * 60)
    print("⚖️ 场景 3: Local 冲突 → Global Crits 投票")
    print("=" * 60)

    gov = GovernanceLayer()
    # 只有 ApproveCrit，没有冲突 → 直接批准
    # 加一个会 reject（非 P0）的 crit 制造冲突
    class CautiousCrit(LocalCrit):
        def __init__(self):
            super().__init__(name="CautiousCrit", role="caution_officer")

        def _analyze(self, task):
            return {
                "decision": ReviewDecision.REJECT,
                "reasoning": "谨慎起见，建议延迟执行",
                "confidence": 0.7,
            }

    gov.register_local_crit(ApproveCrit())
    gov.register_local_crit(CautiousCrit())

    decision = {
        "task_id": "TASK_003",
        "description": "部署新版本到生产环境",
        "agent": "DevOps",
        "action": "deploy production",
    }

    result = gov.review_decision(decision)
    print(f"决策 ID: {result.decision_id}")
    print(f"阶段: {result.stage.value}")
    print(f"结果: {'✅ 批准' if result.approved else '❌ 拒绝'}")
    print(f"理由: {result.reasoning}")

    if result.global_votes:
        print(f"\n  Global Crits 投票详情:")
        for v in result.global_votes.get("votes", []):
            print(f"    Crit {v['crit_id']}: {v['decision']} — {v['reasoning']}")
    print()


if __name__ == "__main__":
    demo_normal_approval()
    demo_veto()
    demo_split_vote()
    print("🎉 所有场景演示完成！")
