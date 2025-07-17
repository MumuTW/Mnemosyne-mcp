"""
治理 CLI 工具

提供 mnemo pr-check 等命令行工具，支援雙格式輸出（人類可讀 + 機器可讀）。
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click

from ..governance.constraint_engine import ConstraintEngine
from ..governance.models import Constraint, Severity, ValidationResult


class OutputFormatter:
    """輸出格式化器"""
    
    def __init__(self, format_type: str = "human"):
        self.format_type = format_type
    
    def format_validation_result(self, result: ValidationResult) -> str:
        """格式化驗證結果"""
        if self.format_type == "json":
            return self._format_json(result)
        else:
            return self._format_human(result)
    
    def _format_human(self, result: ValidationResult) -> str:
        """人類可讀格式"""
        lines = []
        
        lines.append("🔍 程式碼檢查結果")
        lines.append("=" * 50)
        
        if result.violations:
            for violation in result.violations:
                severity_emoji = {
                    Severity.ERROR: "❌",
                    Severity.WARNING: "⚠️",
                    Severity.INFO: "ℹ️"
                }.get(violation.severity, "")
                
                lines.append(f"{severity_emoji} {violation.location.file_path}:{violation.location.line_number}")
                lines.append(f"   {violation.message}")
                if violation.suggestion:
                    lines.append(f"   💡 建議: {violation.suggestion}")
                lines.append("")
        
        # 摘要
        lines.append("📊 檢查摘要")
        lines.append("-" * 30)
        lines.append(f"檢查檔案數: {result.total_files_checked}")
        lines.append(f"總違規數: {result.total_violations}")
        lines.append(f"錯誤: {result.error_count}")
        lines.append(f"警告: {result.warning_count}")
        lines.append(f"執行時間: {result.execution_time_ms:.1f}ms")
        
        if result.success:
            lines.append("\n✅ 檢查通過")
        else:
            lines.append("\n❌ 檢查失敗")
        
        return "\n".join(lines)
    
    def _format_json(self, result: ValidationResult) -> str:
        """機器可讀 JSON 格式"""
        result_dict = {
            "summary": {
                "success": result.success,
                "total_files_checked": result.total_files_checked,
                "total_violations": result.total_violations,
                "error_count": result.error_count,
                "warning_count": result.warning_count,
                "execution_time_ms": result.execution_time_ms
            },
            "violations": [
                {
                    "id": v.id,
                    "constraint_id": v.constraint_id,
                    "message": v.message,
                    "severity": v.severity.value,
                    "location": {
                        "file_path": v.location.file_path,
                        "line_number": v.location.line_number
                    },
                    "suggestion": v.suggestion
                }
                for v in result.violations
            ]
        }
        
        return json.dumps(result_dict, indent=2, ensure_ascii=False)


class GovernanceCLI:
    """治理 CLI 主類"""
    
    def __init__(self):
        self.constraint_engine = ConstraintEngine()
        self.formatter = None
    
    async def setup(self, config_path: Optional[str] = None):
        """設置 CLI 環境"""
        # 載入配置
        if config_path and Path(config_path).exists():
            await self._load_config(config_path)
        else:
            # 載入默認約束
            await self._load_default_constraints()
    
    async def _load_config(self, config_path: str):
        """載入約束配置"""
        # 簡化實作，實際會解析 YAML 配置
        pass
    
    async def _load_default_constraints(self):
        """載入默認約束"""
        from ..governance.models import ConstraintType, RuleConfig, Severity
        
        # 添加默認的架構約束
        arch_constraint = Constraint(
            id="arch_001",
            name="UI 層不應直接訪問數據層",
            description="確保分層架構的完整性",
            type=ConstraintType.ARCHITECTURE,
            severity=Severity.ERROR,
            rule_config=RuleConfig(),
            suggestion="請通過服務層訪問數據"
        )
        self.constraint_engine.add_constraint(arch_constraint)
        
        # 添加默認的安全約束
        security_constraint = Constraint(
            id="sec_001",
            name="禁止使用危險函數",
            description="避免使用 eval, exec 等危險函數",
            type=ConstraintType.SECURITY,
            severity=Severity.ERROR,
            rule_config=RuleConfig(),
            suggestion="請使用更安全的替代方案"
        )
        self.constraint_engine.add_constraint(security_constraint)
    
    async def pr_check(
        self,
        target_branch: str = "main",
        config_path: Optional[str] = None,
        format_type: str = "human",
        severity_threshold: str = "error"
    ) -> int:
        """執行 PR 檢查"""
        self.formatter = OutputFormatter(format_type)
        
        try:
            # 1. 設置環境
            await self.setup(config_path)
            
            # 2. 獲取變更的檔案（模擬）
            changed_files = await self._get_changed_files(target_branch)
            
            # 3. 解析 AST 數據（模擬）
            files_data = {}
            for file_path in changed_files:
                ast_data = await self._parse_file_ast(file_path)
                files_data[file_path] = ast_data
            
            # 4. 執行約束檢查
            all_violations = []
            total_files = len(files_data)
            
            for file_path, ast_data in files_data.items():
                result = await self.constraint_engine.validate_file(file_path, ast_data)
                all_violations.extend(result.violations)
            
            # 5. 創建總結果
            final_result = ValidationResult(
                success=True,
                total_files_checked=total_files
            )
            
            for violation in all_violations:
                final_result.add_violation(violation)
            
            final_result.success = not final_result.has_errors()
            
            # 6. 輸出結果
            output = self.formatter.format_validation_result(final_result)
            click.echo(output)
            
            # 7. 設置退出碼
            if severity_threshold == "error" and final_result.has_errors():
                return 1
            elif severity_threshold == "warning" and (final_result.has_errors() or final_result.warning_count > 0):
                return 1
            
            return 0
            
        except Exception as e:
            click.echo(f"錯誤: {e}", err=True)
            return 1
    
    async def _get_changed_files(self, target_branch: str) -> List[str]:
        """獲取變更的檔案列表（模擬實作）"""
        return [
            "src/ui/components/user_form.py",
            "src/services/user_service.py",
            "src/data/user_repository.py"
        ]
    
    async def _parse_file_ast(self, file_path: str) -> Dict:
        """解析檔案的 AST 數據（模擬實作）"""
        # 模擬不同檔案的 AST 數據
        if "ui" in file_path:
            return {
                "imports": [
                    {"module": "src.data.user_repository", "line_number": 3}
                ],
                "functions": [],
                "function_calls": []
            }
        elif "service" in file_path:
            return {
                "imports": [
                    {"module": "src.data.user_repository", "line_number": 2}
                ],
                "functions": [
                    {"name": "get_user", "start_line": 10, "end_line": 20}
                ],
                "function_calls": [
                    {"name": "eval", "line_number": 15}
                ]
            }
        else:
            return {
                "imports": [],
                "functions": [],
                "function_calls": []
            }


# CLI 命令定義
@click.group()
def mnemo():
    """Mnemosyne MCP 治理工具"""
    pass


@mnemo.command("pr-check")
@click.option("--target-branch", default="main", help="目標分支名稱")
@click.option("--config", "config_path", help="配置檔案路徑")
@click.option("--format", "format_type", type=click.Choice(["human", "json"]), default="human", help="輸出格式")
@click.option("--severity-threshold", type=click.Choice(["error", "warning", "info"]), default="error", help="失敗的嚴重程度閾值")
def pr_check_command(target_branch: str, config_path: str, format_type: str, severity_threshold: str):
    """檢查 PR 中的程式碼約束違規"""
    cli = GovernanceCLI()
    
    # 運行異步檢查
    exit_code = asyncio.run(cli.pr_check(
        target_branch=target_branch,
        config_path=config_path,
        format_type=format_type,
        severity_threshold=severity_threshold
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    mnemo()
