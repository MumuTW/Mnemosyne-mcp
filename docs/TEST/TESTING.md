# 🧪 Mnemosyne MCP 測試指南

## 快速測試設置

### 1. 環境配置

```bash
# 複製測試配置
cp .env.local .env

# 編輯 .env 檔案，至少設定一個 LLM API 金鑰
# nano .env
```

**重要**：請填入您的 API 金鑰（擇一即可）：
- `OPENAI_API_KEY=sk-xxxxxxxxxx`
- `OPENROUTER_API_KEY=or-xxxxxxxxxx`

### 2. 啟動測試環境

```bash
# 方式一：使用 Docker（推薦）
make docker-up          # 啟動 FalkorDB
make serve              # 啟動 MCP 服務

# 方式二：一鍵部署
make deploy             # 包含 Docker + 服務啟動
```

### 3. 驗證服務狀態

```bash
# 系統診斷
make doctor

# 或手動檢查
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## npm 包測試

### 安裝與測試

```bash
# 本地測試 npm 包
cd /path/to/project
npm install -g .

# 測試啟動
mnemosyne-mcp-server --health-check
mnemosyne-mcp-server --debug
```

### Claude Desktop 整合測試

1. **配置 Claude Desktop**：
   ```json
   // ~/.claude/claude_desktop_config.json
   {
     "mcpServers": {
       "mnemosyne": {
         "command": "mnemosyne-mcp-server",
         "env": {
           "GRPC_BACKEND_URL": "localhost:50051",
           "DEBUG": "true"
         }
       }
     }
   }
   ```

2. **重啟 Claude Desktop** 並檢查連線狀態

## 功能測試清單

### ✅ 基礎功能測試

- [ ] **健康檢查**：`curl http://localhost:8000/health`
- [ ] **API 文檔**：訪問 `http://localhost:8000/docs`
- [ ] **資料庫連線**：`make doctor` 顯示綠色 ✅
- [ ] **MCP 伺服器啟動**：`mnemosyne-mcp-server` 無錯誤

### ✅ MCP 整合測試

- [ ] **Claude Desktop 連線**：MCP 伺服器在 Claude 中可見
- [ ] **工具調用**：在 Claude 中可以使用程式碼搜尋功能
- [ ] **gRPC 通訊**：後端服務正常回應

### ✅ 開發工具測試

- [ ] **測試套件**：`make test` 全部通過
- [ ] **程式碼品質**：`make ci-check` 無錯誤
- [ ] **格式化**：`make format` 成功執行

## 常見問題排除

### Python 依賴問題

```bash
# 檢查 Python 版本
python3 --version  # 需要 3.10+

# 重新安裝依賴
uv pip install -e .
# 或
pip install -e .
```

### FalkorDB 連線問題

```bash
# 檢查 Docker 容器狀態
docker ps | grep falkor

# 重啟資料庫
make docker-down
make docker-up
```

### MCP 連線問題

```bash
# 檢查 gRPC 服務
curl http://localhost:50051  # 應該顯示 gRPC 錯誤（正常）

# 檢查伺服器日誌
mnemosyne-mcp-server --debug
```

## 測試數據載入

```bash
# 載入示範資料
make doctor  # 先確保服務正常
mnemo seed --project-name test-project

# 驗證資料
mnemo search "database"
mnemo query "MATCH (n) RETURN count(n) as total"
```

## 效能測試

```bash
# 基本負載測試
curl -X GET "http://localhost:8000/api/v1/search?query=test&limit=10"

# 併發測試（需要 ab 工具）
ab -n 100 -c 10 http://localhost:8000/health
```

## 部署測試

```bash
# Docker 部署測試
docker-compose up --build

# 服務可用性檢查
curl http://localhost:8000/health
curl http://localhost:3000  # FalkorDB UI
```

---

## 🔧 測試環境配置檔案

已創建 `.env.local` 作為測試模板，包含：
- 本地資料庫配置
- 除錯模式啟用
- MCP 測試參數
- 效能調校設定

**重要提醒**：
- ✅ `.env.local` 已在 `.gitignore` 中，不會被提交
- ⚠️ 請勿在版本控制中提交任何包含 API 金鑰的檔案
- 🔒 測試完成後請清理或輪換 API 金鑰
