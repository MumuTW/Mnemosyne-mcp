"""
Load 階段：圖資料庫載入器

負責將解析結果載入到 FalkorDB 圖資料庫中。
"""

from dataclasses import dataclass
from typing import List

from ..drivers.falkordb_driver import FalkorDBDriver
from .cognify import CallInfo, FunctionInfo


@dataclass
class LoadResult:
    """載入結果"""

    functions_loaded: int
    calls_loaded: int
    errors: List[str]


class GraphLoader:
    """
    圖資料庫載入器

    負責將 ECL 管線的結果載入到 FalkorDB 中。
    """

    def __init__(self, driver: FalkorDBDriver):
        """
        初始化載入器

        Args:
            driver: FalkorDB 驅動器
        """
        self.driver = driver

    async def load_data(
        self, functions: List[FunctionInfo], calls: List[CallInfo]
    ) -> LoadResult:
        """
        載入資料到圖資料庫

        Args:
            functions: 函數列表
            calls: 呼叫關係列表

        Returns:
            LoadResult: 載入結果
        """
        errors = []
        functions_loaded = 0
        calls_loaded = 0

        try:
            # 確保連接
            if not self.driver.is_connected:
                await self.driver.connect()

            # 載入函數節點
            for function in functions:
                try:
                    await self._create_function_node(function)
                    functions_loaded += 1
                except Exception as e:
                    error_msg = f"載入函數節點失敗 {function.name}: {str(e)}"
                    errors.append(error_msg)

            # 載入呼叫關係
            for call in calls:
                try:
                    await self._create_call_edge(call)
                    calls_loaded += 1
                except Exception as e:
                    error_msg = f"載入呼叫關係失敗 {call.caller_function} -> {call.callee_function}: {str(e)}"
                    errors.append(error_msg)

        except Exception as e:
            error_msg = f"載入過程發生錯誤: {str(e)}"
            errors.append(error_msg)

        return LoadResult(
            functions_loaded=functions_loaded, calls_loaded=calls_loaded, errors=errors
        )

    async def _create_function_node(self, function: FunctionInfo) -> None:
        """創建函數節點"""
        # 使用 MERGE 確保節點唯一性
        query = """
        MERGE (f:Function {
            name: $name,
            file_path: $file_path,
            line_start: $line_start
        })
        SET f.line_end = $line_end,
            f.signature = $signature,
            f.is_method = $is_method,
            f.class_name = $class_name
        RETURN f
        """

        parameters = {
            "name": function.name,
            "file_path": function.file_path,
            "line_start": function.line_start,
            "line_end": function.line_end,
            "signature": function.signature,
            "is_method": function.is_method,
            "class_name": function.class_name,
        }

        await self.driver.execute_query(query, parameters)

    async def _create_call_edge(self, call: CallInfo) -> None:
        """創建呼叫關係邊"""
        # 建立呼叫關係
        query = """
        MATCH (caller:Function {name: $caller_name, file_path: $file_path})
        MATCH (callee:Function {name: $callee_name, file_path: $file_path})
        MERGE (caller)-[r:CALLS]->(callee)
        SET r.call_line = $call_line
        RETURN r
        """

        parameters = {
            "caller_name": call.caller_function,
            "callee_name": call.callee_function,
            "file_path": call.file_path,
            "call_line": call.call_line,
        }

        await self.driver.execute_query(query, parameters)

    async def clear_data(self, file_path: str = None) -> None:
        """
        清除資料

        Args:
            file_path: 檔案路徑，如果提供則只清除該檔案的資料
        """
        if file_path:
            # 清除特定檔案的資料
            query = """
            MATCH (f:Function {file_path: $file_path})
            OPTIONAL MATCH (f)-[r:CALLS]-()
            DELETE r, f
            """
            await self.driver.execute_query(query, parameters={"file_path": file_path})
        else:
            # 清除所有資料
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            DELETE r, n
            """
            await self.driver.execute_query(query)
