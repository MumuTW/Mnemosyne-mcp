// Mnemosyne MCP - 初始化種子數據
// 這個腳本會在 FalkorDB 啟動時自動執行，創建測試節點和邊

// 創建測試文件節點
CREATE (:File {
    id: "file_001",
    path: "/app/main.py",
    name: "main.py",
    hash: "abc123def456",
    created_at: datetime(),
    updated_at: datetime()
});

// 創建測試函數節點
CREATE (:Function {
    id: "func_001",
    name: "main",
    file_path: "/app/main.py",
    line_start: 1,
    line_end: 10,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (:Function {
    id: "func_002",
    name: "helper_function",
    file_path: "/app/main.py",
    line_start: 12,
    line_end: 20,
    created_at: datetime(),
    updated_at: datetime()
});

// 創建函數調用關係
MATCH (f1:Function {id: "func_001"}), (f2:Function {id: "func_002"})
CREATE (f1)-[:CALLS {
    created_at: datetime(),
    call_type: "direct"
}]->(f2);

// 創建文件包含關係
MATCH (file:File {id: "file_001"}), (func1:Function {id: "func_001"}), (func2:Function {id: "func_002"})
CREATE (file)-[:CONTAINS]->(func1),
       (file)-[:CONTAINS]->(func2);

// 創建測試約束（為 Sprint 3 準備）
CREATE (:Constraint {
    id: "constraint_001",
    type: "IMMUTABLE_LOGIC",
    description: "Core main function should not be modified",
    severity: "HIGH",
    created_at: datetime(),
    active: true
});

// 將約束應用到主函數
MATCH (c:Constraint {id: "constraint_001"}), (f:Function {id: "func_001"})
CREATE (c)-[:APPLIES_TO]->(f);

// 驗證數據創建成功
MATCH (n) RETURN labels(n) as NodeType, count(n) as Count;
