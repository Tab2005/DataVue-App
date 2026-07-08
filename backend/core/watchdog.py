"""
Event loop 看門狗 + 記憶體曲線記錄（2026-07-08 事故診斷工具）

背景：backend 多次出現「event loop 凍結 → 全站逾時 → 節點過載」，但凍結
當下 app log 全靜默，無法定位卡住的程式碼位置；記憶體亦曾暴衝至 2GB+
而聚合指標無法對齊觸發時刻。

本模組以「獨立的原生 thread」監看 event loop 心跳：
  - loop 上每秒跳一次心跳（asyncio task）；監看 thread 發現心跳落後超過
    LAG_THRESHOLD 秒時，用 faulthandler 將**所有 thread 的完整堆疊**傾印到
    stderr（進入容器日誌）——凍結元兇的檔案/行號會直接出現在 dump 中。
  - 每 RSS_LOG_INTERVAL 秒記錄一次 process RSS（MB），提供帶時間戳的記憶體
    曲線；超過 RSS_ALERT_MB 時改以 WARNING 記錄。

監看 thread 是 daemon、純 stdlib（faulthandler + /proc/self/status），
不依賴 psutil；loop 完全凍結時 thread 仍能運作（GIL 會在 I/O 等待/系統
呼叫時釋放；若 GIL 被純 Python 迴圈長期持有，dump 仍會在片刻間隙執行）。
"""

from __future__ import annotations

import asyncio
import faulthandler
import logging
import sys
import threading
import time

logger = logging.getLogger(__name__)

# loop 心跳間隔（秒）
HEARTBEAT_INTERVAL = 1.0
# 心跳落後多少秒視為凍結（扣除心跳間隔本身）
LAG_THRESHOLD = 3.0
# 監看 thread 檢查頻率（秒）
CHECK_INTERVAL = 5.0
# 堆疊傾印的最小間隔（秒；避免持續凍結時洗版）
DUMP_COOLDOWN = 30.0
# RSS 例行記錄間隔（秒）
RSS_LOG_INTERVAL = 60.0
# RSS 超標門檻（MB；超過改用 WARNING 並提高記錄頻率）
RSS_ALERT_MB = 700

_started = False


def _rss_mb() -> int:
    """讀取目前 process 的 RSS（MB）；非 Linux（本機開發）回 -1。"""
    try:
        with open("/proc/self/status", encoding="ascii") as f:
            for line in f:
                if line.startswith("VmRSS"):
                    return int(line.split()[1]) // 1024
    except (OSError, ValueError, IndexError):
        pass
    return -1


def start_watchdog() -> None:
    """在目前執行中的 event loop 上啟動心跳 task 與監看 thread（冪等）。"""
    global _started
    if _started:
        return
    _started = True

    state = {"beat": time.monotonic()}

    async def _heartbeat() -> None:
        while True:
            state["beat"] = time.monotonic()
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    def _monitor() -> None:
        last_dump = 0.0
        last_rss_log = 0.0
        while True:
            time.sleep(CHECK_INTERVAL)
            now = time.monotonic()
            lag = now - state["beat"] - HEARTBEAT_INTERVAL
            rss = _rss_mb()

            rss_interval = RSS_LOG_INTERVAL if rss < RSS_ALERT_MB else 15.0
            if now - last_rss_log >= rss_interval:
                last_rss_log = now
                if rss >= RSS_ALERT_MB:
                    logger.warning("[Watchdog] RSS=%dMB（超過 %dMB 門檻）", rss, RSS_ALERT_MB)
                else:
                    logger.info("[Watchdog] RSS=%dMB", rss)

            if lag >= LAG_THRESHOLD and now - last_dump >= DUMP_COOLDOWN:
                last_dump = now
                logger.error(
                    "[Watchdog] event loop 心跳落後 %.1f 秒（RSS=%dMB）——"
                    "傾印所有 thread 堆疊以定位凍結點：",
                    lag,
                    rss,
                )
                # 直接寫 stderr（容器日誌），不經 logging（loop 可能已凍結）
                faulthandler.dump_traceback(file=sys.stderr)
                sys.stderr.flush()

    loop = asyncio.get_running_loop()
    loop.create_task(_heartbeat())
    thread = threading.Thread(target=_monitor, daemon=True, name="loop-watchdog")
    thread.start()
    logger.info(
        "[Watchdog] started（lag>%ss dump stacks；RSS 每 %ss 記錄，>%dMB 告警）",
        LAG_THRESHOLD,
        int(RSS_LOG_INTERVAL),
        RSS_ALERT_MB,
    )


__all__ = ["start_watchdog"]
