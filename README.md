# agora-core

Multi-Agent 治理框架核心模块 — 投票、一票否决、先例系统、操作风险分级。

Core governance building blocks for multi-agent systems: voting with veto, precedent database, operation risk classification (P0/P1/P2), and human-in-the-loop escalation.

## Install

```bash
pip install -e .
```

## Quick Start

```bash
python examples/quickstart.py
```

## Key Concepts

- **Global Crit Voting**: 3-crit panel, 2/3 majority rule, 1-1-1 split escalates to T-Mind
- **Local Crits**: Domain-expert reviewers with veto power (15min timeout)
- **Veto (一票否决)**: Any crit can reject, P0 issues block immediately
- **Precedent DB**: Jaccard-similarity based precedent matching (pure Python, no sklearn)
- **Operation Classifier**: P0 default-deny / P1 allow+audit / P2 allow+log
- **HITL Escalation**: Human confirmation for high-risk operations

## License

Apache 2.0
