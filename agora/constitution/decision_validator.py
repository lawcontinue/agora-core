"""
决策验证器

版本: agora-core 0.1.0
原始作者: 忒弥斯 (T-Mind)
"""

from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass


class ValidationSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    is_valid: bool
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    suggestion: Optional[str] = None


class DecisionValidator:
    """决策验证器"""

    REQUIRED_FIELDS = ["decision", "participants", "reasoning"]

    def validate(self, entry: Dict) -> List[ValidationResult]:
        results = []
        for f in self.REQUIRED_FIELDS:
            if f not in entry or not entry[f]:
                results.append(ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"缺少必需字段: {f}",
                    field=f,
                ))
        if "participants" in entry and len(entry.get("participants", [])) < 1:
            results.append(ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.WARNING,
                message="参与者列表为空",
                field="participants",
            ))
        if not results:
            results.append(ValidationResult(
                is_valid=True,
                severity=ValidationSeverity.INFO,
                message="验证通过",
            ))
        return results
