import logging
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Query

from app.collector.eastmoney import EastMoneyClient
from app.collector.models import SectorSnapshot
from app.collector.storage import SnapshotStorage, get_db_connection

logger = logging.getLogger("trading.api.collector")
router = APIRouter(prefix="/api/agent/collector", tags=["资金流数据采集与管理"])


@router.post("/backfill", summary="历史交易日真实数据回补入库")
def backfill_data(
    target_date: str = Query(
        default="2026-09-18",
        description="回补的目标交易日 (YYYY-MM-DD)",
        examples=["2026-09-18"],
    ),
    top_klines_count: int = Query(
        default=10,
        description="拉取分时线的核心主线板块数量 (流入TopN + 流出TopN)",
    ),
):
    """从东方财富公网接口拉取真实全市场行业板块行情快照与核心板块日内分时线，存入 PostgreSQL 数据库"""
    try:
        t_date = date.fromisoformat(target_date)
    except ValueError:
        return {"code": 400, "message": f"日期格式非法: {target_date}，格式应为 YYYY-MM-DD"}

    client = EastMoneyClient()
    storage = SnapshotStorage()
    sh_tz = ZoneInfo("Asia/Shanghai")

    logger.info(f"收到数据回补请求: 目标日期 {t_date}")

    # 1. 抓取 14:59:00 快照 (全市场行业板块)
    dt_1459 = datetime.combine(t_date, time(14, 59, 0), tzinfo=sh_tz)
    snaps_1459 = client.fetch_sector_snapshots(max_pages=2, target_dt=dt_1459)
    cnt_1459 = storage.save_snapshots(snaps_1459)

    # 2. 抓取 15:00:00 收盘快照 (全市场行业板块)
    dt_1500 = datetime.combine(t_date, time(15, 0, 0), tzinfo=sh_tz)
    snaps_1500 = client.fetch_sector_snapshots(max_pages=2, target_dt=dt_1500)
    cnt_1500 = storage.save_snapshots(snaps_1500)

    # 3. 抓取重点板块分时走势线 (用于支撑走势曲线图)
    top_inflow = sorted(snaps_1500, key=lambda s: s.main_net_inflow, reverse=True)[
        :top_klines_count
    ]
    top_outflow = sorted(snaps_1500, key=lambda s: s.main_net_inflow)[:5]
    key_sectors = {s.sector_code: s for s in (top_inflow + top_outflow)}.values()

    timeline_snaps: list[SectorSnapshot] = []
    for s in key_sectors:
        try:
            klines = client.fetch_sector_minute_kline(s.sector_code)
            day_klines = [k for k in klines if k.trade_date == t_date]
            day_klines.sort(key=lambda x: x.snapshot_time)
            prev_main = 0.0
            for i, k in enumerate(day_klines):
                delta = k.main_net_inflow if i == 0 else (k.main_net_inflow - prev_main)
                prev_main = k.main_net_inflow
                timeline_snaps.append(
                    SectorSnapshot(
                        trade_date=k.trade_date,
                        snapshot_time=k.snapshot_time,
                        sector_code=s.sector_code,
                        sector_name=s.sector_name,
                        change_pct=s.change_pct,
                        main_net_inflow=k.main_net_inflow,
                        minute_net_inflow=round(delta, 2),
                        super_large_inflow=k.super_large_inflow,
                        large_inflow=k.large_inflow,
                        middle_inflow=k.middle_inflow,
                        small_inflow=k.small_inflow,
                        main_inflow_ratio=s.main_inflow_ratio,
                        lead_stock_code=s.lead_stock_code,
                        lead_stock_name=s.lead_stock_name,
                        lead_stock_change_pct=s.lead_stock_change_pct,
                    )
                )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"拉取 {s.sector_name} 分时线异常: {e}")

    cnt_timeline = storage.save_snapshots(timeline_snaps)
    total_count = storage.get_snapshot_count(t_date)

    return {
        "code": 200,
        "message": "历史真实数据回补落库成功！",
        "data": {
            "trade_date": str(t_date),
            "snapshots_1459_saved": cnt_1459,
            "snapshots_1500_saved": cnt_1500,
            "timeline_points_saved": cnt_timeline,
            "total_records_for_date": total_count,
        },
    }


@router.get("/status", summary="查询数据库快照统计与最新时间")
def get_collector_status():
    """查询 PostgreSQL 中目前存储的快照总数、最新交易日和最新时间切片"""
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT count(*), max(trade_date), max(snapshot_time) FROM sector_fund_flow_snapshots;"
        )
        count, max_date, max_time = cur.fetchone()

    return {
        "code": 200,
        "data": {
            "total_records": count,
            "latest_trade_date": str(max_date) if max_date else None,
            "latest_snapshot_time": str(max_time) if max_time else None,
        },
    }
