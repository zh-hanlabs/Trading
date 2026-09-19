from datetime import date, time

import pytest

from app.collector.models import SectorSnapshot
from app.collector.storage import SnapshotStorage, get_db_connection


@pytest.fixture
def cleanup_test_data():
    """测试前后清理测试测试数据"""
    test_date = date(2099, 1, 1)
    yield test_date
    with get_db_connection() as conn, conn.cursor() as cur:
        cur.execute(
            "DELETE FROM sector_fund_flow_snapshots WHERE trade_date = %s;",
            (test_date,),
        )
        conn.commit()


def test_batch_save_and_idempotence(cleanup_test_data):
    """测试批量快照写入及 ON CONFLICT 幂等防重"""
    test_date = cleanup_test_data
    test_time = time(10, 0, 0)

    storage = SnapshotStorage()

    s1 = SectorSnapshot(
        trade_date=test_date,
        snapshot_time=test_time,
        sector_code="BK_TEST_01",
        sector_name="测试板块一",
        change_pct=1.23,
        main_net_inflow=5000000.0,
        minute_net_inflow=200000.0,
        super_large_inflow=3000000.0,
        large_inflow=2000000.0,
        middle_inflow=-1000000.0,
        small_inflow=-4000000.0,
        main_inflow_ratio=2.5,
        lead_stock_code="600001",
        lead_stock_name="测试龙头一",
        lead_stock_change_pct=3.45,
    )

    s2 = SectorSnapshot(
        trade_date=test_date,
        snapshot_time=test_time,
        sector_code="BK_TEST_02",
        sector_name="测试板块二",
        change_pct=-0.56,
        main_net_inflow=-2000000.0,
        minute_net_inflow=-50000.0,
        super_large_inflow=-1000000.0,
        large_inflow=-1000000.0,
        middle_inflow=500000.0,
        small_inflow=1500000.0,
        main_inflow_ratio=-1.2,
        lead_stock_code=None,
        lead_stock_name=None,
        lead_stock_change_pct=None,
    )

    # 首次写入：应成功新增 2 条
    inserted = storage.save_snapshots([s1, s2])
    assert inserted == 2

    count = storage.get_snapshot_count(test_date, test_time)
    assert count == 2

    # 重复写入相同数据：唯一键约束生效，新增数为 0，且绝不报错
    inserted_again = storage.save_snapshots([s1, s2])
    assert inserted_again == 0

    # 验证最新时刻自检能力
    latest_time = storage.get_latest_snapshot_time(test_date)
    assert latest_time == test_time
