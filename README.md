# Mnemosyne MCP

[![CI](https://github.com/your-username/Mnemosyne-mcp/workflows/CI/badge.svg)](https://github.com/your-username/Mnemosyne-mcp/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> 主動的、有狀態的軟體知識圖譜引擎

Mnemosyne MCP 是一個為 AI 代理和人類開發者設計的**「全知開發夥伴」**，通過將軟體專案的所有元素模型化為即時的、可查詢的知識圖譜，為開發的每一個環節提供精準的上下文、預測性的洞察和強制性的護欄。

## 🚀 快速開始

### 前置需求

- Docker & Docker Compose
- Python 3.10+
- Poetry (用於開發)

### 一鍵啟動

```bash
# 複製環境配置
cp .env.example .env

# 啟動所有服務
docker-compose up -d

# 檢查服務狀態
docker-compose ps
```

服務啟動後，您可以訪問：

- **API 服務**: http://localhost:8000
- **健康檢查**: http://localhost:8000/health
- **FalkorDB Browser**: http://localhost:3000
- **API 文檔**: http://localhost:8000/docs

### 開發環境設置

```bash
# 快速設置開發環境
make dev-setup

# 或手動安裝依賴
pip3 install -r requirements-dev.txt

# 運行系統診斷
make doctor

# 啟動開發服務器
make serve

# 運行測試
make test

# 代碼格式化
make format

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
poetry run pytest

# 運行特定類型的測試
poetry run pytest -m unit
poetry run pytest -m integration
poetry run pytest -m e2e

# 生成覆蓋率報告
poetry run pytest --cov=src/mnemosyne --cov-report=html
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
