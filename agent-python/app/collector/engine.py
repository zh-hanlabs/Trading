import logging
import time
from datetime import datetime

from app.collector.backfill import BackfillService
from app.collector.clock import TradingClock
from app.collector.eastmoney import EastMoneyClient
from app.collector.models import SectorSnapshot
from app.collector.storage import SnapshotStorage

logger = logging.getLogger("trading.collector.engine")


class CollectorEngine:
    """A 股资金流分钟级采集与增量计算总引擎"""

    def __init__(
        self,
        client: EastMoneyClient | None = None,
        storage: SnapshotStorage | None = None,
        clock: TradingClock | None = None,
        backfill: BackfillService | None = None,
    ):
        self.client = client or EastMoneyClient()
        self.storage = storage or SnapshotStorage()
        self.clock = clock or TradingClock()
        self.backfill = backfill or BackfillService(
            client=self.client, storage=self.storage, clock=self.clock
        )

        # 内存状态缓存: sector_code -> 上一分钟 main_net_inflow
        self.prev_inflows: dict[str, float] = {}
        self.is_running = False

    def run_startup_check(self) -> None:
        """开机自检：检查今天是否需要迟到开机自愈补数，并恢复内存增量缓存基准"""
        now = self.clock.now()
        today = now.date()
        logger.info(f"执行采集引擎开机自检 (当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')})...")

        if self.clock.is_trading_day(today):
            # 尝试自愈补齐盘中已发生的历史分钟线
            self.backfill.check_and_backfill(today)
            # 加载数据库中最近时刻的主力净流入，恢复内存增量基准
            self.prev_inflows = self.backfill.load_latest_inflow_cache(today)
        else:
            logger.info("当前非交易日，跳过盘中断点自愈检查")

    def run_once(self, target_dt: datetime | None = None) -> list[SectorSnapshot]:
        """单次采集心跳：拉取实时快照、计算本分钟瞬时增量 Δ、落库并更新内存状态

        :param target_dt: 指定时间，主要用于回测与测试
        :return: 本次处理并落库的快照列表
        """
        now_dt = target_dt or self.clock.now()
        cur_time = now_dt.time()
        logger.info(f"开始执行分钟采集轮询 ({now_dt.strftime('%H:%M:%S')})...")

        try:
            snapshots = self.client.fetch_sector_snapshots(
                page_size=100, max_pages=1, target_dt=now_dt
            )
        except Exception as e:  # noqa: BLE001
            logger.error(f"东财公网接口抓取异常: {e}")
            return []


        if not snapshots:
            logger.warning("本次未拉取到任何板块快照数据")
            return []

        # 是否属于早盘开盘第一分钟 (09:30 ~ 09:31)
        is_first_minute = cur_time.hour == 9 and cur_time.minute <= 31

        for s in snapshots:
            code = s.sector_code
            curr_main = s.main_net_inflow

            if code not in self.prev_inflows:
                # 内存中尚无上一分钟记录
                if is_first_minute:
                    # 首根分钟线: 本分钟增量 = 自身累计值
                    delta = curr_main
                else:
                    # 盘中首次捕获到该板块: 本分钟增量置 0，作为后续差值基准
                    delta = 0.0
            else:
                # 正常盘中推进: 本分钟增量 Δ = 当前累计 - 上一点累计
                delta = curr_main - self.prev_inflows[code]

            s.minute_net_inflow = round(delta, 2)
            # 刷新内存中该板块的前值
            self.prev_inflows[code] = curr_main

        # 批量原子性入库
        self.storage.save_snapshots(snapshots)
        logger.info(
            f"完成单次分钟切片处理: {len(snapshots)} 个板块已落库 (快照时间: {now_dt.strftime('%H:%M:%S')})"
        )
        return snapshots

    def start(self) -> None:
        """启动长驻采集调度循环"""
        self.is_running = True
        logger.info("A 股板块资金流采集引擎正式启动！")

        self.run_startup_check()

        while self.is_running:
            try:
                now_dt = self.clock.now()

                if self.clock.is_trading_time(now_dt):
                    self.run_once(now_dt)
                    # 采集后计算距离下一整分钟 (:00) 的休眠时长，实现准点对齐
                    sleep_sec = self.clock.seconds_until_next_minute()
                    logger.debug(f"距离下个分钟采集切片还剩 {sleep_sec:.2f} 秒，进入休眠...")
                    time.sleep(sleep_sec)
                elif self.clock.is_midday_break(now_dt):
                    logger.info("当前处于中午休市时段 (11:30~13:00)，休眠 30 秒...")
                    time.sleep(30.0)
                else:
                    # 盘前、盘后或非交易日
                    logger.debug("当前处于非交易时段，休眠 60 秒等待...")
                    time.sleep(60.0)

            except KeyboardInterrupt:
                logger.info("接收到终端中断信号，正在退出采集引擎...")
                self.stop()
                break
            except Exception:
                logger.exception("采集循环发生未捕获异常")
                time.sleep(5.0)



    def stop(self) -> None:
        """停止采集引擎循环"""
        self.is_running = False
        self.client.close()
        logger.info("采集引擎已安全停止。")
