"""
FalkorDB 驅動實作

這個模組實作了 FalkorDB 的 GraphStoreClient 驅動。
"""

import time
import uuid
from typing import Any, Dict, List, Optional

import falkordb
import structlog

from ..interfaces.graph_store import (
    ConnectionConfig,
    ConnectionError,
    GraphStoreClient,
    QueryError,
    QueryResult,
)

logger = structlog.get_logger(__name__)


class FalkorDBDriver(GraphStoreClient):
    """
    FalkorDB 驅動實作

    實作了 GraphStoreClient 抽象介面，提供對 FalkorDB 的訪問能力。
    """

    def __init__(self, config: ConnectionConfig):
        super().__init__(config)
        self._client = None
        self._graph = None

    async def connect(self) -> None:
        """建立 FalkorDB 連接"""
        try:
            self.logger.info(
                "Connecting to FalkorDB",
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
            )

            # 創建 FalkorDB 客戶端
            self._client = falkordb.FalkorDB(
                host=self.config.host,
                port=self.config.port,
                username=self.config.username,
                password=self.config.password,
            )

            # 選擇圖資料庫
            self._graph = self._client.select_graph(self.config.database)

            # 測試連接
            self._test_connection()

            self._connected = True
            self.logger.info("Successfully connected to FalkorDB")

        except Exception as e:
            self.logger.error("Failed to connect to FalkorDB", error=str(e))
            raise ConnectionError(f"Failed to connect to FalkorDB: {str(e)}")

    async def disconnect(self) -> None:
        """關閉 FalkorDB 連接"""
        try:
            if self._client:
                self._client.close()
                self._client = None
                self._graph = None
                self._connected = False
                self.logger.info("Disconnected from FalkorDB")
        except Exception as e:
            self.logger.error("Error during disconnect", error=str(e))

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> QueryResult:
        """執行 Cypher 查詢"""
        if not self._connected or not self._graph:
            raise ConnectionError("Not connected to FalkorDB")

        if trace_id is None:
            trace_id = str(uuid.uuid4())

        start_time = time.time()

        try:
            self.logger.debug(
                "Executing query", query=query, parameters=parameters, trace_id=trace_id
            )

            # 執行查詢
            if parameters:
                result = self._graph.query(query, parameters)
            else:
                result = self._graph.query(query)

            execution_time = (time.time() - start_time) * 1000

            # 轉換結果格式
            data = self._convert_result(result)

            query_result = QueryResult(
                data=data,
                execution_time_ms=execution_time,
                query=query,
                parameters=parameters,
                metadata={
                    "trace_id": trace_id,
                    "nodes_created": getattr(result, "nodes_created", 0),
                    "nodes_deleted": getattr(result, "nodes_deleted", 0),
                    "relationships_created": getattr(
                        result, "relationships_created", 0
                    ),
                    "relationships_deleted": getattr(
                        result, "relationships_deleted", 0
                    ),
                    "properties_set": getattr(result, "properties_set", 0),
                },
            )

            self.logger.debug(
                "Query executed successfully",
                trace_id=trace_id,
                execution_time_ms=execution_time,
                result_count=query_result.count,
            )

            return query_result

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self.logger.error(
                "Query execution failed",
                query=query,
                parameters=parameters,
                trace_id=trace_id,
                execution_time_ms=execution_time,
                error=str(e),
            )
            raise QueryError(f"Query execution failed: {str(e)}")

    async def ping(self) -> bool:
        """檢查 FalkorDB 連接狀態"""
        try:
            if not self._client or not self._graph:
                return False

            # 執行簡單的 ping 查詢
            result = await self.execute_query("RETURN 1")
            return not result.is_empty

        except Exception as e:
            self.logger.debug("Ping failed", error=str(e))
            return False

    def _test_connection(self) -> None:
        """測試連接是否正常"""
        try:
            # 執行簡單查詢測試連接
            test_result = self._graph.query("RETURN 1 as test")
            if not test_result:
                raise ConnectionError("Test query failed")
        except Exception as e:
            raise ConnectionError(f"Connection test failed: {str(e)}")

    def _convert_result(self, result) -> List[Dict[str, Any]]:
        """
        轉換 FalkorDB 查詢結果為標準格式

        Args:
            result: FalkorDB 查詢結果

        Returns:
            List[Dict[str, Any]]: 標準化的結果列表
        """
        if not result or not hasattr(result, "result_set"):
            return []

        data = []

        try:
            # 獲取列名
            if hasattr(result, "header") and result.header:
                columns = result.header
            else:
                columns = []

            # 轉換每一行數據
            for row in result.result_set:
                row_dict = {}
                for i, value in enumerate(row):
                    column_name = columns[i] if i < len(columns) else f"column_{i}"
                    row_dict[column_name] = self._convert_value(value)
                data.append(row_dict)

        except Exception as e:
            self.logger.warning("Failed to convert result", error=str(e))
            # 如果轉換失敗，返回原始結果
            if hasattr(result, "result_set"):
                data = [{"raw": row} for row in result.result_set]

        return data

    def _convert_value(self, value: Any) -> Any:
        """
        轉換 FalkorDB 值為 Python 標準類型

        Args:
            value: FalkorDB 值

        Returns:
            Any: 轉換後的 Python 值
        """
        # 處理節點
        if hasattr(value, "properties") and hasattr(value, "labels"):
            return {
                "type": "node",
                "labels": list(value.labels) if value.labels else [],
                "properties": dict(value.properties) if value.properties else {},
                "id": getattr(value, "id", None),
            }

        # 處理關係
        if hasattr(value, "properties") and hasattr(value, "relation"):
            return {
                "type": "relationship",
                "relation": value.relation,
                "properties": dict(value.properties) if value.properties else {},
                "src_node": getattr(value, "src_node", None),
                "dest_node": getattr(value, "dest_node", None),
            }

        # 處理路徑
        if hasattr(value, "nodes") and hasattr(value, "edges"):
            return {
                "type": "path",
                "nodes": [self._convert_value(node) for node in value.nodes],
                "edges": [self._convert_value(edge) for edge in value.edges],
            }

        # 基本類型直接返回
        return value

    async def create_vector_index(
        self,
        node_label: str,
        property_name: str,
        dimension: int = 1536,
        similarity_function: str = "cosine",
    ) -> bool:
        """
        創建向量索引

        Args:
            node_label: 節點標籤
            property_name: 屬性名稱
            dimension: 向量維度，默認 1536 (text-embedding-3-small)
            similarity_function: 相似度函數，默認 cosine

        Returns:
            bool: 是否成功創建索引
        """
        try:
            # 構建創建向量索引的 Cypher 查詢
            query = f"""
            CALL db.idx.vector.createNodeIndex(
                '{node_label}',
                '{property_name}',
                {dimension},
                '{similarity_function}'
            )
            """

            self.logger.info(
                "Creating vector index",
                node_label=node_label,
                property_name=property_name,
                dimension=dimension,
                similarity_function=similarity_function,
            )

            await self.execute_query(query)

            self.logger.info(
                "Vector index created successfully",
                node_label=node_label,
                property_name=property_name,
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to create vector index",
                node_label=node_label,
                property_name=property_name,
                error=str(e),
            )
            return False

    async def vector_search(
        self,
        node_label: str,
        property_name: str,
        query_vector: List[float],
        top_k: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        執行向量搜索

        Args:
            node_label: 節點標籤
            property_name: 向量屬性名稱
            query_vector: 查詢向量
            top_k: 返回最相似的 k 個結果

        Returns:
            List[Dict[str, Any]]: 搜索結果列表
        """
        try:
            # 構建向量搜索的 Cypher 查詢
            query = f"""
            CALL db.idx.vector.queryNodes(
                '{node_label}',
                '{property_name}',
                {top_k},
                $vector
            ) YIELD node, score
            RETURN node, score
            ORDER BY score DESC
            """

            self.logger.info(
                "Executing vector search",
                node_label=node_label,
                property_name=property_name,
                top_k=top_k,
                vector_dimension=len(query_vector),
            )

            result = await self.execute_query(query, {"vector": query_vector})

            # 處理搜索結果
            search_results = []
            for row in result.data:
                if "node" in row and "score" in row:
                    search_results.append(
                        {
                            "node": row["node"],
                            "similarity_score": float(row["score"]),
                            "node_id": (
                                row["node"].get("id")
                                if isinstance(row["node"], dict)
                                else None
                            ),
                            "properties": (
                                row["node"].get("properties", {})
                                if isinstance(row["node"], dict)
                                else {}
                            ),
                        }
                    )

            self.logger.info(
                "Vector search completed", results_count=len(search_results)
            )

            return search_results

        except Exception as e:
            self.logger.error(
                "Vector search failed",
                node_label=node_label,
                property_name=property_name,
                error=str(e),
            )
            return []

    async def add_node_with_vector(
        self,
        node_label: str,
        properties: Dict[str, Any],
        vector_property: str,
        vector: List[float],
    ) -> Optional[str]:
        """
        添加帶有向量的節點

        Args:
            node_label: 節點標籤
            properties: 節點屬性
            vector_property: 向量屬性名稱
            vector: 向量值

        Returns:
            Optional[str]: 節點 ID，如果失敗則返回 None
        """
        try:
            # 生成唯一 ID
            node_id = str(uuid.uuid4())

            # 合併屬性和向量
            all_properties = {**properties, vector_property: vector, "id": node_id}

            # 構建屬性字符串
            props_str = ", ".join([f"{k}: ${k}" for k in all_properties.keys()])

            query = f"CREATE (n:{node_label} {{{props_str}}}) RETURN n.id as id"

            result = await self.execute_query(query, all_properties)

            if result.data and len(result.data) > 0:
                created_id = result.data[0].get("id", node_id)
                self.logger.info(
                    "Node with vector created",
                    node_id=created_id,
                    node_label=node_label,
                )
                return created_id

            return node_id

        except Exception as e:
            self.logger.error(
                "Failed to create node with vector", node_label=node_label, error=str(e)
            )
            return None
