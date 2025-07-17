"""
約束引擎核心

基於規則引擎模式實作的約束檢查系統，支援多種約束類型和可擴展的規則定義。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

import structlog

from .models import (
    Constraint,
    ConstraintType,
    ValidationResult,
    Violation,
    ViolationLocation,
)

logger = structlog.get_logger(__name__)


class Rule(ABC):
    """規則基類"""

    def __init__(self, constraint: Constraint):
        self.constraint = constraint
        self.rule_config = constraint.rule_config

    @abstractmethod
    async def check(self, file_path: str, ast_data: Dict) -> List[Violation]:
        """檢查規則違規"""
        pass

    def create_violation(
        self,
        message: str,
        location: ViolationLocation,
        suggestion: Optional[str] = None,
    ) -> Violation:
        """創建違規對象"""
        return Violation(
            id=f"{self.constraint.id}_{location.file_path}_{location.line_number}",
            constraint_id=self.constraint.id,
            constraint_name=self.constraint.name,
            message=message,
            severity=self.constraint.severity,
            location=location,
            suggestion=suggestion or self.constraint.suggestion,
        )


class ArchitectureRule(Rule):
    """架構約束規則"""

    async def check(self, file_path: str, ast_data: Dict) -> List[Violation]:
        """檢查架構約束違規"""
        violations = []

        # 簡化的架構檢查邏輯
        imports = ast_data.get("imports", [])

        for import_info in imports:
            module_name = import_info.get("module", "")

            # 示例：檢查是否違反分層架構
            if "ui" in file_path.lower() and "database" in module_name.lower():
                violation = self.create_violation(
                    message=f"架構違規: UI 層不應直接訪問數據層 {module_name}",
                    location=ViolationLocation(
                        file_path=file_path,
                        line_number=import_info.get("line_number", 1),
                    ),
                    suggestion="請通過服務層訪問數據",
                )
                violations.append(violation)

        return violations


class SecurityRule(Rule):
    """安全約束規則"""

    async def check(self, file_path: str, ast_data: Dict) -> List[Violation]:
        """檢查安全約束違規"""
        violations = []

        # 檢查危險函數調用
        function_calls = ast_data.get("function_calls", [])
        dangerous_functions = ["eval", "exec", "compile"]

        for call in function_calls:
            function_name = call.get("name", "")

            if function_name in dangerous_functions:
                violation = self.create_violation(
                    message=f"安全風險: 使用了危險函數 {function_name}",
                    location=ViolationLocation(
                        file_path=file_path, line_number=call.get("line_number", 1)
                    ),
                    suggestion=f"請避免使用 {function_name}，考慮使用更安全的替代方案",
                )
                violations.append(violation)

        return violations


class RuleRegistry:
    """規則註冊表"""

    def __init__(self):
        self._rules = {
            ConstraintType.ARCHITECTURE: ArchitectureRule,
            ConstraintType.SECURITY: SecurityRule,
        }

    def create_rule(self, constraint: Constraint) -> Rule:
        """創建規則實例"""
        rule_class = self._rules.get(constraint.type)
        if not rule_class:
            raise ValueError(f"未知的約束類型: {constraint.type}")

        return rule_class(constraint)


class ConstraintEngine:
    """約束引擎"""

    def __init__(self):
        self.rule_registry = RuleRegistry()
        self.constraints: Dict[str, Constraint] = {}

    def add_constraint(self, constraint: Constraint) -> None:
        """添加約束"""
        self.constraints[constraint.id] = constraint

    def list_constraints(self) -> List[Constraint]:
        """列出啟用的約束"""
        return [c for c in self.constraints.values() if c.enabled]

    async def validate_file(self, file_path: str, ast_data: Dict) -> ValidationResult:
        """驗證單個檔案"""
        start_time = time.time()
        result = ValidationResult(success=True, total_files_checked=1)

        # 獲取啟用的約束
        active_constraints = self.list_constraints()

        # 並行執行所有規則檢查
        tasks = []
        for constraint in active_constraints:
            try:
                rule = self.rule_registry.create_rule(constraint)
                task = rule.check(file_path, ast_data)
                tasks.append(task)
            except Exception as e:
                logger.warning(f"無法創建規則 {constraint.id}: {e}")

        # 等待所有檢查完成
        if tasks:
            violations_lists = await asyncio.gather(*tasks, return_exceptions=True)

            for result_or_exc in violations_lists:
                if isinstance(result_or_exc, Exception):
                    logger.warning(f"規則檢查失敗: {result_or_exc}")
                    continue

                for violation in result_or_exc:
                    result.add_violation(violation)

        # 設置結果狀態
        result.success = not result.has_errors()
        result.execution_time_ms = (time.time() - start_time) * 1000

        return result
