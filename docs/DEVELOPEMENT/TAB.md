Mnemosyne MCP - 技術架構藍圖 (TAB) v2.0 (gRPC-First)
文件版本	2.0
狀態	定義 (Defined)
架構師	AI Assistant & Project Lead
核心原則	gRPC-First、微核心、插件化、事件驅動、Schema-First
1. 總體架構概覽 (gRPC-First High-Level Architecture)
在這個新架構中，gRPC 伺服器成為了所有內部服務邏輯的直接入口，而 REST API 則是一個面向外部 Webhook 和簡易客戶端的「轉譯層」。
Generated mermaid
graph TD
    subgraph "外部系統 (External Systems)"
        A[Git Repository]
        B[CI/CD Pipeline]
        C[IDE Plugin]
        D[AI Agent / Human User]
    end

    subgraph "Mnemosyne MCP Core Service"
        E[**gRPC Server (核心入口)**]
        F[REST Gateway (兼容層)]

        E --> G[異步任務隊列]
        E --> H[查詢引擎]
        E --> I[ECL 管線管理器]

        G --> J((Worker Pool))
        J --> I & K & L

        H --> M[查詢模板庫]
        M --> N[查詢抽象層 (GraphStoreClient)]

        I --> O[ECL Stages: Extract]
        O --> P[ECL Stages: Cognify]
        P --> K[LLM 能力中心]
        P --> Q[ECL Stages: Load]
        Q --> N

        L[鎖定與事務管理器] --> N
    end

    subgraph "插件生態系統 (Plugin Ecosystem)"
        direction LR
        subgraph "數據庫驅動"
            Y[FalkorDB Driver]
        end
    end

    subgraph "核心數據存儲"
        AA[FalkorDB]
    end

    A -- "Webhook (REST)" --> F -- "內部gRPC呼叫" --> E
    B -- "Webhook (REST)" --> F -- "內部gRPC呼叫" --> E
    C -- "gRPC (Streaming)" --> E
    D -- "gRPC (優先)" --> E

    N --> Y
    Y --> AA

    linkStyle 2,3,4,5,6,7,8,9,10,11,12,13,14 stroke-width:1px,stroke:grey,fill:none;
    linkStyle 16,17,18 stroke-width:2px,stroke:blue;```

## 2. 核心架構轉變與模組職責更新

### 2.1 **gRPC 伺服器：系統的「心臟」**
*   **職責**:
    1.  **唯一的業務邏輯入口**: 所有核心功能，如 `IngestProject`, `GetImpactAnalysis`, `AcquireLock` 等，都首先被定義為 gRPC 的服務方法 (RPCs)。
    2.  **處理高性能客戶端**: 直接服務於 AI 代理、IDE 插件等需要低延遲和串流能力的客戶端。
    3.  **編排內部服務**: 接收到 RPC 後，負責將任務分發到異步任務隊列、查詢引擎等後端模組。
*   **技術實現**:
    *   使用 Python 的 `grpcio` 和 `grpcio-tools` 函式庫。
    *   所有服務和消息體都在 `.proto` 文件中嚴格定義，**`.proto` 文件成為了整個系統的 API 契約**。

### 2.2 **REST Gateway：優雅的「翻譯官」與「兼容層」**
*   **職責**:
    1.  **向後兼容**: 為那些不便使用 gRPC 的系統（如簡單的 Webhook）提供一個標準的 HTTP/JSON 接口。
    2.  **簡化 Web 開發**: 為未來可能出現的 Web 管理後台提供一個易於整合的 RESTful API。
*   **技術實現**:
    *   我們依然可以使用 **FastAPI**，但它的角色發生了根本性轉變。
    *   FastAPI 的每個端點處理函數，其內部**只做一件事**：將 HTTP 請求的參數，轉換為對應的 gRPC 請求消息體，然後**通過內部的 gRPC 客戶端 stub，呼叫本地的 gRPC 伺服器**，並將 gRPC 的響應轉換回 JSON 返回。
    *   **示例 (`gateway.py`)**:
        ```python
        import grpc
        from fastapi import FastAPI
        import mcp_pb2
        import mcp_pb2_grpc

        app = FastAPI()
        # 建立到內部 gRPC 服務的 channel
        channel = grpc.insecure_channel('localhost:50051')
        stub = mcp_pb2_grpc.MnemosyneMCPStub(channel)

        @app.post("/v1/check_constraints")
        def check_constraints_http(request_data: MyPydanticModel):
            # 1. 將 HTTP 請求轉換為 gRPC 請求
            grpc_request = mcp_pb2.CheckConstraintsRequest(target_node_id=request_data.node_id)

            # 2. 呼叫核心的 gRPC 服務
            grpc_response = stub.CheckConstraints(grpc_request)

            # 3. 將 gRPC 響應轉換為 HTTP 響應
            return {"status": grpc_response.status, "message": grpc_response.message}
        ```

### 2.3 **開發工作流的調整**
這個架構轉變，將直接影響我們的開發工作流：

1.  **API 設計先行**: **任何新的 API 功能，都必須先在 `.proto` 文件中進行定義。** `.proto` 文件成為了需求和設計的起點。
2.  **自動化程式碼生成**: 在 CI/CD 和本地開發環境中，加入一個步驟，使用 `grpcio-tools` 從 `.proto` 文件自動生成 Python 的伺服器骨架和客戶端 stub。
3.  **核心邏輯實現**: 開發者在生成的伺服器骨架中，填充具體的業務邏輯（呼叫查詢引擎、ECL 管線等）。
4.  **兼容層實現 (可選)**: 如果需要，再為新的 gRPC 接口實現對應的 REST Gateway 端點。

## 3. gRPC-First 架構的戰略優勢

採用這種「gRPC 為核心」的架構，將為 Mnemosyne MCP 帶來巨大的長期優勢：

1.  **性能最大化**: 系統的核心通信路徑被設計為最高效的路徑。所有需要高性能的內部和外部客戶端，都能享受到 gRPC 的全部好處。
2.  **架構清晰**: 職責劃分變得極其清晰。gRPC 伺服器負責**「做什麼（業務邏輯）」**，REST Gateway 負責**「怎麼說（協議轉換）」**。這種分離使得兩部分可以獨立演進和優化。
3.  **契約驅動開發**: `.proto` 文件作為中心契約，強制性地保證了 API 的一致性和類型安全，極大減少了不同服務或客戶端之間的整合問題。
4.  **面向未來**: 這種架構天然地支持構建一個**真正的分散式微服務系統**。未來，如果我們想將「查詢引擎」或「ECL 管線」拆分為獨立的微服務，它們之間也可以繼續使用高效的 gRPC 進行通信，而無需大的架構改動。
