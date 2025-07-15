Mnemosyne MCP 在 FalkorDB 上的資料儲存策略
我們的策略將圍繞以下三個核心原則展開：
強制性的核心 Schema (Mandatory Core Schema)：對核心、穩定的實體強制使用標籤和類型。
彈性的擴展屬性 (Flexible Extended Properties)：對易變的、非結構化的元數據使用自由屬性。
語義驅動的索引策略 (Semantics-Driven Indexing)：不僅為查詢加速，更為 AI 理解服務。
1. 強制性的核心 Schema：定義我們的「本體 (Ontology)」
儘管 FalkorDB 是 Schema-optional，但對於 Mnemosyne MCP 這樣一個需要進行精確推理的系統，我們必須主動地、強制地為我們的核心概念定義一個清晰的「本體」。這將通過節點標籤 (Node Labels) 和關係類型 (Relationship Types) 來實現。
核心節點標籤 (Node Labels)：
這將是我們在 Pydantic 中定義的核心實體。每一個實例都必須有一個主標籤。
:CodeEntity: 一個抽象的父標籤，所有與程式碼相關的節點都將繼承它。
:File
:Class
:Function
:ProcessEntity: 描述開發流程的實體。
:Commit
:PullRequest
:Ticket
:ConstraintEntity: 描述治理規則的實體。
:Constraint
:Lock
:DependencyEntity: 描述外部依賴。
:ThirdPartyPackage
好處：使用這種層級化的標籤，我們可以進行非常高效的查詢。例如，MATCH (n:CodeEntity) 可以一次性找出所有與程式碼相關的節點，而無需遍歷整個圖。
核心關係類型 (Relationship Types)：
關係類型必須被指定，因為它定義了圖譜的語義。
:CONTAINS: (File)-[:CONTAINS]->(Function)
:CALLS: (Function)-[:CALLS]->(Function)
:DEPENDS_ON: (Package)-[:DEPENDS_ON]->(ThirdPartyPackage)
:APPLIES_TO: (Constraint)-[:APPLIES_TO]->(Function)
:MODIFIES: (Commit)-[:MODIFIES]->(File)
雙時標實現: 我們將在所有代表狀態變遷的關係上，實現我們的雙時標模型，即在邊的屬性中加入 t_valid_start 和 t_invalid_end。例如，CALLS 關係。
2. 彈性的擴展屬性：利用「無 Schema」的自由度
對於每個節點，除了我們在 Pydantic 中嚴格定義的核心屬性（如 id, name, path），我們應該允許自由地附加非結構化的元數據。
場景: 在 Cognify 階段，LLM 除了能抽取出一個 Function 的名稱和簽名，可能還能總結出一段關於其「複雜度」或「潛在風險」的自然語言描述。
我們的做法: 我們不需要為這些臨時的、非核心的洞察去修改核心 Schema。我們可以直接將它們作為屬性附加到節點上：
Generated cypher
MATCH (f:Function {id: "func-123"})
SET f.llm_summary = "This function uses recursion and may have performance issues under heavy load.",
    f.cyclomatic_complexity_score = 15
Use code with caution.
Cypher
好處:
快速迭代: 我們可以在不修改核心資料模型的情況下，快速地實驗和增加新的 AI 生成的洞察。
靈活性: 能夠容納來自不同工具或不同版本 LLM 的、格式不一的分析結果。
3. 語義驅動的索引策略：為性能和 AI 服務
FalkorDB 強大的索引能力是我們必須充分利用的。我們的索引策略不僅僅是為了加速查詢。
B-Tree 索引 (用於精確匹配):
對所有節點的唯一標識符建立索引，如 File(path)、Function(fully_qualified_name)、Commit(hash)。這是實現快速節點查找的基礎。
全文檢索索引 (Full-Text Search):
對所有包含大量文本的屬性建立全文索引，例如 Commit(message)、Ticket(description)、Function(docstring)。
這將極大地增強我們的混合檢索能力，讓 AI 代理可以通過關鍵字（如 NPE, fix login bug）快速定位相關的開發歷史和程式碼。
向量索引 (Vector Index):
這是我們的核心 AI 能力。我們將對所有具備「語義」的實體創建向量嵌入，並建立 HNSW 索引。
被索引的內容:
Function 的程式碼體和註釋。
Ticket 的標題和描述。
Documentation 檔案的內容片段。
好處: 這使得我們的 Search API 能夠回答非常模糊的、基於意圖的查詢，例如「找到所有與用戶身份驗證流程相關的程式碼」。
總結：一個既嚴謹又靈活的資料儲存模型
綜合以上策略，Mnemosyne MCP 的資料儲存模型將呈現以下特點：
結構化的骨架: 通過強制性的節點標籤和關係類型，我們建立了一個穩定、可靠、易於進行邏輯推理的知識圖譜「骨架」。這是系統可預測性的基礎。
豐富的血肉: 通過靈活的節點屬性，我們允許 AI 和其他工具不斷地為這個骨架附加豐富的、非結構化的「血肉」（元數據、洞察），使其不斷成長和演進。
強大的神經系統: 通過多維度的索引策略（B-Tree, 全文, 向量），我們為這個「數位孿生體」安裝了一個強大的「神經系統」，使其能夠對來自 AI 和人類的各種查詢，做出快速、精準的反應。
