from datetime import date, time

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


def test_fetch_sector_snapshots():
    """测试东财板块资金流实时排行榜抓取"""
    with EastMoneyClient() as client:
        snapshots = client.fetch_sector_snapshots(page_size=10, max_pages=1)

    assert isinstance(snapshots, list)
    assert len(snapshots) > 0

    first = snapshots[0]
    assert isinstance(first, SectorSnapshot)
    assert isinstance(first.trade_date, date)
    assert isinstance(first.snapshot_time, time)
    assert first.sector_code.startswith("BK")
    assert len(first.sector_name) > 0
    assert isinstance(first.main_net_inflow, float)
    assert isinstance(first.change_pct, float)


def test_fetch_sector_minute_kline():
    """测试东财单板块日内分钟分时资金线抓取"""
    with EastMoneyClient() as client:
        # BK1036: 半导体板块
        klines = client.fetch_sector_minute_kline("BK1036")

    assert isinstance(klines, list)
    if klines:
        first = klines[0]
        assert isinstance(first, MinuteKlinePoint)
        assert isinstance(first.main_net_inflow, float)
        assert isinstance(first.trade_date, date)
        assert isinstance(first.snapshot_time, time)
