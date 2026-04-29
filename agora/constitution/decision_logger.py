"""
决策记录器

版本: agora-core 0.1.0
原始作者: 忒弥斯 (T-Mind)
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class DecisionLogger:
    """决策记录器（JSONL 格式）"""

    def __init__(self, log_file: str = ""):
        self.log_file = Path(log_file) if log_file else Path("/tmp/agora_decision_log.jsonl")
        self.decisions: List[Dict] = []
        if self.log_file.exists():
            self._load()

    def _load(self):
        try:
            for line in self.log_file.read_text().strip().split("\n"):
                if line.strip():
                    self.decisions.append(json.loads(line))
        except Exception:
            pass

    def record(
        self,
        decision: str,
        participants: List[str],
        reasoning: str,
        crit_veto: bool = False,
        veto_reason: str = "",
        context: Optional[Dict] = None,
    ) -> str:
        import uuid
        entry_id = uuid.uuid4().hex[:12]
        entry = {
            "id": entry_id,
            "decision": decision,
            "participants": participants,
            "reasoning": reasoning,
            "crit_veto": crit_veto,
            "veto_reason": veto_reason,
            "context": context or {},
            "timestamp": datetime.now().isoformat(),
        }
        self.decisions.append(entry)
        self._append(entry)
        return entry_id

    def _append(self, entry: Dict):
        try:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def get_recent(self, limit: int = 10) -> List[Dict]:
        return self.decisions[-limit:]

    def count(self) -> int:
        return len(self.decisions)
