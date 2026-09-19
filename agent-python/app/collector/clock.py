import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

logger = logging.getLogger("trading.collector.clock")

SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")

# A 股核心交易时段定义
MORNING_START = time(9, 30, 0)
MORNING_END = time(11, 30, 0)
AFTERNOON_START = time(13, 0, 0)
AFTERNOON_END = time(15, 0, 0)


class TradingClock:
    """A 股交易时钟守卫 (负责交易日、盘中时段判定与整分钟对齐)"""

    def __init__(self, tz: ZoneInfo = SHANGHAI_TZ):
        self.tz = tz

    def now(self) -> datetime:
        """获取上海时区的当前时间"""
        return datetime.now(self.tz)

    def is_trading_day(self, target_date: date | datetime | None = None) -> bool:
        """判断是否为交易日 (常规工作日，周一至周五)

        :param target_date: 目标日期或时刻，缺省为当前时刻
        """
        if target_date is None:
            d = self.now().date()
        elif isinstance(target_date, datetime):
            d = target_date.date()
        else:
            d = target_date

        # weekday(): 0=周一, 4=周五, 5=周六, 6=周日
        return d.weekday() < 5

    def is_morning_session(self, dt: datetime | None = None) -> bool:
        """判断当前是否处于上午交易时段 (09:30:00 ~ 11:30:00)"""
        current_dt = dt or self.now()
        if not self.is_trading_day(current_dt):
            return False
        t = current_dt.time()
        return MORNING_START <= t <= MORNING_END

    def is_afternoon_session(self, dt: datetime | None = None) -> bool:
        """判断当前是否处于下午交易时段 (13:00:00 ~ 15:00:00)"""
        current_dt = dt or self.now()
        if not self.is_trading_day(current_dt):
            return False
        t = current_dt.time()
        return AFTERNOON_START <= t <= AFTERNOON_END

    def is_midday_break(self, dt: datetime | None = None) -> bool:
        """判断当前是否处于中午休盘时段 (11:30:01 ~ 12:59:59)"""
        current_dt = dt or self.now()
        if not self.is_trading_day(current_dt):
            return False
        t = current_dt.time()
        return MORNING_END < t < AFTERNOON_START

    def is_trading_time(self, dt: datetime | None = None) -> bool:
        """判断当前是否处于盘中交易时刻 (上午或下午时段)"""
        return self.is_morning_session(dt) or self.is_afternoon_session(dt)

    def is_market_closed_for_day(self, dt: datetime | None = None) -> bool:
        """判断当日盘面是否已彻底收盘 (15:00:00 之后或非交易日)"""
        current_dt = dt or self.now()
        if not self.is_trading_day(current_dt):
            return True
        return current_dt.time() > AFTERNOON_END

    @staticmethod
    def seconds_until_next_minute(dt: datetime | None = None) -> float:
        """计算距离下一次整分钟 (:00 秒) 的微调休眠秒数

        例如 09:31:25.400 -> 距离 09:32:00 还剩 34.6 秒
        """
        current_dt = dt or datetime.now(SHANGHAI_TZ)
        sec = current_dt.second
        micro = current_dt.microsecond
        remain = 60.0 - (sec + micro / 1_000_000.0)
        # 若刚好位于 0 秒且微秒极小，避免返回 60 秒，返回微小正数
        return remain if remain > 0.05 else 60.0

    @staticmethod
    def get_all_trading_minutes() -> list[time]:
        """获取 A 股全天标准 240 根分钟线时间刻度列表

        上午 120 根: 09:31 ~ 11:30 (或按东财刻度从 09:30 开始)
        下午 120 根: 13:01 ~ 15:00
        """
        minutes: list[time] = []
        # 上午 09:31 ~ 11:30
        curr = datetime(2000, 1, 1, 9, 31, tzinfo=SHANGHAI_TZ)
        end_am = datetime(2000, 1, 1, 11, 30, tzinfo=SHANGHAI_TZ)
        while curr <= end_am:
            minutes.append(curr.time())
            curr += timedelta(minutes=1)

        # 下午 13:01 ~ 15:00
        curr = datetime(2000, 1, 1, 13, 1, tzinfo=SHANGHAI_TZ)
        end_pm = datetime(2000, 1, 1, 15, 0, tzinfo=SHANGHAI_TZ)
        while curr <= end_pm:
            minutes.append(curr.time())
            curr += timedelta(minutes=1)


        return minutes

    def get_expected_minutes_up_to(self, dt: datetime | None = None) -> list[time]:
        """获取截至当前时刻，理论上应具备的历史交易分钟列表 (用于对比补数)"""
        current_dt = dt or self.now()
        if not self.is_trading_day(current_dt):
            return []

        all_mins = self.get_all_trading_minutes()
        current_time = current_dt.time()

        # 过滤出早于或等于当前时间的所有分钟切片
        return [m for m in all_mins if m <= current_time]
