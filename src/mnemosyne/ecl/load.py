"""
Load 階段：圖資料庫載入器

負責將解析結果載入到 FalkorDB 圖資料庫中。
"""

from dataclasses import dataclass
from typing import List, Optional

from ..core.logging import get_logger
from ..drivers.falkordb_driver import FalkorDBDriver
from ..schemas.core import File, Function
from ..schemas.relationships import CallsRelationship

logger = get_logger(__name__)


@dataclass
class LoadResult:
    """載入結果"""

    files_loaded: int
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
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    async def load_project_data(
        self,
        files: List[File],
        functions: List[Function],
        calls: List[CallsRelationship],
    ) -> LoadResult:
        """
        載入專案資料到圖資料庫

        Args:
            files: 檔案列表
            functions: 函數列表
            calls: 呼叫關係列表

        Returns:
            LoadResult: 載入結果
        """
        errors = []
        files_loaded = 0
        functions_loaded = 0
        calls_loaded = 0

        try:
            # 確保連接
            if not self.driver.is_connected:
                await self.driver.connect()

            # 載入檔案節點
            for file in files:
                try:
                    await self._load_file_node(file)
                    files_loaded += 1
                    self.logger.debug(f"載入檔案節點: {file.path}")
                except Exception as e:
                    error_msg = f"載入檔案節點失敗 {file.path}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # 載入函數節點
            for function in functions:
                try:
                    await self._load_function_node(function)
                    functions_loaded += 1
                    self.logger.debug(f"載入函數節點: {function.name}")
                except Exception as e:
                    error_msg = f"載入函數節點失敗 {function.name}: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            # 載入呼叫關係
            for call in calls:
                try:
                    await self._load_call_relationship(call)
                    calls_loaded += 1
                    self.logger.debug(f"載入呼叫關係: {call.caller_id} -> {call.callee_id}")
                except Exception as e:
                    error_msg = (
                        f"載入呼叫關係失敗 {call.caller_id} -> {call.callee_id}: {str(e)}"
                    )
                    errors.append(error_msg)
                    self.logger.error(error_msg)

            self.logger.info(
                f"載入完成: {files_loaded} 檔案, {functions_loaded} 函數, {calls_loaded} 呼叫關係"
            )

        except Exception as e:
            error_msg = f"載入過程發生錯誤: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)

        return LoadResult(
            files_loaded=files_loaded,
            functions_loaded=functions_loaded,
            calls_loaded=calls_loaded,
            errors=errors,
        )

    async def _load_file_node(self, file: File) -> None:
        """載入檔案節點"""
        properties = file.to_graph_properties()

        # 使用 MERGE 確保節點唯一性
        query = """
        MERGE (f:File {unique_key: $unique_key})
        SET f += $properties
        RETURN f
        """

        await self.driver.execute_query(
            query, parameters={"unique_key": file.unique_key, "properties": properties}
        )

    async def _load_function_node(self, function: Function) -> None:
        """載入函數節點"""
        properties = function.to_graph_properties()

        # 使用 MERGE 確保節點唯一性
        query = """
        MERGE (fn:Function {unique_key: $unique_key})
        SET fn += $properties
        RETURN fn
        """

        await self.driver.execute_query(
            query,
            parameters={"unique_key": function.unique_key, "properties": properties},
        )

        # 建立函數與檔案的關係
        if function.file_path:
            file_query = """
            MATCH (fn:Function {unique_key: $function_key})
            MATCH (f:File {path: $file_path})
            MERGE (fn)-[:DEFINED_IN]->(f)
            """

            await self.driver.execute_query(
                file_query,
                parameters={
                    "function_key": function.unique_key,
                    "file_path": function.file_path,
                },
            )

    async def _load_call_relationship(self, call: CallsRelationship) -> None:
        """載入呼叫關係"""
        properties = call.to_graph_properties()

        # 建立呼叫關係
        query = """
        MATCH (caller:Function {unique_key: $caller_id})
        MATCH (callee:Function {unique_key: $callee_id})
        MERGE (caller)-[r:CALLS]->(callee)
        SET r += $properties
        RETURN r
        """

        await self.driver.execute_query(
            query,
            parameters={
                "caller_id": call.caller_id,
                "callee_id": call.callee_id,
                "properties": properties,
            },
        )

    async def clear_project_data(self, project_path: Optional[str] = None) -> None:
        """
        清除專案資料

        Args:
            project_path: 專案路徑，如果提供則只清除該專案的資料
        """
        if project_path:
            # 清除特定專案的資料
            query = """
            MATCH (f:File)
            WHERE f.path STARTS WITH $project_path
            OPTIONAL MATCH (f)<-[:DEFINED_IN]-(fn:Function)
            OPTIONAL MATCH (fn)-[r:CALLS]-()
            DELETE r, fn, f
            """
            await self.driver.execute_query(
                query, parameters={"project_path": project_path}
            )
        else:
            # 清除所有資料
            query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            DELETE r, n
            """
            await self.driver.execute_query(query)

        self.logger.info(f"清除專案資料完成: {project_path or '全部'}")
