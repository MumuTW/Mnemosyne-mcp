Mnemosyne MCP - API & 查詢契約規格 (v1.0)
文件版本	1.0
狀態	草案 (Draft)
核心協議	gRPC (Protocol Buffers v3)
兼容協議	RESTful JSON (via gRPC Gateway)
1. 核心設計原則
gRPC-First: 所有功能首先被定義為 gRPC 服務。RESTful API 是 gRPC 服務的 HTTP/JSON 封裝，以提供兼容性。
Schema-Driven: 所有請求和響應的數據結構，都在 .proto 文件中以 Protocol Buffers 消息 (Message) 嚴格定義。
能力導向 (Capability-Oriented): API 的設計旨在暴露「能力」，而非底層的資料庫操作。
異步優先: 對於所有可能耗時的操作（如 Ingest），API 都將採用異步模式，立即返回任務 ID，並提供查詢任務狀態的機制。
富錯誤信息: 錯誤響應不僅包含錯誤碼，還應包含人類可讀的錯誤信息和機器可解析的上下文（如衝突詳情）。
2. Protocol Buffers 定義 (mcp.proto)
這是我們系統 API 的唯一事實來源 (Single Source of Truth)。
Generated protobuf
syntax = "proto3";

package mnemosyne.mcp.v1;

import "google/protobuf/struct.proto";
import "google/protobuf/timestamp.proto";

// ===================================================================
// 核心服務定義 (Core Service Definition)
// ===================================================================
service MnemosyneMCP {
  // --- 數據導入與管理 (Ingestion & Management) ---
  rpc IngestProject(IngestProjectRequest) returns (IngestProjectResponse);
  rpc GetIngestStatus(GetIngestStatusRequest) returns (IngestStatus);

  // --- 查詢與分析 (Query & Analysis) ---
  rpc Search(SearchRequest) returns (SearchResponse);
  rpc RunImpactAnalysis(ImpactAnalysisRequest) returns (ImpactAnalysisResponse);

  // --- 約束與鎖定 (Constraints & Locking) ---
  rpc ApplyConstraint(ApplyConstraintRequest) returns (ApplyConstraintResponse);
  rpc AcquireLock(AcquireLockRequest) returns (AcquireLockResponse);
  rpc ReleaseLock(ReleaseLockRequest) returns (ReleaseLockResponse);

  // --- 可視化 (Visualization) ---
  rpc GetGraphVisualization(GetGraphVisualizationRequest) returns (GraphVisualization);
}

// ===================================================================
// 數據結構定義 (Message Definitions)
// ===================================================================

// --- 數據導入 ---
message IngestProjectRequest {
  string project_id = 1; // 專案的唯一標識符
  string git_url = 2; // 要導入的 Git 倉儲 URL
  // 可選：指定要分析的分支
  optional string branch = 3;
}

message IngestProjectResponse {
  string task_id = 1; // 用於查詢狀態的異步任務 ID
}

message IngestStatus {
  string task_id = 1;
  enum Status {
    PENDING = 0;
    RUNNING = 1;
    COMPLETED = 2;
    FAILED = 3;
  }
  Status status = 2;
  string message = 3; // 例如 "Parsing file 50/100..."
  google.protobuf.Timestamp completion_time = 4;
}

message GetIngestStatusRequest {
  string task_id = 1;
}


// --- 查詢與分析 ---
message SearchRequest {
  string query_text = 1; // 自然語言查詢
  int32 top_k = 2; // 返回最相關的結果數量
  // 可選：指定時間點進行歷史查詢
  optional google.protobuf.Timestamp as_of_time = 3;
}

message SearchResponse {
  string summary = 1; // MCP 生成的情報摘要
  repeated Node relevant_nodes = 2; // 檢索到的相關節點
  Graph subgraph = 3; // 圍繞相關節點擴展的子圖
  string suggested_next_step = 4;
}

message ImpactAnalysisRequest {
  string project_id = 1;
  string pr_number = 2; // 或 commit_hash
}

message ImpactAnalysisResponse {
  string summary = 1;
  enum RiskLevel {
    LOW = 0;
    MEDIUM = 1;
    HIGH = 2;
  }
  RiskLevel risk_level = 2;
  Graph impact_subgraph = 3;
}


