# Atlassian gRPC 知識提取服務

## 概述

本文檔描述了 Atlassian 知識提取的 gRPC 服務實現，該服務是 Mnemosyne MCP 系統中用於從 Atlassian 工具（Jira 和 Confluence）提取知識的核心組件。

## 架構概覽

### 核心組件

1. **Protocol Buffer 定義** (`proto/atlassian.proto`)
   - 定義了 gRPC 服務介面和訊息結構
   - 包含所有 Atlassian 相關的實體和關係定義

2. **gRPC 服務實現** (`src/mnemosyne/grpc/atlassian_service_simple.py`)
   - 實現了 AtlassianKnowledgeExtractorService
   - 整合了 AtlassianClient 和 AtlassianMapper

3. **gRPC 伺服器** (`src/mnemosyne/grpc/server.py`)
   - 提供伺服器啟動和管理功能
   - 支援優雅關閉和信號處理

## 服務端點

### 主要服務方法

#### 1. ExtractJiraIssues
```protobuf
rpc ExtractJiraIssues(ExtractJiraIssuesRequest) returns (ExtractJiraIssuesResponse);
```
- **功能**: 從 Jira 提取 Issues 數據
- **輸入**: 查詢字符串、專案過濾器、最大結果數
- **輸出**: JiraIssueEntity 列表和相關關係

#### 2. ExtractConfluencePages
```protobuf
rpc ExtractConfluencePages(ExtractConfluencePagesRequest) returns (ExtractConfluencePagesResponse);
```
- **功能**: 從 Confluence 提取頁面數據
- **輸入**: 查詢字符串、空間過濾器、最大結果數
- **輸出**: ConfluencePageEntity 列表和相關關係

#### 3. CheckHealth
```protobuf
rpc CheckHealth(HealthCheckRequest) returns (HealthCheckResponse);
```
- **功能**: 檢查服務健康狀態
- **輸入**: 是否檢查連通性
- **輸出**: 健康狀態和響應時間

#### 4. GetExtractionStats
```protobuf
rpc GetExtractionStats(GetExtractionStatsRequest) returns (ExtractionStatsResponse);
```
- **功能**: 獲取提取統計信息
- **輸出**: 請求計數、成功率、提取的實體數量

## 數據模型

### 核心實體

#### JiraIssueEntity
```protobuf
message JiraIssueEntity {
  string id = 1;                    // 內部唯一 ID
  string jira_id = 2;               // Jira 系統 ID
  string key = 3;                   // Issue 鍵值 (如 "DEMO-123")
  string summary = 4;               // Issue 摘要
  string description = 5;           // Issue 描述
  string status = 6;                // 狀態
  string priority = 7;              // 優先級
  string issue_type = 8;            // Issue 類型
  string project_key = 9;           // 專案鍵值
  string assignee = 10;             // 指派者
  string reporter = 11;             // 報告者
  google.protobuf.Timestamp created_at = 12;
  google.protobuf.Timestamp updated_at = 13;
  repeated string labels = 14;      // 標籤
  repeated string components = 15;  // 組件
  map<string, string> custom_fields = 16;
  string url = 17;                  // Issue URL
}
```

#### ConfluencePageEntity
```protobuf
message ConfluencePageEntity {
  string id = 1;                    // 內部唯一 ID
  string confluence_id = 2;         // Confluence 系統 ID
  string title = 3;                 // 頁面標題
  string content = 4;               // 頁面內容
  string space_key = 5;             // 空間鍵值
  string space_name = 6;            // 空間名稱
  string author = 7;                // 作者
  google.protobuf.Timestamp created_at = 8;
  google.protobuf.Timestamp updated_at = 9;
  int32 version = 10;               // 版本號
  string status = 11;               // 狀態
  repeated string labels = 12;      // 標籤
  repeated string ancestors = 13;   // 父頁面
  string url = 14;                  // 頁面 URL
}
```

### 關係模型

#### KnowledgeRelationship
```protobuf
message KnowledgeRelationship {
  string id = 1;                    // 關係唯一 ID
  string source_id = 2;             // 源實體 ID
  string target_id = 3;             // 目標實體 ID
  RelationshipType type = 4;        // 關係類型
  map<string, string> properties = 5;
  google.protobuf.Timestamp created_at = 6;
  float strength = 7;               // 關係強度 (0.0-1.0)
}
```

#### 關係類型
- `BELONGS_TO`: 屬於關係 (Issue → Project, Page → Space)
- `ASSIGNED_TO`: 指派關係 (Issue → Person)
- `AUTHORED_BY`: 創建者關係 (Page → Person)
- `REFERENCES`: 引用關係 (Page → Issue)
- `DEPENDS_ON`: 依賴關係 (Issue → Issue)
- `BLOCKS`: 阻塞關係 (Issue → Issue)
- `LINKED_TO`: 連結關係 (Issue → Page)
- `CONTAINS`: 包含關係 (Space → Page)
- `CHILD_OF`: 子關係 (Page → Page)

