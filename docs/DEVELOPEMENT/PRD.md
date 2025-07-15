Mnemosyne MCP - 產品需求文件 (PRD)
文件版本	2.2 (MVP Scope Locked)
狀態	最終版 (Final)
作者	AI Assistant & Project Lead
更新日期	2025年7月17日
產品代號	Project Mnemosyne

1. 產品概述與願景 (Introduction & Vision)
1.1 問題陳述

AI 編程代理在處理長週期、多模組、多分支的複雜軟體專案時，普遍存在「上下文失憶」問題。它們缺乏對專案全局結構、歷史演進、團隊約束和潛在副作用的理解，導致頻繁出現重複開發、破壞架構、引入依賴衝突和產生「殭屍程式碼」等問題，極大地消耗了開發資源並增加了技術債。

1.2 解決方案：Mnemosyne MCP

Mnemosyne MCP 是一個主動的、有狀態的軟體知識圖譜引擎，旨在成為 AI 代理和人類開發者的**「全知開發夥伴 (Omniscient Development Partner)」。它通過將軟體專案的所有元素（程式碼、依賴、變更歷史、工作流、團隊約束）模型化為一個即時的、可查詢的知識圖譜，為開發的每一個環節提供精準的上下文、預測性的洞察和強制性的護欄**。

### 1.2.1 核心差異化價值主張

**專為軟體工程而生 (Purpose-Built for Software Engineering)**:
「與通用知識圖譜框架不同，Mnemosyne MCP 深度理解軟體開發的本質。我們將 Git 作為一等公民，利用其內建的版本歷史，來構建一個更輕量、更高效、更具洞察力的知識圖譜。」

**智能的「選擇性時序」模型 (Intelligent Selective Temporality)**:
「我們不會為所有數據都增加不必要的時序開銷。我們只在那些真正反映了狀態變遷的關鍵關係（如依賴版本）上，啟用精細的雙時標追蹤，從而在性能和歷史完整性之間，達到了最佳的平衡。」

**健壯的「優雅降級」機制 (Robust Graceful Degradation)**:
「無論您的專案是託管在公開的 GitHub 上，還是存儲在一個無法訪問的私有伺服器中，Mnemosyne MCP 都能工作。在能獲取 Git 歷史時，它提供全部的深度洞察；在無法獲取時，它依然能作為一個強大的靜態程式碼分析和知識圖譜引擎，為您提供核心價值。」

1.3 產品願景

打造一個**「軟體開發的數位孿生體 (Digital Twin for Software Development)」，讓任何開發活動（無論由 AI 或人類發起）都能在一個完全透明、可預測、受治理**的環境中進行，從而根本性地提升軟體工程的效率、品質和安全性。

2. 目標用戶與核心場景 (Personas & Scenarios)
2.1 用戶畫像

AI 編程代理 (Primary Consumer)：需要上下文來執行複雜任務的自動化程式。

人類開發者/架構師 (Primary Human User)：需要洞察專案全貌、審查變更、定義架構約束的工程師。

DevOps 工程師 (Secondary User)：需要將 MCP 整合到 CI/CD 流程中，並監控專案健康狀況的運維專家。

2.2 核心解決場景 (Top Scenarios)

場景一：避免重複開發 - 在 AI 代理試圖創建新功能前，MCP 主動告知已存在的、語義相似的功能，並建議重用或擴展。

場景二：守護核心架構 - 在 AI 或人類試圖修改被鎖定的核心模組時，MCP 在 IDE、API 和 CI/CD 環節進行多層次攔截和警告。

場景三：清理技術債務 - MCP 自動檢測並報告因程式碼刪除而產生的孤兒資源和長期存在的殭屍程式碼。

場景四：化解併發與依賴衝突 - MCP 透過事務性鎖定協調多代理的並行操作，並在 CI/CD 階段自動檢測跨分支的依賴版本不一致問題。

3. 核心功能與需求 (Features & Requirements)
3.1 (P0) 統一知識圖譜引擎

F-1.1 (增量導入管線): 提供一個可配置的 ECL (Extract→Cognify→Load) 管線，支持從本地 Git 倉儲增量式地、非破壞性地更新知識圖譜。

F-1.2 (豐富的 Schema): 圖譜需能模型化核心的程式碼、開發流程和約束實體及關係。

F-1.3 (雙時標模型): 所有代表狀態的邊和屬性變更，都必須記錄事件時間 (Valid Time) 和攝取時間 (Ingestion Time)，支持歷史狀態回溯查詢。

3.2 (P0) 智能查詢與分析 API (gRPC-First)

F-2.1 (混合檢索 API): 提供 Search() RPC，結合向量語義搜索和圖遍歷，返回經過上下文豐富的結構化響應。

F-2.2 (自省式工具 API): 提供一組基於圖譜推理的高層次 RPC，作為 AI 代理的核心工具集，包括 RunImpactAnalysis(), CheckConstraints() 等。

F-2.3 (事務性鎖定 API): 提供 AcquireLock() 和 ReleaseLock() RPC，用於協調多代理的併發操作，必須保證原子性。

