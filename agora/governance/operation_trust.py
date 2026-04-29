"""
渐进式信任管理器（Trust Manager）

版本: agora-core 0.1.0
原始作者: Aria 🎨 + 家族研讨会 #37
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TrustRecord:
    category: str
    trust_score: int = 0
    last_updated: float = 0.0
    total_confirmed: int = 0
    total_denied: int = 0
    total_auto_approved: int = 0

    DECAY_FACTOR = 0.8
    DECAY_INTERVAL = 86400.0
    AUTO_THRESHOLD = 3

    def maybe_decay(self):
        now = time.time()
        intervals = int((now - self.last_updated) / self.DECAY_INTERVAL)
        if intervals > 0 and self.trust_score > 0:
            self.trust_score = max(0, int(self.trust_score * (self.DECAY_FACTOR ** intervals)))
            self.last_updated = now

    def confirm(self) -> int:
        self.maybe_decay()
        self.trust_score += 1
        self.total_confirmed += 1
        self.last_updated = time.time()
        return self.trust_score

    def deny(self):
        self.trust_score = 0
        self.total_denied += 1
        self.last_updated = time.time()

    def record_auto_approve(self):
        self.total_auto_approved += 1
        self.last_updated = time.time()


class TrustManager:
    """渐进式信任管理器"""

    def __init__(self, store_path: str = ""):
        self._records: Dict[str, TrustRecord] = {}
        self._store_path = Path(store_path) if store_path else None
        if self._store_path and self._store_path.exists():
            self._load()

    def _load(self):
        try:
            data = json.loads(self._store_path.read_text())
            for k, v in data.items():
                self._records[k] = TrustRecord(**v)
        except Exception as e:
            logger.warning(f"Failed to load trust store: {e}")

    def _save(self):
        if not self._store_path:
            return
        try:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            data = {k: asdict(v) for k, v in self._records.items()}
            self._store_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save trust store: {e}")

    def _get(self, category: str) -> TrustRecord:
        if category not in self._records:
            self._records[category] = TrustRecord(category=category, last_updated=time.time())
        return self._records[category]

    def check_trust(self, category: str) -> Tuple[bool, int]:
        rec = self._get(category)
        rec.maybe_decay()
        return rec.trust_score >= rec.AUTO_THRESHOLD, rec.trust_score

    def confirm(self, category: str) -> int:
        rec = self._get(category)
        score = rec.confirm()
        self._save()
        return score

    def deny(self, category: str):
        rec = self._get(category)
        rec.deny()
        self._save()

    def record_auto_approve(self, category: str):
        rec = self._get(category)
        rec.record_auto_approve()
        self._save()

    def get_stats(self) -> Dict:
        return {k: asdict(v) for k, v in self._records.items()}
