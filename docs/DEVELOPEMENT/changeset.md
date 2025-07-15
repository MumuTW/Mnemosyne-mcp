Mnemosyne MCP - 變更集與約束手冊 (v1.0)
文件版本	1.0
狀態	草案 (Draft)
目標讀者	架構師、DevOps 工程師、AI 代理開發者
核心目標	定義一個標準化的、可自動執行的變更審查與約束強制流程。
1. 概述
本手冊定義了 Mnemosyne MCP 如何處理和驗證程式碼變更。核心概念包括：
變更集 (ChangeSet): 一個描述程式碼變更的結構化數據對象。
約束 (Constraint): 一個定義在知識圖譜中的、程式碼必須遵守的規則。
工作流 (Workflow): 一個自動化的流程，用於在 CI/CD 中使用 ChangeSet 來驗證 Constraint。
2. 變更集 (ChangeSet) 的結構
ChangeSet 是 MCP 理解一個 Pull Request 的核心數據結構。它是在 CI/CD 流程中，由 MCP 的 pr-check 命令通過比對分支差異而動態生成的。
2.1 JSON Schema 定義 (changeset.schema.json)
Generated json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Mnemosyne MCP ChangeSet",
  "type": "object",
  "properties": {
    "pr_id": { "type": "string" },
    "source_branch": { "type": "string" },
    "target_branch": { "type": "string" },
    "author": { "type": "string" },
    "generated_at": { "type": "string", "format": "date-time" },
    "changes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "change_type": { "enum": ["ADDED", "MODIFIED", "DELETED", "RENAMED"] },
          "entity_type": { "enum": ["File", "Function", "Class", "..."] },
          "entity_id": { "type": "string" }, // 圖譜中的內部 UUID
          "before": { "type": ["object", "null"] }, // 變更前的屬性快照
          "after": { "type": ["object", "null"] }  // 變更後的屬性快照
        },
        "required": ["change_type", "entity_type", "entity_id"]
      }
    }
  },
  "required": ["pr_id", "changes"]
}
Use code with caution.
Json
2.2 ChangeSet 與 Git PR 的映射 (Mapping)
當 mnemo pr-check 运行时，它会：
使用 git diff --name-status <target_branch>...<source_branch> 獲取變更的檔案列表。
對於每個變更的檔案，觸發 ECL 管線的 Cognify 階段，解析出變更的 Function, Class 等細粒度實體。
在知識圖譜中查詢這些實體的變更前狀態 (before)。
將解析出的變更後狀態 (after) 與之對比，生成 changes 陣列。
3. 約束 (Constraint) 的類型庫與範例
約束是在知識圖譜中定義的 (:Constraint) 節點，它們通過 [:APPLIES_TO] 邊與受其影響的節點關聯。
3.1 核心約束類型庫
約束類型 (type)	描述	應用場景
IMMUTABLE_LOGIC	核心邏輯不可變。禁止修改目標節點的內部實現（可以新增，但不能修改或刪除）。	保護核心演算法、認證流程、計費邏輯。
DEPRECATION_POLICY	棄用策略。禁止新的程式碼呼叫被標記為 DEPRECATED 的節點。	強制團隊使用新版 API，防止舊技術債擴散。
VERSION_PINNING	依賴版本鎖定。禁止將目標 ThirdPartyPackage 的版本升級到指定範圍之外。	維護 Monorepo 依賴一致性，防止因不兼容升級導致的隱性錯誤。
LICENSE_RESTRICTION	授權限制。禁止在專案中引入具有特定類型（如 GPL, AGPL）授權的第三方套件。	確保產品的商業授權合規性。
ACCESS_CONTROL	存取控制。只有特定角色 (Role) 的開發者才能修改目標節點。	保護敏感的配置文件或安全相關的模組。
3.2 約束的創建與應用 (API 範例)
Generated python
# 範例：鎖定 validateCredentials 函數的邏輯
mcp_client.apply_constraint(
    target_node_query="Function{name:'validateCredentials'}",
    constraint={
        "type": "IMMUTABLE_LOGIC",
        "reason": "Core security function. Requires sign-off from @security-team.",
        "severity": "BLOCKER"
    }
)

# 範例：禁止在 web 應用中使用 GPL 授權的套件
mcp_client.apply_constraint(
    target_node_query="Application{name:'web'}",
    constraint={
        "type": "LICENSE_RESTRICTION",
        "params": { "disallowed_licenses": ["GPL-3.0", "AGPL-3.0"] },
        "severity": "CRITICAL"
    }
)
Use code with caution.
Python
4. 發現違規後的自動化處理工作流
這是將「約束」轉化為「護欄」的關鍵。當 pr-check 發現 ChangeSet 中的變更違反了圖譜中的 Constraint 時，會觸發以下自動化工作流。
4.1 工作流階段
檢測 (Detection):
MCP 的 pr-check 服務遍歷 ChangeSet 中的每一個 change。
對於每個 change，它在知識圖譜中查詢與之相關的 entity_id 是否有任何活動的約束。
如果一個變更（例如，MODIFIED 一個 Function）違反了一個約束（例如，IMMUTABLE_LOGIC），則記錄一次違規 (Violation)。
報告 (Reporting):
MCP 將所有檢測到的 Violations 聚合成一份結構化的 JSON 報告。
使用這個報告，透過 GitHub API 在對應的 Pull Request 上發表評論，清晰地列出所有違規項、違反的規則和修復建議。
將 CI/CD 的檢查狀態設置為 FAILURE，阻止 PR 被合併。
通知 (Notification):
在 PR 評論中，@ 通知在約束中定義的所有者 (owner) 或相關團隊（如 @security-team）。
（進階）將高嚴重性的違規事件推送到團隊的 Slack/Teams 頻道，或自動在 Jira 中創建一個高優先級的 BLOCKER Ticket。
修復與回滾 (Remediation & Rollback):
對於 AI 代理: MCP 的 API 響應會包含結構化的違規信息，AI 代理可以讀取這些信息並嘗試自動修復其程式碼，然後提交一個新的 Commit。
對於人類開發者: 開發者根據 PR 評論中的建議手動修復程式碼。
半自動 Rollback (進階): 對於某些類型的違規，MCP 甚至可以提供一個「建議的修復 patch」。例如，如果一個 PR 錯誤地升級了一個庫的版本，MCP 可以自動生成一個將 package.json 回滾到之前版本的 git diff 內容，供開發者一鍵應用。
