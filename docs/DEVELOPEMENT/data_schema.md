Mnemosyne MCP - 資料 Schema v1.1 (MVP 鎖定版)

這份更新後的 Schema，將在您原有策略的基礎上，進行細化和補充。
## 1. 核心節點標籤 (Node Labels) - 新增與細化

原有的 CodeEntity, ProcessEntity, ConstraintEntity, DependencyEntity 四大類別劃分得非常好，我們將在此基礎上進行細化。

### :CodeEntity
- :Workspace (id, name)
- :Application (id, name, path)
- :Package (id, name, path)
- :File (id, path, content_hash)
- :Class (id, name, fully_qualified_name)
- :Function (id, name, fully_qualified_name, signature, docstring_embedding_id)

### :ProcessEntity
- :Commit (id, hash, message, author, timestamp)
- :PullRequest (id, pr_number, title, status)
- :Ticket (id, ticket_number, title, description, priority, status)
- [+] :Branch (id, name) - 新增: 為了支持「跨分支遺漏問題」的場景。

### :ConstraintEntity
- :Constraint (id, type, params, reason, severity, owner)
- :Lock (id, lock_type, agent_id, task_id, timestamp)

### :DependencyEntity
- :ThirdPartyPackage (id, name, ecosystem) - ecosystem 如 'npm', 'pypi'
- [+] :PackageVersion (id, version_string) - 新增: 為了支持「依賴版本差異」的場景。
## 2. 核心關係類型 (Relationship Types) - 新增與細化

關係是圖譜的靈魂。我們需要更精確地定義它們，並明確哪些需要進行雙時標管理。

### 結構關係 (Structural)
- :CONTAINS ((Workspace)-[:CONTAINS]->(Application))
- :IMPORTS ((File)-[:IMPORTS]->(File))
- :INHERITS_FROM ((Class)-[:INHERITS_FROM]->(Class))

### 行為關係 (Behavioral) - [雙時標]
- :CALLS ((Function)-[:CALLS]->(Function)) - [雙時標]: 函數呼叫關係會隨重構而改變。

### 開發流程關係 (Process)
- :MODIFIES ((Commit)-[:MODIFIES]->(File))
- :ADDRESSES ((Commit)-[:ADDRESSES]->(Ticket))
- :IN_BRANCH ((Commit)-[:IN_BRANCH]->(Branch))
- :HEAD ((Branch)-[:HEAD]->(Commit)) - [+] 新增: 指向分支的最新提交。

### 約束關係 (Constraint)
- :APPLIES_TO ((Constraint)-[:APPLIES_TO]->(:CodeEntity))
- :IS_LOCKED_BY ((:CodeEntity)-[:IS_LOCKED_BY]->(Lock))

### 依賴關係 (Dependency) - [雙時標]
- :DEPENDS_ON ((Package)-[:DEPENDS_ON]->(ThirdPartyPackage))
- :LOCKS_VERSION ((Package)-[:LOCKS_VERSION]->(PackageVersion)) - [+] 新增 & [雙時標]: package.json 中的版本鎖定會改變。
- :VERSION_OF ((PackageVersion)-[:VERSION_OF]->(ThirdPartyPackage)) - [+] 新增

## 3. 版本管理與雙時標實現 (MVP 焦點)

### 3.1 雙時標概念
所有具有狀態變化特性的關係和節點屬性，都需要支持雙時標追蹤：
- **Valid Time (事件時間)**: 實際發生變更的時間（如 commit timestamp）
- **Ingestion Time (攝取時間)**: MCP 發現並記錄此變更的時間

### 3.2 雙時標關係實現
標記為 [雙時標] 的關係將包含以下屬性：
```cypher
// 範例：函數呼叫關係的雙時標
(:Function)-[:CALLS {
  valid_from: "2025-07-15T10:30:00Z",     // 實際程式碼變更時間
  valid_to: null,                         // null 表示仍然有效
  ingested_at: "2025-07-15T11:00:00Z",    // MCP 處理時間
  source_commit: "abc123",                // 來源 commit
  confidence: 0.95                        // AI 解析置信度
}]->(:Function)
```

### 3.3 歷史狀態查詢支持
通過雙時標設計，MCP 能夠回答以下類型的查詢：
- "在 commit X 時，函數 A 都呼叫了哪些函數？"
- "依賴版本 Y 是何時引入的，又是何時被移除的？"
- "檢測 MCP 攝取延遲：哪些變更超過 1 小時才被發現？"

## 4. 彈性的擴展屬性：利用「無 Schema」的自由度
對於每個節點，除了我們在 Pydantic 中嚴格定義的核心屬性（如 id, name, path），我們應該允許自由地附加非結構化的元數據。

### 4.1 AI 洞察擴展場景
在 Cognify 階段，LLM 除了能抽取出一個 Function 的名稱和簽名，可能還能總結出關於其「複雜度」或「潛在風險」的自然語言描述。

### 4.2 動態屬性附加策略
我們不需要為這些臨時的、非核心的洞察去修改核心 Schema。我們可以直接將它們作為屬性附加到節點上：