// --- 約束與鎖定 ---
message AcquireLockRequest {
  string target_node_query = 1; // 例如 "File{path:'/app/main.py'}"
  string agent_id = 2;
  string task_id = 3;
}

message AcquireLockResponse {
  bool locked = 1;
  optional LockConflict conflict_details = 2;
}

// ... 其他請求和響應消息 ...


// --- 通用數據結構 ---
message Node {
  string id = 1; // 內部唯一 UUID
  string type = 2; // 如 'Function', 'File'
  google.protobuf.Struct properties = 3; // 存儲所有屬性 (如 name, path, hash)
}

message Edge {
  string id = 1;
  string type = 2; // 如 'CALLS', 'DEPENDS_ON'
  string from_node_id = 3;
  string to_node_id = 4;
  google.protobuf.Struct properties = 5;
}

message Graph {
  repeated Node nodes = 1;
  repeated Edge edges = 2;
}

// ... 其他通用消息 ...
Use code with caution.
Protobuf
3. 核心 API 端點詳解
3.1 IngestProject (異步)
gRPC 方法: rpc IngestProject(IngestProjectRequest) returns (IngestProjectResponse)
REST Gateway: POST /v1/projects/{project_id}/ingest
描述: 觸發對一個 Git 倉儲的完整 ECL 導入管線。這是一個耗時操作，會立即返回一個 task_id。
用途:
CI/CD 在專案初始化時呼叫，建立基線知識圖譜。
開發者手動觸發，對專案進行全量更新。
3.2 Search (同步)
gRPC 方法: rpc Search(SearchRequest) returns (SearchResponse)
REST Gateway: POST /v1/search
描述: 執行核心的混合檢索。接收自然語言查詢，返回一個包含摘要、相關實體和上下文子圖的結構化響應。
用途:
AI 代理的核心入口。在執行任何任務前，先呼叫此 API 來獲取全局上下文和初步情報。
IDE 插件的智能搜索功能。
3.3 RunImpactAnalysis (同步)
gRPC 方法: rpc RunImpactAnalysis(ImpactAnalysisRequest) returns (ImpactAnalysisResponse)
REST Gateway: GET /v1/projects/{project_id}/prs/{pr_number}/impact
描述: 對一個 Pull Request 或 Commit 進行全域影響力分析，返回風險評級和受影響的子圖。
用途:
CI/CD 的強制性檢查門，在合併前自動評估變更風險。
人類開發者在進行程式碼審查時的核心輔助工具。
3.4 AcquireLock (同步, 事務性)
gRPC 方法: rpc AcquireLock(AcquireLockRequest) returns (AcquireLockResponse)
REST Gateway: POST /v1/locks/acquire
描述: 為一個圖譜中的資源（節點）申請鎖定。此操作必須是原子性的。如果資源已被鎖定，會返回衝突信息。
用途:
多代理協作的基礎。任何 AI 代理在執行有潛在衝突的寫入操作前，必須先呼叫此 API。
4. API 使用範例 (AI Agent 視角)
場景: AI 代理接到任務「為 Events collection 新增 organizer 欄位」。
第一步：獲取上下文
Generated python
# 偽代碼
request = mcp_pb2.SearchRequest(query_text="Events data model organizer field")
response = mcp_stub.Search(request)

# AI 代理分析 response.summary 和 response.relevant_nodes
# 發現 'Events' model 已存在於 'packages/cms/src/collections/Events.ts'
Use code with caution.
Python
第二步：申請鎖定
Generated python
request = mcp_pb2.AcquireLockRequest(
    target_node_query="File{path:'packages/cms/src/collections/Events.ts'}",
    agent_id="agent-007",
    task_id="TASK-ADD-ORGANIZER"
)
response = mcp_stub.AcquireLock(request)

if not response.locked:
    # 處理鎖定失敗的邏輯，例如等待或上報
    handle_lock_conflict(response.conflict_details)
Use code with caution.
Python
第三步：執行修改... (省略)
第四步：提交 PR 並等待影響力分析... (CI/CD 觸發)
第五步：釋放鎖
Generated python
# 在 PR 合併後，由 CI/CD 觸發
request = mcp_pb2.ReleaseLockRequest(task_id="TASK-ADD-ORGANIZER")
mcp_stub.ReleaseLock(request)
