from datetime import datetime, time

from app.collector.clock import SHANGHAI_TZ, TradingClock


def test_trading_day_detection():
    """测试交易日与周末判定"""
    clock = TradingClock()
    # 2026-09-18 为周五 (交易日)
    friday = datetime(2026, 9, 18, 10, 0, tzinfo=SHANGHAI_TZ)
    # 2026-09-19 为周六 (休市)
    saturday = datetime(2026, 9, 19, 10, 0, tzinfo=SHANGHAI_TZ)
    # 2026-09-20 为周日 (休市)
    sunday = datetime(2026, 9, 20, 10, 0, tzinfo=SHANGHAI_TZ)
    # 2026-09-21 为周一 (交易日)
    monday = datetime(2026, 9, 21, 10, 0, tzinfo=SHANGHAI_TZ)

    assert clock.is_trading_day(friday) is True
    assert clock.is_trading_day(saturday) is False
    assert clock.is_trading_day(sunday) is False
    assert clock.is_trading_day(monday) is True


def test_trading_sessions():
    """测试盘中时段、休盘与收盘判定"""
    clock = TradingClock()

    # 交易日: 周五 2026-09-18
    dt_before_open = datetime(2026, 9, 18, 9, 29, 59, tzinfo=SHANGHAI_TZ)
    dt_am_open = datetime(2026, 9, 18, 9, 30, 0, tzinfo=SHANGHAI_TZ)
    dt_am_mid = datetime(2026, 9, 18, 10, 15, 0, tzinfo=SHANGHAI_TZ)
    dt_am_close = datetime(2026, 9, 18, 11, 30, 0, tzinfo=SHANGHAI_TZ)
    dt_midday = datetime(2026, 9, 18, 12, 0, 0, tzinfo=SHANGHAI_TZ)
    dt_pm_open = datetime(2026, 9, 18, 13, 0, 0, tzinfo=SHANGHAI_TZ)
    dt_pm_mid = datetime(2026, 9, 18, 14, 0, 0, tzinfo=SHANGHAI_TZ)
    dt_pm_close = datetime(2026, 9, 18, 15, 0, 0, tzinfo=SHANGHAI_TZ)
    dt_after_close = datetime(2026, 9, 18, 15, 0, 1, tzinfo=SHANGHAI_TZ)

    # 盘前
    assert clock.is_morning_session(dt_before_open) is False
    assert clock.is_trading_time(dt_before_open) is False

    # 上午时段
    assert clock.is_morning_session(dt_am_open) is True
    assert clock.is_morning_session(dt_am_mid) is True
    assert clock.is_morning_session(dt_am_close) is True
    assert clock.is_trading_time(dt_am_mid) is True
    assert clock.is_midday_break(dt_am_mid) is False

    # 中午休盘
    assert clock.is_trading_time(dt_midday) is False
    assert clock.is_midday_break(dt_midday) is True

    # 下午时段
    assert clock.is_afternoon_session(dt_pm_open) is True
    assert clock.is_afternoon_session(dt_pm_mid) is True
    assert clock.is_afternoon_session(dt_pm_close) is True
    assert clock.is_trading_time(dt_pm_mid) is True
    assert clock.is_market_closed_for_day(dt_pm_mid) is False

    # 盘后
    assert clock.is_trading_time(dt_after_close) is False
    assert clock.is_market_closed_for_day(dt_after_close) is True


def test_seconds_until_next_minute():
    """测试距离下一次整分钟的对齐休眠时间计算"""
    clock = TradingClock()

    # 10:00:30.000 -> 距离下一分钟 30.0 秒
    t1 = datetime(2026, 9, 18, 10, 0, 30, 0, tzinfo=SHANGHAI_TZ)
    remain1 = clock.seconds_until_next_minute(t1)
    assert abs(remain1 - 30.0) < 0.001

    # 10:00:59.500 -> 距离下一分钟 0.5 秒
    t2 = datetime(2026, 9, 18, 10, 0, 59, 500000, tzinfo=SHANGHAI_TZ)
    remain2 = clock.seconds_until_next_minute(t2)
    assert abs(remain2 - 0.5) < 0.001


def test_trading_minutes_list():
    """测试全天 240 根分钟线及指定时刻预期分钟数"""
    clock = TradingClock()

    all_mins = clock.get_all_trading_minutes()
    assert len(all_mins) == 240
    assert all_mins[0] == time(9, 31)
    assert all_mins[119] == time(11, 30)
    assert all_mins[120] == time(13, 1)
    assert all_mins[239] == time(15, 0)

    # 12:00:00 (中午开机) 应该预期上午已产生 120 根分钟线
    midday = datetime(2026, 9, 18, 12, 0, 0, tzinfo=SHANGHAI_TZ)
    expected_midday = clock.get_expected_minutes_up_to(midday)
    assert len(expected_midday) == 120
    assert expected_midday[-1] == time(11, 30)

    # 09:35:00 预期已产生 5 根分钟线
    am_5 = datetime(2026, 9, 18, 9, 35, 0, tzinfo=SHANGHAI_TZ)
    expected_5 = clock.get_expected_minutes_up_to(am_5)
    assert len(expected_5) == 5
    assert expected_5[-1] == time(9, 35)

    # 15:30:00 预期产生全天 240 根分钟线
    closed = datetime(2026, 9, 18, 15, 30, 0, tzinfo=SHANGHAI_TZ)
    expected_all = clock.get_expected_minutes_up_to(closed)
    assert len(expected_all) == 240
