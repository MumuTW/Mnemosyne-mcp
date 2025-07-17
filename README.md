# Mnemosyne MCP

[![CI](https://github.com/MumuTW/Mnemosyne-mcp/workflows/CI/badge.svg)](https://github.com/MumuTW/Mnemosyne-mcp/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 主動的、有狀態的軟體知識圖譜引擎

Mnemosyne MCP 是一個為 AI 代理和人類開發者設計的**「全知開發夥伴」**，通過將軟體專案的所有元素模型化為即時的、可查詢的知識圖譜，為開發的每一個環節提供精準的上下文、預測性的洞察和強制性的護欄。

## 🚀 快速開始

### 安裝選項

#### 方式一：一鍵安裝（推薦）

```bash
# 使用 Claude Code 一鍵安裝
claude mcp add mnemosyne-mcp npx @MumuTW/Mnemosyne-mcp

# 或手動安裝
npm install -g @mnemosyne/mcp-server

# 手動配置 Claude Desktop（~/.claude/claude_desktop_config.json）
{
  "mcpServers": {
    "mnemosyne": {
      "command": "npx",
      "args": ["@mnemosyne/mcp-server"]
    }
  }
}
```

#### 方式二：原始碼開發

前置需求：
- Docker & Docker Compose
- Python 3.10+
- uv (Python 套件管理工具)

### 🎯 極簡 4 步驟啟動

**1️⃣ 克隆並設置開發環境**
```bash
git clone https://github.com/your-org/mnemosyne-mcp.git
cd mnemosyne-mcp
make dev-setup
```
自動完成：建立虛擬環境、安裝依賴、生成 .env、建立 logs/ 目錄

**2️⃣ 啟用虛擬環境**
```bash
source .venv/bin/activate
```

**3️⃣ 設定 API 金鑰（可選但建議）**
```bash
cp .env.example .env
# 編輯 .env，填入 OPENAI_API_KEY 或 OPENROUTER_API_KEY
```

**4️⃣ 一鍵啟動所有服務**
```bash
make deploy
```
自動完成：
- 🏗️ 建構 Docker 映像
- 📚 啟動 FalkorDB（圖形資料庫）
- 🚀 啟動 FalkorDB UI（圖形可視化介面）
- ⚡ 啟動 MCP API 服務（提供 /docs 和 /health）

### 🔍 驗證服務狀態

執行完畢後，可直接訪問：
- **FalkorDB UI**: http://localhost:3000 — 圖譜可視化介面
- **MCP API Docs**: http://localhost:8000/docs — Swagger API 文件
- **健康檢查**: http://localhost:8000/health — 服務狀態檢查

### 🎯 導入你的專案（可選）

```bash
mnemo ingest --git https://github.com/example-org/example-repo
```

查詢導入進度：
```bash
mnemo ingest-status <task_id>
```

## 🐳 Docker 一鍵啟動方案

### 📋 前置需求

確保專案根目錄包含以下檔案：
- `docker-compose.yml` - 服務編排配置
- `Dockerfile` - MCP 應用建置檔案
- `.env` - 環境變數設定（包含 API 金鑰）

### 🚀 一鍵啟動

1. **確保 `.env` 包含必要設定**：
   ```bash
   # 至少需要其中一組
   OPENAI_API_KEY=sk-xxx
   # 或
   OPENROUTER_API_KEY=or-xxx
   ```

2. **執行啟動指令**：
   ```bash
   docker-compose up --build
   ```

### 🔍 驗證狀態

啟動完成後，可訪問：
- **圖形 UI**: http://localhost:3000 — FalkorDB 圖譜可視化介面
- **API 文檔**: http://localhost:8000/docs — Swagger API 文件
- **健康檢查**: http://localhost:8000/health — 服務狀態檢查

### 💡 Docker 方案優勢

- **資料持久化**: 使用 `falkor-data` volume 確保重啟不丟資料
- **環境變數管理**: 統一在 `.env` 設定所有配置
- **可擴展性**: 可輕鬆加入 Redis 叢集、副本服務或其他 microservice
- **一鍵部署**: 支援 CI/CD 接入，適合開發/staging/production 環境

## 🛠️ 一鍵部署指令

**🎯 最快速的啟動方式**

1️⃣ **確保你已填寫 `.env`**（或複製 `.env.example`）：
```bash
cp .env.example .env
```

2️⃣ **執行部署指令**：
```bash
make deploy
```

3️⃣ **檢查服務是否成功**：
- 📊 **FalkorDB UI**: http://localhost:3000
- 📚 **MCP API Docs**: http://localhost:8000/docs
- ✅ **健康檢查**: http://localhost:8000/health

---

## ✅ 最終使用體驗（4 行指令完成部署）

```bash
git clone https://github.com/your-org/mnemosyne-mcp.git
cd mnemosyne-mcp
make dev-setup && source .venv/bin/activate
make deploy
```
🎉 **完整的知識圖譜系統 + API + UI 一次啟動完成！**

### 其他開發指令

```bash
# 運行測試
make test

# 代碼格式化
make format

# CI 流程檢查
make ci-check

# 驗證 Sprint 0 完成狀態
make sprint0-verify
```

## 🏗️ 架構概覽

```
src/mnemosyne/
├── api/           # FastAPI 應用和 REST Gateway
├── core/          # 核心業務邏輯
├── interfaces/    # 抽象介面定義
├── drivers/       # 資料庫驅動實作
├── schemas/       # Pydantic 數據模型
└── cli/           # 命令行工具
```

## 📊 當前狀態 (Sprint 0 - 已完成 ✅)

- ✅ 基礎設施搭建完成
- ✅ Docker Compose 環境
- ✅ FalkorDB 整合
- ✅ GraphStoreClient 抽象層
- ✅ 完整的 API 骨架
- ✅ 健康檢查端點
- ✅ 27個單元測試全部通過
- ✅ CLI 工具和開發工具鏈
- ✅ 完整的配置管理系統
- ✅ Pydantic v2 數據模型

## 🔄 開發流程

### Sprint 計劃

- **Sprint 0**: 基礎設施與核心抽象層搭建 ✅
- **Sprint 1**: 數據的「生」與「現」- 實現第一個 ECL 閉環
- **Sprint 2**: AI 的「靈魂注入」- 混合檢索與核心工具
- **Sprint 3**: 治理與約束 - 建立「安全護欄」

### 貢獻指南

1. Fork 專案
2. 創建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

## 🧪 測試

```bash
# 運行所有測試
make test

# 運行特定類型的測試
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m e2e

# 生成覆蓋率報告
make test-cov
```

## 📝 文檔

詳細文檔請參考 `docs/` 目錄：

- [產品需求文件 (PRD)](docs/DEVELOPEMENT/PRD.md)
- [技術架構藍圖 (TAB)](docs/DEVELOPEMENT/TAB.md)
- [API 規格](docs/DEVELOPEMENT/API.md)
- [數據模型](docs/DEVELOPEMENT/data_schema.md)
- [開發計劃](docs/DEVELOPEMENT/mvp_sprint.md)

## 📄 授權

本專案採用 MIT 授權 - 詳見 [LICENSE](LICENSE) 文件。

## 🤝 支援

如有問題或建議，請：

1. 查看 [Issues](https://github.com/your-org/mnemosyne-mcp/issues)
2. 創建新的 Issue
3. 聯繫開發團隊

---

**Mnemosyne MCP** - 讓軟體開發變得更智能、更安全、更高效。
