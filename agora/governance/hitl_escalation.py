"""
HITL Escalation — Human-in-the-Loop 升级机制

版本: agora-core 0.1.0
原始作者: Shield 🛡️ + 家族研讨会 #37
"""

import time
import uuid
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class HITLStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"


@dataclass
class HITLRequest:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    decision: Dict = field(default_factory=dict)
    risk_level: str = ""
    risk_category: str = ""
    status: HITLStatus = HITLStatus.PENDING
    created_at: float = field(default_factory=time.time)
    resolved_at: Optional[float] = None
    timeout_seconds: int = 300
    reasoning: str = ""

    def is_expired(self) -> bool:
        return (
            self.status == HITLStatus.PENDING
            and (time.time() - self.created_at) > self.timeout_seconds
        )


class HITLResult:
    """HITL 处理结果"""
    def __init__(self, approved: bool, request_id: str, status: HITLStatus, reasoning: str = ""):
        self.approved = approved
        self.request_id = request_id
        self.status = status
        self.reasoning = reasoning


class HITLEscalation:
    """HITL 升级机制"""

    def __init__(self, default_timeout: int = 300, store_path: str = ""):
        self.default_timeout = default_timeout
        self._store_path = Path(store_path) if store_path else None
        self._pending: Dict[str, HITLRequest] = {}

    def submit(self, decision: Dict, risk_level: str, risk_category: str, reasoning: str = "") -> HITLRequest:
        req = HITLRequest(
            decision=decision,
            risk_level=risk_level,
            risk_category=risk_category,
            timeout_seconds=self.default_timeout,
            reasoning=reasoning,
        )
        self._pending[req.id] = req
        return req

    def resolve(self, request_id: str, approved: bool) -> HITLResult:
        req = self._pending.get(request_id)
        if not req:
            return HITLResult(False, request_id, HITLStatus.DENIED, "请求不存在")
        req.status = HITLStatus.APPROVED if approved else HITLStatus.DENIED
        req.resolved_at = time.time()
        return HITLResult(approved, request_id, req.status)

    def check_timeout(self, request_id: str) -> HITLResult:
        req = self._pending.get(request_id)
        if not req:
            return HITLResult(False, request_id, HITLStatus.DENIED, "请求不存在")
        if req.is_expired():
            req.status = HITLStatus.TIMEOUT
            req.resolved_at = time.time()
            return HITLResult(False, request_id, HITLStatus.TIMEOUT, "超时 default-deny")
        return HITLResult(True, request_id, HITLStatus.PENDING)

    def get_stats(self) -> Dict:
        total = len(self._pending)
        by_status = {}
        for req in self._pending.values():
            s = req.status.value
            by_status[s] = by_status.get(s, 0) + 1
        return {"total": total, "by_status": by_status}