```cypher
MATCH (f:Function {id: "func-123"})
SET f.llm_summary = "This function uses recursion and may have performance issues under heavy load.",
    f.cyclomatic_complexity_score = 15,
    f.ai_risk_assessment = "medium",
    f.refactoring_suggestions = ["extract nested functions", "add memoization"]
```

### 4.3 好處與優勢
- **快速迭代**: 可以在不修改核心資料模型的情況下，快速實驗和增加新的 AI 生成洞察
- **靈活性**: 能夠容納來自不同工具或不同版本 LLM 的、格式不一的分析結果
- **向後兼容**: 新增的屬性不會影響現有查詢和 API 的穩定性

## 5. 語義驅動的索引策略：為性能和 AI 服務

FalkorDB 強大的索引能力是我們必須充分利用的。我們的索引策略不僅僅是為了加速查詢，更是為了實現智能的混合檢索體驗。

### 5.1 B-Tree 索引 (用於精確匹配)
對所有節點的唯一標識符建立索引，如：
- `File(path)` - 檔案路徑精確查找
- `Function(fully_qualified_name)` - 函數全限定名查找
- `Commit(hash)` - commit 雜湊值查找
- `Package(name)` - 套件名稱查找

這是實現快速節點查找的基礎，確保 API 回應時間 < 50ms。

### 5.2 全文檢索索引 (Full-Text Search)
對所有包含大量文本的屬性建立全文索引：
- `Commit(message)` - commit 訊息關鍵字搜尋
- `Ticket(description)` - 工單描述內容搜尋
- `Function(docstring)` - 函數文檔字符串搜尋
- `File(content)` - 檔案內容全文搜尋（僅限小檔案）

這將極大地增強我們的混合檢索能力，讓 AI 代理可以通過關鍵字（如 "NPE", "fix login bug"）快速定位相關的開發歷史和程式碼。

### 5.3 向量索引 (Vector Index) - AI 核心能力
這是我們的核心 AI 能力。我們將對所有具備「語義」的實體創建向量嵌入，並建立 HNSW 索引。

**被索引的內容:**
- `Function` 的程式碼體和註釋
- `Ticket` 的標題和描述
- `Documentation` 檔案的內容片段
- `Commit` 訊息的語義摘要

**好處:** 這使得我們的 Search API 能夠回答非常模糊的、基於意圖的查詢，例如「找到所有與用戶身份驗證流程相關的程式碼」。

### 5.4 索引建立策略
```cypher
// B-Tree 索引
CREATE INDEX ON :File(path);
CREATE INDEX ON :Function(fully_qualified_name);
CREATE INDEX ON :Commit(hash);

// 全文索引
CALL db.idx.fulltext.createNodeIndex('functionDocstring', ['Function'], ['docstring']);
CALL db.idx.fulltext.createNodeIndex('commitMessage', ['Commit'], ['message']);

// 向量索引 (需要 embedding 屬性)
CALL db.idx.vector.createNodeIndex('functionEmbedding', 'Function', 'embedding', 1536, 'cosine');
```

## 6. MVP 實現重點與限制

### 6.1 MVP 階段實現範圍
- **支援語言**: 專注於 Python 和 TypeScript/JavaScript
- **資料來源**: Git 倉儲和本地檔案系統
- **LLM 整合**: 僅支援 OpenAI (openai-starter 預設)
- **索引策略**: 優先實現 B-Tree 和全文索引，向量索引為次要

### 6.2 效能要求
- **節點查找**: < 50ms (透過 B-Tree 索引)
- **全文搜尋**: < 200ms (中等規模專案)
- **向量搜尋**: < 500ms (用於語義查詢)
- **ECL 處理**: 單檔案 < 2 秒，整個專案 < 5 分鐘

### 6.3 已知限制
- 跨檔案引用解析仍需人工審核
- 複雜的條件邏輯分析準確率約 80%
- 大型專案 (>10k 檔案) 需要分批處理

## 7. 總結：一個既嚴謹又靈活的資料儲存模型

綜合以上策略，Mnemosyne MCP 的資料儲存模型將呈現以下特點：

### 7.1 結構化的骨架
通過強制性的節點標籤和關係類型，我們建立了一個穩定、可靠、易於進行邏輯推理的知識圖譜「骨架」。這是系統可預測性的基礎。

### 7.2 豐富的血肉
通過靈活的節點屬性，我們允許 AI 和其他工具不斷地為這個骨架附加豐富的、非結構化的「血肉」（元數據、洞察），使其不斷成長和演進。

### 7.3 強大的神經系統
通過多維度的索引策略（B-Tree, 全文, 向量），我們為這個「數位孿生體」安裝了一個強大的「神經系統」，使其能夠對來自 AI 和人類的各種查詢，做出快速、精準的反應。

### 7.4 MVP 成功標準
- **資料完整性**: 95% 以上的程式碼實體被正確識別和建模
- **關係準確性**: 90% 以上的函數呼叫關係被正確捕捉
- **查詢效能**: 滿足上述效能要求
- **擴展性**: 支援 1000+ 檔案的中等規模專案

---

**版本歷史**
- v1.0: 初始版本，定義基本 Schema 結構
- v1.1: MVP 鎖定版本，增加雙時標、擴展屬性、索引策略等核心實現細節
