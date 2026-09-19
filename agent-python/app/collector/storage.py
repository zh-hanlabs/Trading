import logging
from collections.abc import Generator
from contextlib import contextmanager
from datetime import date, time
from typing import Any

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import execute_values

from app.collector.models import SectorSnapshot
from app.core.config import settings

logger = logging.getLogger("trading.collector.storage")


@contextmanager
def get_db_connection() -> Generator[PgConnection, None, None]:
    """获取数据库连接上下文管理器"""
    conn = psycopg2.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        dbname=settings.POSTGRES_DB,
    )
    try:
        yield conn
    finally:
        conn.close()


class SnapshotStorage:
    """资金流快照时序存储层 (负责批量高性能落库与防重校验)"""

    INSERT_SQL = """
        INSERT INTO sector_fund_flow_snapshots (
            trade_date,
            snapshot_time,
            sector_code,
            sector_name,
            change_pct,
            main_net_inflow,
            minute_net_inflow,
            super_large_inflow,
            large_inflow,
            middle_inflow,
            small_inflow,
            main_inflow_ratio,
            lead_stock_code,
            lead_stock_name,
            lead_stock_change_pct
        ) VALUES %s
        ON CONFLICT (trade_date, snapshot_time, sector_code)
        DO NOTHING;
    """

    @staticmethod
    def _snapshot_to_tuple(s: SectorSnapshot) -> tuple[Any, ...]:
        """将数据模型转换为 SQL 参数元组"""
        return (
            s.trade_date,
            s.snapshot_time,
            s.sector_code,
            s.sector_name,
            s.change_pct,
            s.main_net_inflow,
            s.minute_net_inflow,
            s.super_large_inflow,
            s.large_inflow,
            s.middle_inflow,
            s.small_inflow,
            s.main_inflow_ratio,
            s.lead_stock_code,
            s.lead_stock_name,
            s.lead_stock_change_pct,
        )

    def save_snapshots(
        self, snapshots: list[SectorSnapshot], conn: PgConnection | None = None
    ) -> int:
        """批量保存资金流快照记录 (具备联合唯一索引幂等防重)

        :param snapshots: 快照列表
        :param conn: 可选外部事务连接
        :return: 实际成功插入的新记录数
        """
        if not snapshots:
            return 0

        tuples = [self._snapshot_to_tuple(s) for s in snapshots]

        def _do_insert(active_conn: PgConnection) -> int:
            with active_conn.cursor() as cur:
                execute_values(
                    cur,
                    self.INSERT_SQL,
                    tuples,
                    page_size=len(tuples),
                )
                inserted = cur.rowcount
            active_conn.commit()
            logger.info(
                f"批量写入资金流快照: 提交 {len(snapshots)} 条，实际新增落库 {inserted} 条"
            )
            return inserted

        if conn is not None:
            return _do_insert(conn)

        with get_db_connection() as new_conn:
            return _do_insert(new_conn)

    def get_latest_snapshot_time(
        self, target_date: date, conn: PgConnection | None = None
    ) -> time | None:
        """获取指定交易日数据库中已记录的最新快照时刻 (用于断点自愈开机自检)

        :param target_date: 目标交易日
        :param conn: 可选外部连接
        :return: 最新快照时刻，若库中尚无数据则返回 None
        """
        query = """
            SELECT MAX(snapshot_time)
            FROM sector_fund_flow_snapshots
            WHERE trade_date = %s;
        """

        def _do_query(active_conn: PgConnection) -> time | None:
            with active_conn.cursor() as cur:
                cur.execute(query, (target_date,))
                row = cur.fetchone()
                return row[0] if row and row[0] is not None else None

        if conn is not None:
            return _do_query(conn)

        with get_db_connection() as new_conn:
            return _do_query(new_conn)

    def get_snapshot_count(
        self, target_date: date, snapshot_time: time | None = None
    ) -> int:
        """查询指定交易日或指定切片的记录总数"""
        query = """
            SELECT COUNT(*)
            FROM sector_fund_flow_snapshots
            WHERE trade_date = %s
        """
        params: list[Any] = [target_date]
        if snapshot_time is not None:
            query += " AND snapshot_time = %s"
            params.append(snapshot_time)

        with get_db_connection() as conn, conn.cursor() as cur:
            cur.execute(query, tuple(params))
            row = cur.fetchone()
            return row[0] if row else 0
