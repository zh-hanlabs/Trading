from datetime import date, time
from unittest.mock import MagicMock

import pytest

from app.collector.eastmoney import EastMoneyClient, safe_float, safe_str
from app.collector.models import MinuteKlinePoint, SectorSnapshot


def test_safe_converters():
    """测试安全转换函数"""
    assert safe_float(None) == 0.0
    assert safe_float("-") == 0.0
    assert safe_float("") == 0.0
    assert safe_float("123.45") == 123.45
    assert safe_float(-999.5) == -999.5

    assert safe_str(None) is None
    assert safe_str("-") is None
    assert safe_str("") is None
    assert safe_str("  半导体  ") == "半导体"


def test_fetch_sector_snapshots_mock():
    """测试东财板块资金流实时排行榜解析逻辑 (单元测试，隔离公网)"""
    mock_raw_response = {
        "data": {
            "total": 1,
            "diff": [
                {
                    "f12": "BK1036",
                    "f14": "半导体",
                    "f2": 2869.78,
                    "f3": 4.35,
                    "f62": 18220373248.0,
                    "f66": 13611058432.0,
                    "f72": 4609314816.0,
                    "f78": -10769022976.0,
                    "f84": -7377339136.0,
                    "f184": 5.46,
                    "f204": "中芯国际",
                    "f205": "688981",
                    "f206": 5.12,
                }
            ],
        }
    }

    client = EastMoneyClient()
    client._get_with_retry = MagicMock(return_value=mock_raw_response)

    snapshots = client.fetch_sector_snapshots(page_size=10, max_pages=1)
    assert len(snapshots) == 1
    s = snapshots[0]
    assert isinstance(s, SectorSnapshot)
    assert s.sector_code == "BK1036"
    assert s.sector_name == "半导体"
    assert s.change_pct == 4.35
    assert s.main_net_inflow == 18220373248.0
    assert s.super_large_inflow == 13611058432.0
    assert s.lead_stock_name == "中芯国际"
    assert s.lead_stock_code == "688981"
    assert s.lead_stock_change_pct == 5.12


def test_fetch_sector_minute_kline_mock():
    """测试单板块日内分钟分时资金线解析逻辑 (单元测试，隔离公网)"""
    mock_raw_kline = {
        "data": {
            "klines": [
                "2026-09-18 09:31,183158202.0,-75462693.0,-10705720.0,39565567.0,143592634.0",
                "2026-09-18 09:32,182699640.0,-75365656.0,-10680600.0,39852903.0,142846736.0",
            ]
        }
    }

    client = EastMoneyClient()
    client._get_with_retry = MagicMock(return_value=mock_raw_kline)

    klines = client.fetch_sector_minute_kline("BK1036")
    assert len(klines) == 2
    k1 = klines[0]
    assert isinstance(k1, MinuteKlinePoint)
    assert k1.trade_date == date(2026, 9, 18)
    assert k1.snapshot_time == time(9, 31)
    assert k1.main_net_inflow == 183158202.0
    assert k1.small_inflow == -75462693.0
    assert k1.middle_inflow == -10705720.0
    assert k1.large_inflow == 39565567.0
    assert k1.super_large_inflow == 143592634.0


def test_live_eastmoney_network_optional():
    """公网连通性集成测试 (若公网风控临时断开则友好跳过)"""
    try:
        with EastMoneyClient(timeout=3.0, max_retries=1) as client:
            snapshots = client.fetch_sector_snapshots(page_size=5, max_pages=1)
            if snapshots:
                assert isinstance(snapshots[0], SectorSnapshot)
    except RuntimeError as e:
        pytest.skip(f"东财公网接口临时限速或网络不可达，跳过公网实时请求: {e}")
