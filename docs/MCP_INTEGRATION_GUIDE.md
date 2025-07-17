# Mnemosyne MCP 整合指南

## 概述

Mnemosyne MCP 適配器讓 Mnemosyne 知識圖譜引擎能夠與 Claude Desktop 等 Model Context Protocol (MCP) 客戶端無縫整合。通過 FastMCP 框架實作，提供標準的 JSON-RPC over stdio 通訊協議。

## 快速開始

### 1. 環境設置

確保已安裝所有依賴：

```bash
# 安裝依賴
uv sync

# 驗證安裝
python scripts/test_mcp_simple.py
```

### 2. 啟動 MCP 伺服器

#### 方法一：使用 CLI 命令
```bash
# 基本啟動
mnemo serve-mcp

# 除錯模式
mnemo serve-mcp --debug
```

#### 方法二：直接執行 Python 模組
```bash
python -m mnemosyne.mcp_adapter.server
```

### 3. 配置 Claude Desktop

在 `~/.claude/claude_desktop_config.json` 中新增：

```json
{
  "mcpServers": {
    "mnemosyne": {
      "command": "mnemo",
      "args": ["serve-mcp"],
      "env": {
        "PYTHONPATH": "/path/to/your/Mnemosyne-mcp/src"
      }
    }
  }
}
```

## 可用工具

### 1. search_code - 程式碼搜尋
在知識圖譜中搜尋相關程式碼片段。

**使用範例：**
```
@mnemosyne search_code("user authentication functions", 10)
```

**參數：**
- `query` (string): 搜尋查詢（自然語言或關鍵字）
- `limit` (int, 可選): 返回結果數量，預設 10，範圍 1-50

### 2. analyze_impact - 影響分析
分析程式碼變更對專案的影響範圍和風險等級。

**使用範例：**
```
@mnemosyne analyze_impact("backend-api", "PR-123")
```

**參數：**
- `project_id` (string): 專案識別符
- `pr_number` (string, 可選): Pull Request 編號

### 3. health_status - 系統健康檢查
檢查 Mnemosyne 系統各組件的運行狀態。

**使用範例：**
```
@mnemosyne health_status()
```

### 4. get_system_info - 系統資訊
獲取系統概覽、功能說明和使用指南。

**使用範例：**
```
@mnemosyne get_system_info()
```

## 系統架構

### 雙層架構設計

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  MCP Adapter    │    │   gRPC Core     │
│  (Claude etc.)  │◄──►│  (FastMCP)      │◄──►│  (現有系統)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
     JSON-RPC                JSON-RPC                gRPC
     over stdio              ↔ gRPC                Protocol
```

### 核心組件

1. **FastMCP 伺服器** (`mcp_adapter/server.py`)
   - 處理 MCP 協議通訊
   - 管理工具註冊和生命週期

2. **gRPC 橋接器** (`mcp_adapter/grpc_bridge.py`)
   - 連線池管理
   - 協議轉換 (JSON ↔ Protobuf)
   - 錯誤處理和重試

3. **工具定義** (`mcp_adapter/tools.py`)
   - MCP 工具註冊
   - 參數驗證
   - 回應格式化

## 故障排除

### 常見問題

#### 1. gRPC 連線失敗
**症狀：** 工具呼叫返回「服務暫時無法使用」

**解決方案：**
```bash
# 檢查系統狀態
mnemo doctor

# 啟動 gRPC 後端
mnemo serve

# 檢查端口
netstat -an | grep 50052
```

#### 2. Claude Desktop 無法連線
**症狀：** Claude Desktop 顯示 MCP 伺服器連線錯誤

**解決方案：**
1. 檢查配置檔案路徑：`~/.claude/claude_desktop_config.json`
2. 驗證命令路徑：`which mnemo`
3. 測試伺服器啟動：`mnemo serve-mcp --debug`

#### 3. 權限問題
**症狀：** 命令執行失敗，權限拒絕

**解決方案：**
```bash
# 確保執行權限
chmod +x $(which mnemo)

# 檢查 Python 路徑
echo $PYTHONPATH
```

### 除錯模式

啟用詳細日誌：

```bash
# 除錯模式啟動
mnemo serve-mcp --debug

# 查看日誌
tail -f ~/.claude/logs/mcp_server.log
```

## 開發指南

### 新增自定義工具

1. 在 `tools.py` 中新增工具函數：

```python
@mcp.tool()
@mcp_tool_wrapper
async def my_custom_tool(param1: str, param2: int = 10) -> str:
    """
    自定義工具描述

    Args:
        param1: 參數 1 描述
        param2: 參數 2 描述，預設 10

    Returns:
        工具執行結果
    """
    # 實作邏輯
    result = await bridge.some_grpc_method(param1, param2)
    return format_result(result)
```

2. 在 `register_tools` 函數中會自動註冊新工具。

### 擴展 gRPC 服務

1. 更新 `proto/mcp.proto` 新增 RPC 定義
2. 重新生成 Python 程式碼：
   ```bash
   python -m grpc_tools.protoc --proto_path=proto \
     --python_out=src/mnemosyne/grpc/generated \
     --grpc_python_out=src/mnemosyne/grpc/generated \
     proto/mcp.proto
   ```
3. 在 `grpc_bridge.py` 中新增橋接方法

### 測試新功能

```bash
# 執行基本功能測試
python scripts/test_mcp_simple.py

# 執行完整協議測試（需要後端運行）
python scripts/test_mcp_protocol.py
```

## 效能優化

### 連線池設定

在 `grpc_bridge.py` 中調整連線參數：

```python
options = [
    ('grpc.keepalive_time_ms', 30000),
    ('grpc.keepalive_timeout_ms', 5000),
    ('grpc.keepalive_permit_without_calls', True),
]
```

### 快取策略

對於頻繁查詢，可以在 `grpc_bridge.py` 中新增快取：

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query: str, limit: int) -> dict:
    # 快取搜尋結果
    pass
```

## 安全考量

### 輸入驗證

所有工具都使用 `validate_tool_params` 裝飾器進行參數驗證：

```python
@validate_tool_params(
    query=lambda x: (validate_non_empty_string(x), validate_query_length(x)),
    limit=validate_positive_integer
)
```

### 錯誤處理

敏感資訊不會洩露到錯誤訊息中：

```python
except Exception as e:
    logger.error("Internal error", error=str(e))
    return "⚠️ 內部錯誤，請聯繫管理員"
```

## 更新日誌

### Sprint 5 (v0.1.0)
- ✅ FastMCP 適配器實作
- ✅ gRPC 橋接器
- ✅ 4 個核心工具
- ✅ CLI 整合
- ✅ 錯誤處理和降級機制

## 支援與回饋

如遇問題或需要功能增強：

1. 執行系統診斷：`mnemo doctor`
2. 查看日誌檔案
3. 建立 Issue 回報問題
4. 提供詳細的錯誤訊息和環境資訊
