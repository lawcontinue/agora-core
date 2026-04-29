"""
先例数据库 — 纯 Python Jaccard 相似度实现（不依赖 sklearn/numpy）

版本: agora-core 0.1.0
原始作者: 忒弥斯 (T-Mind) 🔮 + Code 💻
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Precedent:
    """先例记录"""
    decision_id: str
    description: str
    category: str
    outcome: str  # approved / rejected / escalated
    reasoning: str
    weight: float = 1.0
    created_at: float = 0.0
    keywords: List[str] = None

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()
        if self.keywords is None:
            self.keywords = self._extract_keywords(self.description)

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """简单的关键词提取（按空格分词 + 去重）"""
        # 支持中英文：按空格和常见标点分割
        import re
        tokens = re.findall(r'[a-zA-Z0-9\u4e00-\u9fff]+', text.lower())
        return list(set(tokens))


def jaccard_similarity(set_a: set, set_b: set) -> float:
    """Jaccard 相似度"""
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0


class PrecedentDatabase:
    """先例数据库（纯 Python，无外部依赖）"""

    def __init__(self, store_path: str = ""):
        self._precedents: List[Precedent] = []
        self._store_path = Path(store_path) if store_path else None
        if self._store_path and self._store_path.exists():
            self._load()

    def add(self, precedent: Precedent):
        self._precedents.append(precedent)
        self._save()

    def search(
        self,
        query: str,
        top_k: int = 5,
        threshold: float = 0.1,
    ) -> List[Tuple[Precedent, float]]:
        """搜索相似先例（Jaccard 相似度）"""
        query_tokens = set(Precedent._extract_keywords(query))
        scored = []
        for p in self._precedents:
            sim = jaccard_similarity(query_tokens, set(p.keywords))
            if sim >= threshold:
                scored.append((p, sim))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def get_by_id(self, decision_id: str) -> Optional[Precedent]:
        for p in self._precedents:
            if p.decision_id == decision_id:
                return p
        return None

    def count(self) -> int:
        return len(self._precedents)

    def _load(self):
        try:
            data = json.loads(self._store_path.read_text())
            for item in data:
                self._precedents.append(Precedent(**item))
        except Exception as e:
            logger.warning(f"Failed to load precedents: {e}")

    def _save(self):
        if not self._store_path:
            return
        try:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            data = [asdict(p) for p in self._precedents]
            self._store_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save precedents: {e}")
