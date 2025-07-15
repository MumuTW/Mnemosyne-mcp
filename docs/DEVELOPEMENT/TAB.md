Mnemosyne MCP - 技術架構藍圖 (TAB) v2.1 (MVP Scope Locked)
文件版本	2.1
狀態	最終版 (Final)
架構師	AI Assistant & Project Lead
核心原則	gRPC-First、微核心、插件化、事件驅動、Schema-First
MVP 焦點	專注於 openai-starter 預設，確保核心體驗的穩定與可靠
1. 總體架構概覽 (MVP-Focused Architecture)
整體架構保持不變，但我們在圖中更清晰地標示出 MVP 階段的焦點實現。
Generated mermaid
graph TD
    subgraph "外部系統 (External Systems)"
        A[Git Repository]
        B[CI/CD Pipeline]
        C["(Future) IDE Plugin"]
        D[AI Agent / Human User]
    end

    subgraph "Mnemosyne MCP Core Service (MVP)"
        E[**gRPC Server (核心入口)**]
        F[REST Gateway (兼容層)]

        E --> G[異步任務隊列 (In-Memory)]
        E --> H[查詢引擎]
        E --> I[ECL 管線管理器]

        G --> J((Worker Pool))
        J --> I & K & L

        H --> M[查詢模板庫]
        M --> N[查詢抽象層 (GraphStoreClient)]

        I --> O[ECL Stages: Extract]
        O --> P[ECL Stages: Cognify]
        P --> K[**LLM 能力中心 (OpenAI-Focused)**]
        P --> Q[ECL Stages: Load]
        Q --> N

        L[鎖定與事務管理器] --> N
    end

    subgraph "插件生態系統 (MVP Scope)"
        direction LR
        subgraph "數據源插件"
            R[Git Extractor]
            S[File System Extractor]
        end
        subgraph "認知插件"
            T[AST Parser (Python/TS)]
        end
        subgraph "LLM 提供者"
            V[**OpenAI Provider (核心實現)**]
        end
        subgraph "資料庫驅動"
            Y[**FalkorDB Driver (核心實現)**]
        end
    end

    subgraph "核心數據存儲 (MVP)"
        AA[FalkorDB]
    end

    A -- "Webhook (REST)" --> F -- "內部gRPC呼叫" --> E
    B -- "Webhook (REST)" --> F -- "內部gRPC呼叫" --> E
    C -- "(Future) gRPC" --> E
    D -- "gRPC / REST" --> E
    K --> V
    N --> Y
    Y --> AA

    linkStyle 2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22 stroke-width:1px,stroke:grey,fill:none;
    linkStyle 24,25,26,27,28,29,30,31,32,33 stroke-width:2px,stroke:blue;```

[~] 架構圖變更說明:
- 明確標示出 IDE Plugin 為未來功能。
- 在插件生態系統中，用粗體高亮 MVP 階段必須實現的核心插件，其他插件（如 GeminiProvider, Neo4jDriver）則被視為未來的擴展。
- LLM 能力中心 被明確標示為 OpenAI-Focused。

## 2. 模組分層與職責定義 (MVP 聚焦版)

### 2.1 gRPC 伺服器 & REST Gateway
[~] 職責更新: 維持不變，但 MVP 階段實現的 RPCs 將嚴格對應 PRD v2.2 中定義的功能集。

### 2.2 異步任務隊列 & Worker Pool
[~] 技術實現確認: MVP 階段確定使用 Python asyncio 和 ThreadPoolExecutor 實現內存隊列。這避免了引入外部依賴（如 Redis），完美契合我們「一鍵啟動」的易用性目標。

### 2.3 ECL 管線管理器
[+] 具體實現細節:
- Extract: 必須實現 GitExtractor（從遠程 URL clone 到臨時目錄）和 FileSystemExtractor（處理本地目錄）。
- Cognify: 必須實現 ASTParser_Python 和 ASTParser_TypeScript 兩個核心認知插件。其輸出將傳遞給 LLM 能力中心。
- Load: 將 Cognify 階段的結果通過 GraphStoreClient 寫入 FalkorDB。

### 2.4 查詢引擎
[+] 查詢模板庫: MVP 階段必須實現 PRD 中所有核心場景對應的查詢模板，例如：find_orphans.cypher, calculate_impact.cypher, check_version_conflict.cypher。這些模板將被硬編碼在程式碼中，供查詢引擎呼叫。

### 2.5 [~] LLM 能力中心 (MVP 核心)
職責: 統一管理所有與 LLM 的交互，並固化 openai-starter 預設。

[~] 技術實現:
- 簡化的配置: 不再需要複雜的 preset 載入邏輯。服務啟動時，直接讀取環境變數 OPENAI_API_KEY。如果未設置，則服務可以啟動，但所有依賴 LLM 的功能將返回錯誤，並在 /health 端點中明確提示。
- 單一 Provider 實現: MVP 階段，我們只實現一個功能完備的 OpenAIProvider 插件。
- 能力硬綁定: 三個核心能力將在程式碼中直接綁定到對應的 OpenAI 模型，無需通過配置文件：
  - generation → gpt-4.1-mini
  - embedding → text-embedding-3-small
  - reasoning → gpt-4.1-nano

## 3. 核心抽象層設計：GraphStoreClient
[~] 狀態: 設計保持不變，但 MVP 階段我們只實現 FalkorDBDriver。Neo4jDriver 等將作為未來擴展的「存根」或接口定義存在，以時刻提醒我們保持抽象層的乾淨。

## 4. 數據模型與 Schema (Pydantic)
[~] 狀態: 保持不變。Pydantic 模型是我們系統的契約，必須在 Sprint 0 就定義好所有 MVP 需要的實體和關係。

## 5. 部署與運維 (MVP)
[~] 狀態: 保持不變。Docker Compose 是我們 MVP 的黃金標準，確保了「一鍵啟動」的承諾。
