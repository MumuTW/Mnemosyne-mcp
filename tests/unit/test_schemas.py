"""
數據模型測試

測試 Pydantic 數據模型的驗證和序列化。
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from mnemosyne.schemas.constraints import Constraint, ConstraintSeverity, ConstraintType
from mnemosyne.schemas.core import EntityType, File, Function
from mnemosyne.schemas.relationships import CallsRelationship, RelationshipType


@pytest.mark.unit
class TestFileEntity:
    """測試文件實體模型"""

    def test_file_creation_valid(self):
        """測試有效文件創建"""
        file_entity = File(
            name="main.py", path="/app/main.py", extension=".py", language="python"
        )

        assert file_entity.name == "main.py"
        assert file_entity.path == "/app/main.py"
        assert file_entity.extension == ".py"
        assert file_entity.language == "python"
        assert file_entity.entity_type == EntityType.FILE
        assert file_entity.unique_key == "File:/app/main.py"

    def test_file_extension_normalization(self):
        """測試文件擴展名標準化"""
        file_entity = File(name="test.py", path="/test.py", extension="py")  # 沒有點

        assert file_entity.extension == ".py"

    def test_file_path_validation(self):
        """測試文件路徑驗證"""
        with pytest.raises(ValidationError):
            File(name="test.py", path="", extension=".py")  # 空路徑

    def test_file_hash_calculation(self):
        """測試文件哈希計算"""
        file_entity = File(name="test.py", path="/test.py", extension=".py")

        content = "print('hello world')"
        hash_value = file_entity.calculate_hash(content)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 哈希長度


@pytest.mark.unit
class TestFunctionEntity:
    """測試函數實體模型"""

    def test_function_creation_valid(self):
        """測試有效函數創建"""
        function_entity = Function(
            name="main",
            file_path="/app/main.py",
            line_start=1,
            line_end=10,
            parameters=["args", "kwargs"],
            is_async=True,
        )

        assert function_entity.name == "main"
        assert function_entity.file_path == "/app/main.py"
        assert function_entity.line_start == 1
        assert function_entity.line_end == 10
        assert function_entity.parameters == ["args", "kwargs"]
        assert function_entity.is_async is True
        assert function_entity.entity_type == EntityType.FUNCTION

    def test_function_line_validation(self):
        """測試函數行號驗證"""
        with pytest.raises(ValidationError):
            Function(
                name="test", file_path="/test.py", line_start=0, line_end=10  # 無效行號
            )

        with pytest.raises(ValidationError):
            Function(
                name="test",
                file_path="/test.py",
                line_start=10,
                line_end=5,  # 結束行小於開始行
            )

    def test_function_signature(self):
        """測試函數簽名生成"""
        function_entity = Function(
            name="test_func",
            file_path="/test.py",
            line_start=1,
            line_end=5,
            parameters=["arg1", "arg2", "kwarg1=None"],
        )

        expected_signature = "test_func(arg1, arg2, kwarg1=None)"
        assert function_entity.signature == expected_signature

    def test_function_unique_key(self):
        """測試函數唯一鍵"""
        function_entity = Function(
            name="test", file_path="/app/test.py", line_start=10, line_end=20
        )

        expected_key = "Function:/app/test.py:test:10"
        assert function_entity.unique_key == expected_key


@pytest.mark.unit
class TestCallsRelationship:
    """測試調用關係模型"""

    def test_calls_relationship_creation(self):
        """測試調用關係創建"""
        relationship = CallsRelationship(
            source_id="func_001",
            target_id="func_002",
            call_type="direct",
            call_line=15,
            is_conditional=True,
        )

        assert relationship.source_id == "func_001"
        assert relationship.target_id == "func_002"
        assert relationship.call_type == "direct"
        assert relationship.call_line == 15
        assert relationship.is_conditional is True
        assert relationship.relationship_type == RelationshipType.CALLS

    def test_relationship_is_active(self):
        """測試關係有效性檢查"""
        relationship = CallsRelationship(source_id="func_001", target_id="func_002")

        # 沒有設置有效期，應該是活動的
        assert relationship.is_active is True

        # 設置未來的有效期
        future_time = datetime.now().replace(year=2030)
        relationship.valid_from = future_time
        assert relationship.is_active is False


@pytest.mark.unit
class TestConstraint:
    """測試約束模型"""

    def test_constraint_creation(self):
        """測試約束創建"""
        constraint = Constraint(
            name="Core Logic Protection",
            constraint_type=ConstraintType.IMMUTABLE_LOGIC,
            description="Protect core authentication logic",
            severity=ConstraintSeverity.HIGH,
            owner="security-team",
        )

        assert constraint.name == "Core Logic Protection"
        assert constraint.constraint_type == ConstraintType.IMMUTABLE_LOGIC
        assert constraint.severity == ConstraintSeverity.HIGH
        assert constraint.owner == "security-team"
        assert constraint.active is True
        assert constraint.violation_count == 0

    def test_constraint_expiry(self):
        """測試約束過期檢查"""
        constraint = Constraint(
            name="Test Constraint",
            constraint_type=ConstraintType.DEPRECATION_POLICY,
            description="Test constraint",
        )

        # 沒有設置過期時間，不應該過期
        assert constraint.is_expired is False
        assert constraint.is_effective is True

        # 設置過去的過期時間
        past_time = datetime.now().replace(year=2020)
        constraint.expires_at = past_time
        assert constraint.is_expired is True
        assert constraint.is_effective is False

    def test_constraint_violation_recording(self):
        """測試約束違規記錄"""
        constraint = Constraint(
            name="Test Constraint",
            constraint_type=ConstraintType.VERSION_PINNING,
            description="Test constraint",
        )

        initial_count = constraint.violation_count
        initial_time = constraint.last_violation

        constraint.record_violation()

        assert constraint.violation_count == initial_count + 1
        assert constraint.last_violation != initial_time
        assert constraint.last_violation is not None


@pytest.mark.unit
class TestModelSerialization:
    """測試模型序列化"""

    def test_file_to_graph_properties(self):
        """測試文件實體轉換為圖屬性"""
        file_entity = File(
            name="test.py",
            path="/test.py",
            extension=".py",
            language="python",
            extra={"custom_field": "custom_value"},
        )

        properties = file_entity.to_graph_properties()

        assert "name" in properties
        assert "path" in properties
        assert "entity_type" in properties
        assert "custom_field" in properties
        assert properties["custom_field"] == "custom_value"

    def test_relationship_to_graph_properties(self):
        """測試關係轉換為圖屬性"""
        relationship = CallsRelationship(
            source_id="func_001",
            target_id="func_002",
            call_type="direct",
            extra={"context": "test_context"},
        )

        properties = relationship.to_graph_properties()

        assert "relationship_type" in properties
        assert "call_type" in properties
        assert "context" in properties
        # source_id 和 target_id 不應該在屬性中
        assert "source_id" not in properties
        assert "target_id" not in properties
