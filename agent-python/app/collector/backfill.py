import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date

from app.collector.clock import TradingClock
from app.collector.eastmoney import EastMoneyClient
from app.collector.models import SectorSnapshot
from app.collector.storage import SnapshotStorage, get_db_connection

logger = logging.getLogger("trading.collector.backfill")


class BackfillService:
    """迟到开机自愈补数服务

    在交易盘中或休盘期（如 12:00 午休）启动系统时，
    检测库中缺失分钟线，并发调取东财日内分时接口回溯补齐，
    并为后续实时采集初始化增量基准状态。
    """

    def __init__(
        self,
        client: EastMoneyClient | None = None,
        storage: SnapshotStorage | None = None,
        clock: TradingClock | None = None,
    ):
        self.client = client or EastMoneyClient()
        self.storage = storage or SnapshotStorage()
        self.clock = clock or TradingClock()

    def check_and_backfill(
        self,
        target_date: date | None = None,
        sector_targets: list[tuple[str, str]] | None = None,
        max_workers: int = 5,
    ) -> int:
        """检查并执行断点自愈补数

        :param target_date: 目标日期，缺省为当前日期
        :param sector_targets: 指定补数的板块清单 [(code, name), ...]，若为空则自动拉取核心板块
        :param max_workers: 并发拉取线程数
        :return: 实际补齐入库的快照条数
        """
        now_dt = self.clock.now()
        cur_date = target_date or now_dt.date()

        if not self.clock.is_trading_day(cur_date):
            logger.info(f"{cur_date} 非交易日，无需自愈补数")
            return 0

        expected_minutes = self.clock.get_expected_minutes_up_to(now_dt)
        if not expected_minutes:
            logger.info(f"{cur_date} 尚未开盘，无需自愈补数")
            return 0

        latest_saved_time = self.storage.get_latest_snapshot_time(cur_date)
        if latest_saved_time is not None and latest_saved_time >= expected_minutes[-1]:
            logger.info(
                f"{cur_date} 数据已是最新 (已记录到 {latest_saved_time})，无需补数"
            )
            return 0

        logger.info(
            f"检测到数据缺失！预期截至 {expected_minutes[-1]}，库中最新为 {latest_saved_time}，启动自愈补数..."
        )

        # 1. 确定需要补数的板块列表
        if not sector_targets:
            try:
                snapshots = self.client.fetch_sector_snapshots(page_size=100, max_pages=1)
                sector_targets = [(s.sector_code, s.sector_name) for s in snapshots]
            except Exception as e:  # noqa: BLE001
                logger.error(f"拉取板块元数据失败，放弃补数: {e}")
                return 0

        logger.info(f"准备对 {len(sector_targets)} 个板块进行日内历史分钟线回溯补齐...")

        # 2. 并发拉取各板块历史分时线并计算每分钟增量 Δ
        all_snapshots: list[SectorSnapshot] = []

        def _fetch_and_build(code: str, name: str) -> list[SectorSnapshot]:
            try:
                klines = self.client.fetch_sector_minute_kline(code)
            except Exception as err:  # noqa: BLE001
                logger.warning(f"拉取板块 {code} ({name}) 分时数据异常: {err}")
                return []

            # 过滤属于当前目标日期的分钟线
            day_klines = [k for k in klines if k.trade_date == cur_date]
            if not day_klines:
                return []

            # 按时间升序排序
            day_klines.sort(key=lambda x: x.snapshot_time)

            sector_snaps: list[SectorSnapshot] = []
            prev_main = 0.0

            for i, k in enumerate(day_klines):
                # 增量 Δ 计算: 第一根线等于自身累计值，后续等于前点差值
                delta = k.main_net_inflow if i == 0 else (k.main_net_inflow - prev_main)
                prev_main = k.main_net_inflow

                snap = SectorSnapshot(
                    trade_date=k.trade_date,
                    snapshot_time=k.snapshot_time,
                    sector_code=code,
                    sector_name=name,
                    change_pct=0.0,
                    main_net_inflow=k.main_net_inflow,
                    minute_net_inflow=round(delta, 2),
                    super_large_inflow=k.super_large_inflow,
                    large_inflow=k.large_inflow,
                    middle_inflow=k.middle_inflow,
                    small_inflow=k.small_inflow,
                    main_inflow_ratio=0.0,
                )
                sector_snaps.append(snap)

            return sector_snaps

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_code = {
                executor.submit(_fetch_and_build, code, name): code
                for code, name in sector_targets
            }
            for future in as_completed(future_to_code):
                res = future.result()
                all_snapshots.extend(res)

        # 3. 批量写入数据库 (强依赖唯一键防重)
        inserted = self.storage.save_snapshots(all_snapshots)
        logger.info(
            f"自愈补数完成！总生成 {len(all_snapshots)} 条快照，实际新增写入 {inserted} 条"
        )
        return inserted

    def load_latest_inflow_cache(self, target_date: date) -> dict[str, float]:
        """从数据库加载最近一个快照时刻各板块的累计主力净流入，用于初始化内存增量缓存"""
        cache: dict[str, float] = {}
        latest_time = self.storage.get_latest_snapshot_time(target_date)
        if latest_time is None:
            return cache

        query = """
            SELECT sector_code, main_net_inflow
            FROM sector_fund_flow_snapshots
            WHERE trade_date = %s AND snapshot_time = %s;
        """
        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (target_date, latest_time))
            for code, inflow in cur.fetchall():
                cache[code] = float(inflow)

        logger.info(
            f"已恢复内存增量缓存: 交易日 {target_date} 刻度 {latest_time}，加载 {len(cache)} 个板块状态"
        )
        return cache
