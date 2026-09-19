from datetime import date, datetime, time
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

from app.collector.backfill import BackfillService
from app.collector.clock import SHANGHAI_TZ
from app.collector.engine import CollectorEngine
from app.collector.models import MinuteKlinePoint, SectorSnapshot


def test_engine_delta_calculation():
    """测试 CollectorEngine 分钟瞬时增量 Δ 计算逻辑"""
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_clock = MagicMock()

    engine = CollectorEngine(
        client=mock_client,
        storage=mock_storage,
        clock=mock_clock,
    )

    test_date = date(2026, 9, 18)

    # 第 1 步: 09:31 首根分钟线
    dt_1 = datetime(2026, 9, 18, 9, 31, 0, tzinfo=SHANGHAI_TZ)
    snap_1 = SectorSnapshot(
        trade_date=test_date,
        snapshot_time=dt_1.time(),
        sector_code="BK1036",
        sector_name="半导体",
        change_pct=1.0,
        main_net_inflow=1000.0,
        minute_net_inflow=0.0,
    )
    mock_client.fetch_sector_snapshots.return_value = [snap_1]

    res_1 = engine.run_once(target_dt=dt_1)
    assert len(res_1) == 1
    # 首根分钟线 Δ 应当等于累计流入值
    assert res_1[0].minute_net_inflow == 1000.0
    assert engine.prev_inflows["BK1036"] == 1000.0

    # 第 2 步: 09:32 第二根分钟线 (主力继续买入)
    dt_2 = datetime(2026, 9, 18, 9, 32, 0, tzinfo=SHANGHAI_TZ)
    snap_2 = SectorSnapshot(
        trade_date=test_date,
        snapshot_time=dt_2.time(),
        sector_code="BK1036",
        sector_name="半导体",
        change_pct=1.5,
        main_net_inflow=1350.0,
        minute_net_inflow=0.0,
    )
    mock_client.fetch_sector_snapshots.return_value = [snap_2]

    res_2 = engine.run_once(target_dt=dt_2)
    # Δ = 1350 - 1000 = 350.0
    assert res_2[0].minute_net_inflow == 350.0
    assert engine.prev_inflows["BK1036"] == 1350.0

    # 第 3 步: 09:33 第三根分钟线 (主力资金净流出)
    dt_3 = datetime(2026, 9, 18, 9, 33, 0, tzinfo=SHANGHAI_TZ)
    snap_3 = SectorSnapshot(
        trade_date=test_date,
        snapshot_time=dt_3.time(),
        sector_code="BK1036",
        sector_name="半导体",
        change_pct=1.2,
        main_net_inflow=1200.0,
        minute_net_inflow=0.0,
    )
    mock_client.fetch_sector_snapshots.return_value = [snap_3]

    res_3 = engine.run_once(target_dt=dt_3)
    # Δ = 1200 - 1350 = -150.0
    assert res_3[0].minute_net_inflow == -150.0
    assert engine.prev_inflows["BK1036"] == 1200.0


def test_backfill_calculation_and_recovery():
    """测试 BackfillService 历史分钟线增量还原与落库"""
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_clock = MagicMock()

    # 模拟当前为 2026-09-18 12:00:00 (中午开机)
    now_midday = datetime(2026, 9, 18, 12, 0, 0, tzinfo=ZoneInfo("Asia/Shanghai"))
    mock_clock.now.return_value = now_midday
    mock_clock.is_trading_day.return_value = True
    mock_clock.get_expected_minutes_up_to.return_value = [time(9, 31), time(9, 32)]
    # 模拟数据库中尚无当天数据
    mock_storage.get_latest_snapshot_time.return_value = None
    mock_storage.save_snapshots.return_value = 2

    # 模拟东财返回的上午 2 根历史分钟线
    mock_client.fetch_sector_minute_kline.return_value = [
        MinuteKlinePoint(
            dt=datetime(2026, 9, 18, 9, 31, tzinfo=SHANGHAI_TZ),
            trade_date=date(2026, 9, 18),
            snapshot_time=time(9, 31),
            main_net_inflow=500.0,
            small_inflow=0.0,
            middle_inflow=0.0,
            large_inflow=200.0,
            super_large_inflow=300.0,
        ),
        MinuteKlinePoint(
            dt=datetime(2026, 9, 18, 9, 32, tzinfo=SHANGHAI_TZ),
            trade_date=date(2026, 9, 18),
            snapshot_time=time(9, 32),
            main_net_inflow=800.0,
            small_inflow=0.0,
            middle_inflow=0.0,
            large_inflow=300.0,
            super_large_inflow=500.0,
        ),
    ]

    service = BackfillService(
        client=mock_client,
        storage=mock_storage,
        clock=mock_clock,
    )

    inserted = service.check_and_backfill(
        target_date=date(2026, 9, 18),
        sector_targets=[("BK1036", "半导体")],
    )

    assert inserted == 2
    assert mock_storage.save_snapshots.called
    saved_snaps: list[SectorSnapshot] = mock_storage.save_snapshots.call_args[0][0]
    assert len(saved_snaps) == 2
    # 验证第一根线 Δ = 500.0
    assert saved_snaps[0].minute_net_inflow == 500.0
    # 验证第二根线 Δ = 800.0 - 500.0 = 300.0
    assert saved_snaps[1].minute_net_inflow == 300.0
