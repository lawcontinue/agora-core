# agora-core

[![PyPI](https://img.shields.io/pypi/v/agora-core.svg)](https://pypi.org/project/agora-core/)
[![Python](https://img.shields.io/pypi/pyversions/agora-core.svg)](https://pypi.org/project/agora-core/)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-67%2F67-green.svg)]()

**Governance primitives for multi-agent systems.**

When your AI agents make decisions together — who votes? Who can veto? How do you prevent cascading failures? Most frameworks assume a single "boss agent" orchestrates everything. **Agora takes a different approach: democratic governance.**

> *"In 48-agent production runs, we observed 19-day periods where every agent reported healthy telemetry — but the goal had quietly drifted."* — [AutoGen #7487](https://github.com/microsoft/autogen/issues/7487)

## Why governance?

Multi-agent systems without governance suffer from:
- **Goal drift**: Agents individually succeed but collectively diverge from the original intent
- **Cascading failures**: One agent's error propagates unchecked through the chain
- **No accountability**: When things go wrong, there's no decision trail to audit
- **Budget explosion**: Agent A spawns B×5, each spawns C×5 — costs spiral in seconds

Policy engines like [AGT](https://github.com/imran-siddique/agent-governance-toolkit) solve the *top-down compliance* problem (Cedar policies, identity verification). **Agora solves the *collective decision-making* problem.**

## What's included

| Module | What it does |
|--------|-------------|
| **Voting** | 3-crit panel, 2/3 majority, 1-1-1 split escalates to human |
| **Veto (一票否决)** | Any crit can reject; P0 issues block immediately |
| **Precedent DB** | Jaccard-similarity matching on past decisions (pure Python, zero dependencies) |
| **Operation Classifier** | P0 default-deny / P1 allow+audit / P2 allow+log |
| **HITL Escalation** | Human-in-the-loop for high-risk operations |
| **Constitution** | Decision logging + validation against constitutional rules |

### Agora vs AGT vs built-in guardrails

| | Agora | AGT | Framework guardrails |
|---|---|---|---|
| **Approach** | Democratic (voting, veto, precedent) | Top-down (Cedar policies) | Per-agent hooks |
| **Veto power** | ✅ Any crit can block | ❌ Policy pass/fail | ❌ |
| **Precedent system** | ✅ Learns from past decisions | ❌ | ❌ |
| **Constitution** | ✅ | ✅ (Cedar) | ❌ |
| **Human escalation** | ✅ Built-in | ✅ | ⚠️ Manual |
| **Dependencies** | Zero | Cedar SDK | Varies |
| **Best for** | Multi-agent collaboration decisions | Enterprise compliance | Single-agent safety |

## Install

```bash
pip install agora-core

# Or from source
git clone https://github.com/lawcontinue/agora-core.git
cd agora-core && pip install -e .
```

## Quick Start

```python
from agora.governance.governance_layer import GovernanceLayer
from agora.agents.crits.local_crit import LocalCrit, ReviewDecision

# Define a crit (reviewer agent)
class SafetyCrit(LocalCrit):
    def _analyze(self, task):
        if "delete" in task["action"].lower():
            return {"decision": ReviewDecision.REJECT,
                    "reasoning": "P0: destructive operation blocked",
                    "confidence": 1.0}
        return {"decision": ReviewDecision.APPROVE,
                "reasoning": "Operation safe",
                "confidence": 0.9}

# Set up governance
gov = GovernanceLayer()
gov.register_local_crit(SafetyCrit())

# Review a decision
result = gov.review_decision({
    "task_id": "TASK_001",
    "description": "Drop user table",
    "agent": "AdminAgent",
    "action": "delete users"
})

print(result.approved)   # False — veto triggered
print(result.reasoning)  # "P0: destructive operation blocked"
```

Run the full demo:

```bash
python examples/quickstart.py
```

## Architecture

```
                    ┌──────────────┐
                    │  Governance  │
                    │    Layer     │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Local   │ │  Local   │ │  Local   │
        │  Crit A  │ │  Crit B  │ │  Crit C  │
        └──────────┘ └──────────┘ └──────────┘
              │            │            │
              └─────┬──────┘────────────┘
                    ▼
            ┌──────────────┐
            │   Consensus  │ ← 2/3 majority
            │   reached?   │
            └──┬───────┬───┘
               │       │
            Yes ▼    No ▼
          Approve  ┌──────────────┐
                   │ Global Crits │ ← 3-crit panel
                   │   Voting     │    tie-break
                   └──────┬───────┘
                          ▼
                   ┌──────────────┐
                   │ HITL         │ ← Human escalation
                   │ (1-1-1 split)│    if needed
                   └──────────────┘
```

## API Overview

### GovernanceLayer

Central orchestrator. Register crits, review decisions, query precedents.

```python
gov = GovernanceLayer()
gov.register_local_crit(MyCrit())

result = gov.review_decision(decision_dict)
result.approved       # bool
result.reasoning      # str
result.local_reviews  # dict of crit responses
result.global_votes   # dict if escalated
```

### LocalCrit

Base class for domain-expert reviewers with veto power.

```python
class MyCrit(LocalCrit):
    def _analyze(self, task) -> dict:
        return {
            "decision": ReviewDecision.APPROVE | ReviewDecision.REJECT,
            "reasoning": "...",
            "confidence": 0.0-1.0
        }
```

### PrecedentDB

Find similar past decisions using Jaccard similarity.

```python
from agora.governance.precedent_db import PrecedentDB

db = PrecedentDB()
db.add_precedent("PRJ-001", tags=["safety", "delete"], outcome="rejected")
matches = db.find_similar(tags=["safety", "remove"])  # → [("PRJ-001", 0.5)]
```

### OperationClassifier

Classify operations by risk level.

```python
from agora.governance.operation_classifier import OperationClassifier

classifier = OperationClassifier()
level = classifier.classify("rm -rf /")  # → RiskLevel.P0 (default-deny)
```

## Design Principles

1. **Veto over consensus** — One strong objection beats weak agreement
2. **Precedent over rules** — Learn from past decisions, don't just follow static rules
3. **Default-deny for P0** — Destructive operations are blocked unless explicitly approved
4. **Zero dependencies** — Pure Python. No sklearn, no Cedar, no LLM required for core logic
5. **Framework-agnostic** — Works with AutoGen, CrewAI, LangGraph, or any agent system

## Production Stats

Battle-tested with a 7-agent team across 190+ governance decisions. Zero safety incidents. Every decision logged, every veto recorded, every precedent retrievable.

## License

Apache 2.0 — see [LICENSE](LICENSE).

## Credits

Built by [lawcontinue](https://github.com/lawcontinue) with the T-Mind agent family. Production-validated alongside [Hippo](https://github.com/lawcontinue/hippo) distributed inference.