## 使用方式

### 啟動 gRPC 伺服器

```python
from mnemosyne.core.config import Settings
from mnemosyne.grpc.server import serve

# 載入配置
settings = Settings()

# 啟動伺服器
await serve(settings, port=50051)
```

### 客戶端使用

```python
import grpc
from mnemosyne.grpc import atlassian_pb2, atlassian_pb2_grpc

# 創建通道
channel = grpc.insecure_channel('localhost:50051')
stub = atlassian_pb2_grpc.AtlassianKnowledgeExtractorStub(channel)

# 提取 Jira Issues
request = atlassian_pb2.ExtractJiraIssuesRequest(
    query="project = DEMO AND status = Open",
    max_results=100,
    include_relationships=True
)
response = stub.ExtractJiraIssues(request)

print(f"Found {len(response.issues)} issues")
for issue in response.issues:
    print(f"- {issue.key}: {issue.summary}")
```

## 配置

### 必要配置
```yaml
mcp_atlassian:
  service_url: "http://mcp-atlassian:8001"
  read_only_mode: true
  enabled_tools:
    - "confluence_search"
    - "jira_search"
    - "jira_get_issue"
  jira_url: "https://company.atlassian.net"
  jira_username: "user@company.com"
  jira_api_token: "your-api-token"
  confluence_url: "https://company.atlassian.net/wiki"
  confluence_username: "user@company.com"
  confluence_api_token: "your-api-token"
```

## 測試

### 單元測試
```bash
uv run python -m pytest tests/unit/test_grpc_atlassian_service.py -v
```

### 整合測試
```bash
uv run python -m pytest tests/integration/test_grpc_server.py -v
```

### 測試覆蓋率
- 服務初始化和配置
- 健康檢查 (有/無連通性檢查)
- Jira Issues 提取 (成功/失敗)
- Confluence 頁面提取 (成功/失敗)
- 統計信息獲取
- 關係轉換
- 錯誤處理

## 監控與統計

### 內建統計
- `total_requests`: 總請求數
- `successful_requests`: 成功請求數
- `failed_requests`: 失敗請求數
- `success_rate`: 成功率 (%)
- `issues_extracted`: 提取的 Issues 數量
- `pages_extracted`: 提取的頁面數量
- `average_response_time_ms`: 平均響應時間 (毫秒)

### 健康檢查端點
提供服務狀態檢查，包括：
- 基本服務狀態
- MCP Atlassian 連通性檢查
- 響應時間測量

## 擴展性

### 新增服務方法
1. 在 `proto/atlassian.proto` 中定義新的 RPC 方法
2. 重新生成 protobuf 文件
3. 在 `atlassian_service_simple.py` 中實現方法
4. 添加相應的測試

### 新增實體類型
1. 在 protobuf 中定義新的 message
2. 在 `AtlassianMapper` 中添加映射邏輯
3. 更新服務方法以處理新實體
4. 添加測試覆蓋

## 效能考量

### 並發處理
- 使用 ThreadPoolExecutor 處理並發請求
- 預設最大工作線程數：10
- 可根據需要調整 `max_workers` 參數

### 響應時間優化
- 使用 asyncio 進行異步 I/O
- 實現請求統計和監控
- 支援批次處理減少往返次數

### 記憶體管理
- 對長內容進行適當截斷
- 使用流式處理處理大型結果集
- 定期清理統計數據

## 故障排除

### 常見問題

1. **服務無法啟動**
   - 檢查端口是否被占用
   - 驗證 MCP Atlassian 配置
   - 查看日誌中的錯誤信息

2. **提取結果為空**
   - 確認 MCP Atlassian 服務正在運行
   - 檢查 API 憑證是否正確
   - 驗證查詢語法

3. **性能問題**
   - 監控請求統計
   - 檢查網絡延遲
   - 調整並發參數

### 日誌級別
- `DEBUG`: 詳細的請求/響應信息
- `INFO`: 基本操作信息
- `WARNING`: 非致命問題
- `ERROR`: 錯誤和異常

## 未來改進

1. **安全性增強**
   - 添加 TLS 支援
   - 實現認證和授權
   - 添加速率限制

2. **功能擴展**
   - 支援更多 Atlassian 產品
   - 添加批次處理端點
   - 實現增量同步

3. **性能優化**
   - 添加連接池
   - 實現智能快取
   - 優化大型結果集處理

4. **監控改進**
   - 添加指標收集
   - 實現分散式追蹤
   - 集成健康檢查系統
