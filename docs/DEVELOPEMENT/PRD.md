Mnemosyne MCP - 產品需求文件 (PRD)
文件版本	2.0
狀態	定義 (Defined)
作者	AI Assistant & Project Lead
更新日期	2025年7月16日
產品代號	Project Mnemosyne (Aletheia Cortex)

1. 產品概述與願景 (Introduction & Vision)
1.1 問題陳述

AI 編程代理在處理長週期、多模組、多分支的複雜軟體專案時，普遍存在「上下文失憶」問題。它們缺乏對專案全局結構、歷史演進、團隊約束和潛在副作用的理解，導致頻繁出現重複開發、破壞架構、引入依賴衝突和產生「殭屍程式碼」等問題，極大地消耗了開發資源並增加了技術債。

1.2 解決方案：Mnemosyne MCP

Mnemosyne MCP 是一個主動的、有狀態的軟體知識圖譜引擎，旨在成為 AI 代理和人類開發者的**「全知開發夥伴 (Omniscient Development Partner)」。它通過將軟體專案的所有元素（程式碼、依賴、變更歷史、工作流、團隊約束）模型化為一個即時的、可查詢的知識圖譜，為開發的每一個環節提供精準的上下文、預測性的洞察和強制性的護欄**。

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

場景三：清理技術債務 - MCP 自動檢測並報告因程式碼刪除而產生的孤兒資源（如無效的 schema、未使用的 hooks）和長期存在的殭屍程式碼。

場景四：化解併發與依賴衝突 - MCP 透過事務性鎖定協調多代理的並行操作，並在 CI/CD 階段自動檢測跨分支的依賴版本不一致問題。

3. 核心功能與需求 (Features & Requirements)
3.1 (P0) 統一知識圖譜引擎

F-1.1 (增量導入管線): 提供一個可配置的 ECL (Extract→Cognify→Load) 管線，支持從本地 Git 倉儲增量式地、非破壞性地更新知識圖譜。

Cognify 階段必須支持可插拔的 AST 解析器，以適應不同程式語言。

F-1.2 (豐富的 Schema): 圖譜需能模型化以下實體和關係：

程式碼實體: Workspace, Application, Package, File, Class, Function, ThirdPartyPackage, PackageVersion。

開發流程實體: Commit, Branch, PullRequest, Ticket, ApiEndpoint。

約束與狀態實體: Constraint (包含類型、原因、所有者), Lock。

關係: CALLS, DEPENDS_ON, DEFINES_MODEL, USES_TECHNOLOGY, MODIFIES, APPLIES_TO, IS_LOCKED_BY。

F-1.3 (雙時標模型): 所有代表狀態的邊和屬性變更，都必須記錄事件時間 (Valid Time) 和攝取時間 (Ingestion Time)，支持歷史狀態回溯查詢。

3.2 (P0) 智能查詢與分析 API

F-2.1 (混合檢索 API): 提供 search() 端點，能夠在一次呼叫中，結合向量語義搜索、關鍵字搜索和圖遍歷，返回經過上下文豐富的結果。

F-2.2 (自省式工具 API): 提供一組高層次的、基於圖譜推理的 API，作為 AI 代理的核心工具集。

get_impact_analysis(change_set): 預測一個變更集的下游影響半徑。

check_constraints(target_node): 檢查一個節點是否受到任何活動約束。

detect_orphans(change_set): 檢測因刪除操作而產生的孤兒資源。

detect_dependency_conflicts(): 檢測全局的第三方依賴版本衝突。

F-2.3 (事務性鎖定 API): 提供 acquire_lock() 和 release_lock() 端點，用於協調多代理的併發操作。API 必須保證原子性。

3.3 (P0) 可視化與開發者體驗

F-3.1 (本地化 UI): 提供一個與後端服務一併啟動的、基於 FalkorDB-Browser 的本地 Web UI。

F-3.2 (核心功能可視化): UI 必須支持：

互動式地探索整個專案的知識圖譜。

執行 Cypher 查詢並將結果視覺化。

