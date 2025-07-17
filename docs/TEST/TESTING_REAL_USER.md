# 🎯 真實用戶測試指南

## 模擬真實用戶場景

### 情境：開發者第一次使用 Mnemosyne MCP

#### 第 1 步：發現並安裝

```bash
# 用戶通過 README 發現一鍵安裝命令
claude mcp add mnemosyne-mcp npx @MumuTW/Mnemosyne-mcp
```

**預期結果**：
- Claude Desktop 自動配置 MCP 伺服器
- 無需手動編輯配置檔案

#### 第 2 步：啟動後端服務

用戶需要啟動 Mnemosyne 後端服務來支援 MCP：

```bash
# 克隆專案（真實用戶會這樣做）
git clone https://github.com/MumuTW/Mnemosyne-mcp.git
cd Mnemosyne-mcp

# 設定環境變數（真實用戶會填入自己的 API 金鑰）
cp .env.example .env
# 編輯 .env 填入 OPENAI_API_KEY

# 一鍵啟動（真實用戶期望的簡單性）
make deploy
```

**預期結果**：
- FalkorDB 容器自動啟動
- MCP API 服務在 localhost:8000 運行
- gRPC 服務在 localhost:50051 運行

#### 第 3 步：驗證整合

```bash
# 健康檢查
curl http://localhost:8000/health

# 檢查 API 文檔
open http://localhost:8000/docs
```

#### 第 4 步：在 Claude Desktop 中測試

1. 重啟 Claude Desktop
2. 開啟對話，測試 MCP 功能
3. 嘗試程式碼搜尋和分析功能

## 真實測試步驟

### 準備階段

```bash
# 1. 模擬全新環境
cd /tmp
mkdir mnemosyne-test
cd mnemosyne-test

# 2. 克隆專案
git clone https://github.com/MumuTW/Mnemosyne-mcp.git
cd Mnemosyne-mcp
```

### 配置階段

```bash
# 3. 設定環境變數（真實 API 金鑰）
cp .env.example .env

# 編輯 .env 檔案，添加真實的 OpenAI API 金鑰：
# nano .env
# 取消註釋並填入：OPENAI_API_KEY=sk-your-actual-key
```

### 啟動階段

```bash
# 4. 啟動所有服務
make deploy

# 預期看到：
# ✅ Docker 容器啟動
# ✅ FalkorDB 服務運行
# ✅ MCP API 服務啟動
# ✅ gRPC 服務運行
```

### 驗證階段

```bash
# 5. 檢查服務狀態
make doctor

# 預期輸出：
# ✅ 配置加載成功
# ✅ 資料庫連接正常
# ✅ API 端口可用
# ✅ gRPC 端口可用
```

### MCP 整合階段

```bash
# 6. 安裝 MCP 伺服器
claude mcp add mnemosyne npx @MumuTW/Mnemosyne-mcp

# 7. 測試 MCP 連線
mnemosyne-mcp-server --health-check
```

## 常見用戶問題模擬

### 問題 1：Docker 未安裝

**模擬情境**：新用戶沒有 Docker

**解決方案**：
```bash
# macOS
brew install docker

# 或下載 Docker Desktop
open https://www.docker.com/products/docker-desktop
```

### 問題 2：API 金鑰未設置

**模擬情境**：用戶忘記設置 OPENAI_API_KEY

**檢測方法**：
```bash
make doctor
# 應該顯示警告：❌ OpenAI API 金鑰未設定
```

### 問題 3：端口衝突

**模擬情境**：8000 或 50051 端口被占用

**檢測方法**：
```bash
make doctor
# 應該顯示：⚠️ API 端口 8000 已被占用
```

### 問題 4：Python 版本不符

**模擬情境**：用戶 Python 版本 < 3.10

**檢測方法**：
```bash
python3 --version
# 如果 < 3.10，npm 包應該給出清楚的錯誤提示
```

## 成功標準

### ✅ 技術成功指標

- [ ] `make deploy` 一次成功
- [ ] `make doctor` 全綠燈通過
- [ ] Claude Desktop 可以連接到 MCP 伺服器
- [ ] 可以在 Claude 中使用程式碼搜尋功能

### ✅ 用戶體驗成功指標

- [ ] 從零到運行 < 10 分鐘
- [ ] 無需複雜的手動配置
- [ ] 錯誤訊息清楚且可執行
- [ ] 文檔易懂且完整

## 故障排除檢查清單

### 當 MCP 連線失敗時

```bash
# 1. 檢查後端服務
curl http://localhost:8000/health

# 2. 檢查 gRPC 服務
curl http://localhost:50051  # 應該返回 gRPC 錯誤（正常）

# 3. 檢查 MCP 伺服器
mnemosyne-mcp-server --debug

# 4. 檢查環境變數
echo $OPENAI_API_KEY
```

### 當 Docker 服務異常時

```bash
# 1. 檢查容器狀態
docker ps | grep falkor

# 2. 重啟服務
make docker-down
make docker-up

# 3. 檢查日誌
docker logs $(docker ps -q --filter "name=falkor")
```

---

**目標**：確保任何開發者都能在 10 分鐘內從零開始完成完整的 Mnemosyne MCP 設置。