3.3 (P0) LLM 能力中心與智慧預設

F-3.1 (能力驅動架構): MCP 內部將 LLM 呼叫抽象為三種核心能力，以實現靈活性和成本優化：
generation: 負責核心的、複雜的推理與生成任務。
embedding: 負責將文本轉換為向量，專門用於語義搜索。
reasoning: 負責所有輕量級、快速的判斷任務（如分類、重排序）。

F-3.2 (MVP 智慧預設): MVP 版本將內建並默認啟用 openai-starter 預設模板，為用戶提供穩定可靠、成本效益最佳的入門體驗。
generation: 綁定到 gpt-4.1-mini。
embedding: 綁定到 text-embedding-3-small。
reasoning: 綁定到 gpt-4.1-nano。

3.4 (P0) 可視化與開發者體驗

F-4.1 (本地化 UI): 提供一個與後端服務一併啟動的、基於 FalkorDB-Browser 的本地 Web UI。

F-4.2 (核心功能可視化): UI 必須支持互動式圖譜探索、Cypher 查詢視覺化，並能高亮顯示分析結果。

F-4.3 (智能命令行工具 mnemo): 提供一個 CLI 工具。
mnemo init: 自動生成一個使用 openai-starter 預設的項目結構。
mnemo doctor: 診斷用戶環境（特別是 OPENAI_API_KEY 是否設置）。

3.5 (P1) 進階功能

F-5.1 (人類在環審核): 對於低置信度的 LLM 抽取結果，將其標記為「待審核」，並在 UI 中提供審核隊列。

F-5.2 (CI/CD 深度整合): 提供官方的 GitHub Action，將 pr-check 等命令無縫整合到開發工作流中。

F-5.3 (多預設支持): 引入 hacker-cloud-free-tier 等更多智慧預設模板，並提供 mnemo config eject 功能供專家用戶定製。

4. 技術棧與架構 (MVP)
層級	技術選擇	理由
核心引擎	FalkorDB	性能卓越，AI 原生（內建向量/全文檢索），openCypher 兼容，內建視覺化，SSPLv1 授權在 MVP 階段風險可控。
應用框架	Python 3.10+ / FastAPI / gRPC	以 gRPC-First 為核心，提供高性能接口；同時通過 Gateway 提供 RESTful API 以保證兼容性。
數據模型/配置	Pydantic V2	實現 Schema-First 和類型安全的配置系統。
核心架構	微核心 + 插件化	確保長期可擴展性。核心只包含抽象介面和管線框架，所有驅動、解析器、LLM Provider 均為插件。
部署方式	Docker Compose	一鍵啟動 MCP 服務、FalkorDB 和視覺化介面。
5. 成功指標與衡量 (Success Metrics)

核心價值指標:

孤島檢測率: 在基準專案中，成功識別出已知孤兒資源的百分比 > 95%。

衝突攔截率: 在模擬的併發衝突場景中，成功阻止不安全合併的百分比 > 99%。

開發者體驗指標:

首次洞察時間 (Time-to-first-insight): 新用戶從安裝到在 UI 中看到自己專案的知識圖譜，所需時間 < 15 分鐘。

用戶留存率: 早期用戶在完成教程後，第二週仍持續使用的比例。

6. 風險與緩解策略 (Risks & Mitigation)
風險類型	具體風險	緩解策略
技術風險	FalkorDB 生態系統（如 OGM）相對不成熟。	採用「查詢模板庫」模式，減少對 OGM 的依賴；預留時間進行必要的工具鏈開發。
用戶採用風險	對 OpenAI API Key 的依賴可能成為部分用戶（如無信用卡學生）的使用障礙。	在 MVP 成功後，立即將支持 hacker-cloud-free-tier（基於 OpenRouter+Jina）作為最高優先級的功能，以擴大用戶基礎。
商業風險	FalkorDB 的 SSPLv1 授權限制了未來的 SaaS 商業模式。	1. MVP 階段專注於開源社群和產品價值驗證；2. 從一開始就設計好「查詢抽象層」，保留未來遷移到其他資料庫的技術可行性。
7. 發布範圍 (Scope) - MVP
7.1 包含範圍 (In Scope)

所有 P0 級別的功能。

實現對 Python 和 TypeScript/JavaScript 專案的導入支持。

提供一個高性能的 FalkorDBDriver。

提供一個專注於 OpenAI 的 LLMProvider 插件，並內建和默認啟用 openai-starter 智慧預設。

提供一份詳盡的端到端教程，指導用戶如何配置 OpenAI API Key，並使用 Mnemosyne MCP 分析一個開源專案。

7.2 不包含範圍 (Out of Scope)

除 OpenAI 外的其他 LLM Provider 插件。

除 openai-starter 外的其他智慧預設模板。

完整的、帶有儀表板的 CI/CD 集成（僅提供可被呼叫的 CLI 命令）。

IDE 插件。

高級的多用戶管理和權限系統。