高亮顯示影響力分析、孤島檢測等核心分析的結果。

F-3.3 (智能命令行工具 mnemo): 提供一個 CLI 工具，用於專案初始化、環境診斷和與 MCP 服務的快速互動。

mnemo init: 提供基於智慧預設 (Smart Preset) 的配置模板（如 openai-default, gemini-pro, cost-sensitive），簡化新手入門。

mnemo doctor: 自動診斷用戶環境和配置，並給出優化建議。

mnemo config eject: 允許進階用戶從模板「彈出」，獲得完整的配置控制權。

3.4 (P1) 進階功能

F-4.1 (人類在環審核): 對於低置信度的 LLM 抽取結果，將其標記為「待審核」，並在 UI 中提供審核隊列，由人類進行確認。

F-4.2 (CI/CD 深度整合): 提供官方的 GitHub Action，將 pr-check（包含所有分析功能）等命令無縫整合到開發工作流中。

F-4.3 (IDE 插件): 開發 VS Code 插件，在開發者編寫程式碼時，即時提供來自 MCP 的上下文警告和洞察。

4. 技術棧與架構 (MVP)
層級	技術選擇	理由
核心引擎	FalkorDB	性能卓越，AI 原生（內建向量/全文檢索），openCypher 兼容，內建視覺化，SSPLv1 授權在 MVP 階段風險可控。
應用框架	Python 3.10+ / FastAPI	開發效率高，性能優越，與 AI 生態無縫整合。
數據模型/配置	Pydantic V2	實現 Schema-First 和類型安全的「智慧預設」配置系統。
核心架構	微核心 + 插件化	確保長期可擴展性。核心只包含抽象介面和管線框架，所有驅動、解析器、LLM Provider 均為插件。
部署方式	Docker Compose	一鍵啟動 MCP 服務、FalkorDB 和視覺化介面。
5. 成功指標與衡量 (Success Metrics)

核心價值指標:

孤島檢測率: 在基準專案中，成功識別出已知孤兒資源的百分比 > 95%。

衝突攔截率: 在模擬的併發衝突場景中，成功阻止不安全合併的百分比 > 99%。

影響力分析準確率: 預測的影響範圍與手動分析結果的重合度（召回率/精確率）。

開發者體驗指標:

首次洞察時間 (Time-to-first-insight): 新用戶從安裝到在 UI 中看到自己專案的知識圖譜，所需時間 < 15 分鐘。

Net Promoter Score (NPS): 針對早期使用者進行問卷調查，衡量產品推薦意願。

6. 風險與緩解策略 (Risks & Mitigation)
風險類型	具體風險	緩解策略
技術風險	FalkorDB 生態系統（如 OGM）相對不成熟。	採用「查詢模板庫」模式，減少對 OGM 的依賴；預留時間進行必要的工具鏈開發。
產品風險	過於複雜的配置（能力驅動）可能勸退新手。	採用「智慧預設 + 雙層配置」設計，為新手提供極簡體驗，同時賦予專家完全的靈活性。
商業風險	FalkorDB 的 SSPLv1 授權限制了未來的 SaaS 商業模式。	1. 專注於內部工具和開源社群，暫不考慮 SaaS；2. 從一開始就設計好「查詢抽象層」，保留未來遷移到其他資料庫（如 NebulaGraph）的技術可行性。
7. 發布範圍 (Scope) - MVP
7.1 包含範圍 (In Scope)

所有 P0 級別的功能。

實現對 Python 和 TypeScript/JavaScript 專案的導入支持。

提供一個 FalkorDBDriver。

提供針對 OpenAI 和 OpenRouter（免費模型）的 LLMProvider 插件和對應的智慧預設模板。

提供一份詳盡的端到端教程，指導用戶如何使用 Mnemosyne MCP 分析一個開源專案。

7.2 不包含範圍 (Out of Scope)

除 FalkorDB 外的其他資料庫驅動。

完整的、帶有儀表板的 CI/CD 集成（僅提供可被呼叫的 CLI 命令）。

IDE 插件。

高級的多用戶管理和權限系統。
