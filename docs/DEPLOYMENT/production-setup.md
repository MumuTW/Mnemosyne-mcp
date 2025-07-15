# Mnemosyne MCP 生產環境部署指南

## FalkorDB 生產環境優化

### Memory Overcommit 設定

FalkorDB (基於 Redis) 在生產環境中需要啟用 Memory Overcommit 以確保最佳性能：

```bash
# 1. 設定系統參數
echo 'vm.overcommit_memory = 1' | sudo tee -a /etc/sysctl.conf

# 2. 立即生效
sudo sysctl -p

# 3. 驗證設定
sysctl vm.overcommit_memory
```

### 為什麼需要 Memory Overcommit？

1. **背景保存操作**: FalkorDB 執行 BGSAVE 時會 fork() 子進程
2. **Copy-on-Write**: 子進程初期共享父進程記憶體，只在修改時複製
3. **防止失敗**: 保守的記憶體策略可能導致 fork() 失敗，影響備份

### 其他生產環境建議

```bash
# 禁用 Transparent Huge Pages (THP) - 持久化設定
# 1. 立即禁用
echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# 2. 持久化設定 (重啟後生效)
echo 'echo never > /sys/kernel/mm/transparent_hugepage/enabled' | sudo tee -a /etc/rc.local
sudo chmod +x /etc/rc.local

# 3. 或使用 systemd service (推薦)
sudo tee /etc/systemd/system/disable-thp.service > /dev/null <<EOF
[Unit]
Description=Disable Transparent Huge Pages (THP)
DefaultDependencies=false
After=sysinit.target local-fs.target
Before=mongod.service

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo never > /sys/kernel/mm/transparent_hugepage/enabled'

[Install]
WantedBy=basic.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable disable-thp.service

# 設定 TCP backlog
echo 'net.core.somaxconn = 65535' | sudo tee -a /etc/sysctl.conf

# 設定文件描述符限制
echo 'falkordb soft nofile 65535' | sudo tee -a /etc/security/limits.conf
echo 'falkordb hard nofile 65535' | sudo tee -a /etc/security/limits.conf
```

## 監控與日誌

### 健康檢查端點

```bash
# 檢查服務健康狀態
curl http://localhost:8000/health

# 檢查 FalkorDB 連接
docker exec mnemosyne-falkordb redis-cli ping
```

### 推薦監控指標

- FalkorDB 記憶體使用率
- API 響應時間
- ECL 管線成功率
- 測試覆蓋率趨勢

## Docker 生產配置

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  falkordb:
    image: falkordb/falkordb:2.12.9  # 使用具體版本，避免 latest 標籤風險
    restart: unless-stopped
    sysctls:
      - net.core.somaxconn=65535
    ulimits:
      memlock: -1
    # Docker Compose 記憶體限制語法 (非 Swarm 模式)
    mem_limit: 4G
    mem_reservation: 2G
    # 注意: deploy.resources 僅適用於 Docker Swarm (docker stack deploy)
    # 對於 docker-compose up，請使用 mem_limit 和 mem_reservation
```
