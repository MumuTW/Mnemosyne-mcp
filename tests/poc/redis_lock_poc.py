"""
Redis 分散式鎖定 POC 測試 - 簡化版

基於專家建議的 Redis 整合測試，使用 Mock 實作進行概念驗證。
"""

import asyncio
import time
from typing import Optional


class MockRedisLock:
    """Redis Lock 的 Mock 實作，用於 POC 測試"""

    _locks = {}  # 模擬 Redis 中的鎖

    def __init__(self, name: str, timeout: Optional[float] = None):
        self.name = name
        self.timeout = timeout or 30
        self.acquired_at = None

    async def acquire(
        self, blocking: bool = True, blocking_timeout: Optional[float] = None
    ) -> bool:
        """獲取鎖"""
        # 檢查鎖是否已存在且未過期
        if self.name in self._locks:
            lock_info = self._locks[self.name]
            if time.time() < lock_info["expires_at"]:
                if not blocking:
                    return False
                # 模擬阻塞等待
                if blocking_timeout:
                    await asyncio.sleep(min(blocking_timeout, 0.1))
                    return False
            else:
                # 鎖已過期，清除
                del self._locks[self.name]

        # 獲取鎖
        expires_at = time.time() + self.timeout
        self._locks[self.name] = {
            "owner": id(self),
            "expires_at": expires_at,
            "acquired_at": time.time(),
        }
        self.acquired_at = time.time()
        return True

    async def release(self) -> bool:
        """釋放鎖"""
        if self.name in self._locks:
            lock_info = self._locks[self.name]
            if lock_info["owner"] == id(self):
                del self._locks[self.name]
                return True
        return False


async def test_basic_locking():
    """基本鎖定功能測試"""
    print("🔒 測試基本鎖定功能...")

    lock = MockRedisLock("test_basic_lock", timeout=10)

    # 測試獲取鎖
    acquired = await lock.acquire(blocking=False)
    assert acquired, "Should acquire lock successfully"
    print("✅ 成功獲取鎖")

    # 測試重複獲取失敗
    lock2 = MockRedisLock("test_basic_lock", timeout=10)
    acquired2 = await lock2.acquire(blocking=False)
    assert not acquired2, "Should not acquire same lock twice"
    print("✅ 重複獲取正確失敗")

    # 測試釋放鎖
    released = await lock.release()
    assert released, "Should release lock successfully"
    print("✅ 成功釋放鎖")

    return True


async def test_timeout_behavior():
    """鎖超時行為測試"""
    print("⏰ 測試鎖超時行為...")

    # 創建短超時的鎖
    lock = MockRedisLock("test_timeout_lock", timeout=1)

    acquired = await lock.acquire()
    assert acquired, "Should acquire lock"
    print("✅ 獲取短超時鎖")

    # 等待超時
    await asyncio.sleep(1.5)
    print("⏳ 等待鎖超時...")

    # 嘗試獲取同一資源的鎖
    lock2 = MockRedisLock("test_timeout_lock", timeout=1)
    acquired2 = await lock2.acquire(blocking=False)
    assert acquired2, "Lock should be auto-released after timeout"
    print("✅ 鎖自動超時釋放")

    await lock2.release()
    return True


async def test_concurrent_access():
    """併發訪問測試"""
    print("🚀 測試併發訪問...")

    async def worker(worker_id: int) -> str:
        """工作者函數"""
        lock = MockRedisLock("test_concurrent_lock", timeout=5)

        try:
            acquired = await lock.acquire(blocking=True, blocking_timeout=1)
            if acquired:
                # 模擬工作
                await asyncio.sleep(0.1)
                await lock.release()
                return f"Worker {worker_id} succeeded"
            else:
                return f"Worker {worker_id} timeout"
        except Exception as e:
            return f"Worker {worker_id} error: {e}"

    # 啟動多個併發 worker
    workers = [worker(i) for i in range(5)]
    results = await asyncio.gather(*workers)

    # 分析結果
    successes = [r for r in results if "succeeded" in r]
    timeouts = [r for r in results if "timeout" in r]

    print(f"📊 結果統計: {len(successes)} 成功, {len(timeouts)} 超時")

    # 驗證至少有一些成功
    assert len(successes) > 0, "At least some workers should succeed"
    print("✅ 併發訪問測試通過")

    return True


async def run_redis_poc():
    """運行 Redis POC 測試"""
    print("🚀 開始 Redis 分散式鎖定 POC 測試")
    print("=" * 50)
    print("🔧 使用 Mock Redis 進行 POC 測試")

    tests = [
        test_basic_locking,
        test_timeout_behavior,
        test_concurrent_access,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
            print()
        except Exception as e:
            print(f"❌ 測試失敗: {e}")
            results.append(False)

    # 總結
    passed = sum(results)
    total = len(results)

    print("=" * 50)
    print(f"📊 POC 測試總結: {passed}/{total} 通過")

    if passed == total:
        print("🎉 所有測試通過！Redis 整合 POC 成功")
        print("💡 建議: 在實際實作中使用 redis-py Lock 或 aioredlock")
    else:
        print("⚠️ 部分測試失敗，需要進一步調查")

    return passed == total


if __name__ == "__main__":
    result = asyncio.run(run_redis_poc())
    exit(0 if result else 1)
