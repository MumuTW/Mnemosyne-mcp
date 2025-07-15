# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 專案概要

Mnemosyne MCP 是一個主動的、有狀態的軟體知識圖譜引擎，採用 gRPC-First 架構，支援 AI 代理和人類開發者進行協作開發。目前已完成 Sprint 0 基礎設施搭建階段。

## 核心架構

### gRPC-First 架構模式
- **gRPC 伺服器**: 核心業務邏輯入口 (port: 50051)
- **REST Gateway**: 外部 HTTP/JSON 兼容層 (port: 8000)  
- **抽象層**: `GraphStoreClient` 介面統一圖資料庫操作
- **驅動層**: FalkorDB 驅動實作具體資料庫操作

### 程式碼架構 (`src/mnemosyne/`)
```
├── api/           # FastAPI REST Gateway
├── core/          # 配置管理、日誌等核心功能  
├── interfaces/    # 抽象介面定義 (GraphStoreClient)
├── drivers/       # 資料庫驅動實作 (FalkorDB)
├── schemas/       # Pydantic 數據模型
└── cli/           # 命令行工具
```

## 開發命令

### 環境設置
```bash
make dev-setup      # 快速設置開發環境
make install        # 安裝依賴套件
make docker-up      # 啟動 FalkorDB 服務
```

### 開發流程
```bash
make serve          # 啟動開發伺服器 (API + CLI)
make doctor         # 系統診斷檢查
make test           # 執行所有測試
make test-unit      # 僅執行單元測試
make ci-check       # CI 流程檢查 (lint + test)
```

### 程式碼品質
```bash
make format         # 格式化程式碼 (black + isort)
make lint           # 執行 lint 檢查 (flake8 + mypy)
```

### 測試與驗證
```bash
make test-cov       # 執行測試並生成覆蓋率報告
make sprint0-verify # Sprint 0 完成狀態驗證
```

## 關鍵配置

### 環境設置
- 主配置：`src/mnemosyne/core/config.py` (Pydantic Settings)
- 環境文件：`.env` (開發) / `configs/{environment}.yaml`
- FalkorDB 預設連接：`localhost:6379`

### API 設計原則
1. **契約優先**: 所有新 API 必須先在 `.proto` 文件中定義
2. **gRPC 核心**: 業務邏輯優先在 gRPC 服務中實作
3. **REST 轉譯**: FastAPI 端點僅進行 HTTP ↔ gRPC 協議轉換

## 開發最佳實踐

### 程式碼規範
- Python 3.10+，使用 black (line-length=88) 格式化
- 型別註解強制要求 (mypy 嚴格模式)
- Pydantic v2 用於數據模型驗證

### 測試策略
- 測試分類：`unit`, `integration`, `e2e` markers
- 27+ 單元測試已全部通過
- 使用 pytest 框架，支援異步測試

### 分支管理
- 主分支：`main`
- 功能分支：`feature/*`
- 使用 Squash & Merge 策略

## 重要文件參考

- **產品需求**: `docs/DEVELOPEMENT/PRD.md`
- **技術架構**: `docs/DEVELOPEMENT/TAB.md` 
- **API 規格**: `docs/DEVELOPEMENT/API.md`
- **Sprint 計劃**: `docs/DEVELOPEMENT/mvp_sprint.md`

## 當前狀態 (Sprint 0 完成)

✅ 基礎設施與抽象層完成  
✅ Docker Compose 環境  
✅ GraphStoreClient 抽象介面  
✅ FalkorDB 驅動整合  
✅ 完整 API 骨架 & 健康檢查  
✅ CLI 工具與開發工具鏈  

下階段：實現第一個 ECL (Extract→Cognify→Load) 閉環