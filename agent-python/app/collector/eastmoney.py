import logging
import socket
import time
from datetime import date, datetime
from typing import Any, ClassVar, Self
from zoneinfo import ZoneInfo

import httpx

from app.collector.models import MinuteKlinePoint, SectorSnapshot

# 针对本地 VPN / 代理 TUN 模式：
# 过滤掉 IPv6 Fake-IP，强制仅使用 IPv4 解析，彻底避免服务端连接重置断开
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_only_getaddrinfo(host: Any, port: Any, family: int = 0, socktype: int = 0, proto: int = 0, flags: int = 0) -> list[Any]:
    res = _orig_getaddrinfo(host, port, family, socktype, proto, flags)
    ipv4_res = [r for r in res if r[0] == socket.AF_INET]
    return ipv4_res if ipv4_res else res


socket.getaddrinfo = _ipv4_only_getaddrinfo

logger = logging.getLogger("trading.collector.eastmoney")


def safe_float(val: Any, default: float = 0.0) -> float:
    """安全转换为浮点数，过滤 '-' 或空值"""
    if val is None or val == "-" or val == "":
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def safe_str(val: Any) -> str | None:
    """安全转换为字符串，过滤 '-' 或空值"""
    if val is None or val == "-" or val == "":
        return None
    return str(val).strip()


class EastMoneyClient:
    """东方财富公网行情与资金流接口通信客户端"""

    # 使用东财高可用稳定数据中心节点 push2delay，彻底规避 push2 节点的 WAF 频控断连
    BASE_URL_CLIST = "https://push2delay.eastmoney.com/api/qt/clist/get"
    BASE_URL_KLINE = "https://push2delay.eastmoney.com/api/qt/stock/fflow/kline/get"
    UT_TOKEN = "b2884a393a59ad64002292a3e90d46a5"

    DEFAULT_HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://data.eastmoney.com/",
        "Accept": "*/*",
        "Connection": "keep-alive",
    }

    def __init__(self, timeout: float = 10.0, max_retries: int = 3, retry_delay: float = 0.5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = httpx.Client(
            headers=self.DEFAULT_HEADERS,
            timeout=self.timeout,
            follow_redirects=True,
        )

    def close(self) -> None:
        """关闭 HTTP 客户端会话"""
        self.client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _get_with_retry(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        """具备指数退避重试的 GET 请求封装"""
        last_err: Exception | None = None
        delay = self.retry_delay

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                if not isinstance(data, dict):
                    raise TypeError(f"响应非合法 JSON 字典: {resp.text[:100]}")
                return data
            except (httpx.RequestError, httpx.HTTPStatusError, TypeError, ValueError) as e:
                last_err = e
                logger.warning(
                    f"东财请求异常 [尝试 {attempt}/{self.max_retries}]: {e}，将在 {delay:.1f}s 后重试"
                )
                time.sleep(delay)
                delay *= 2

        raise RuntimeError(f"东财接口请求失败，超过最大重试次数: {last_err}") from last_err

    def fetch_sector_snapshots(
        self,
        fs: str = "m:90+t:2",
        page_size: int = 100,
        max_pages: int = 1,
        target_dt: datetime | None = None,
    ) -> list[SectorSnapshot]:
        """抓取全市场行业板块资金流快照

        :param fs: 筛选参数，默认 m:90+t:2 (行业板块)
        :param page_size: 单页条数，默认 100
        :param max_pages: 最大抓取页数，默认 1 (涵盖全市场前 100 个核心行业板块)
        :param target_dt: 指定快照时间，缺省使用当前时刻
        :return: 板块快照数据模型列表
        """
        sh_tz = ZoneInfo("Asia/Shanghai")
        now = target_dt or datetime.now(sh_tz)
        current_date: date = now.date()
        current_time = now.time().replace(microsecond=0)


        snapshots: list[SectorSnapshot] = []

        for page in range(1, max_pages + 1):
            params = {
                "pn": str(page),
                "pz": str(page_size),
                "po": "1",
                "np": "1",
                "ut": self.UT_TOKEN,
                "fltt": "2",
                "invt": "2",
                "fid": "f62",
                "fs": fs,
                "fields": "f12,f14,f2,f3,f62,f184,f66,f72,f78,f84,f204,f205,f206",
            }

            raw = self._get_with_retry(self.BASE_URL_CLIST, params)
            diff = raw.get("data", {}).get("diff", [])
            if not diff:
                break

            for item in diff:
                code = safe_str(item.get("f12"))
                name = safe_str(item.get("f14"))
                if not code or not name:
                    continue

                snapshot = SectorSnapshot(
                    trade_date=current_date,
                    snapshot_time=current_time,
                    sector_code=code,
                    sector_name=name,
                    change_pct=safe_float(item.get("f3")),
                    main_net_inflow=safe_float(item.get("f62")),
                    minute_net_inflow=0.0,
                    super_large_inflow=safe_float(item.get("f66")),
                    large_inflow=safe_float(item.get("f72")),
                    middle_inflow=safe_float(item.get("f78")),
                    small_inflow=safe_float(item.get("f84")),
                    main_inflow_ratio=safe_float(item.get("f184")),
                    lead_stock_name=safe_str(item.get("f204")),
                    lead_stock_code=safe_str(item.get("f205")),
                    lead_stock_change_pct=safe_float(item.get("f206"))
                    if item.get("f206") not in (None, "-", "")
                    else None,
                )
                snapshots.append(snapshot)

        logger.info(f"成功获取 {len(snapshots)} 条板块资金流快照数据 ({current_date} {current_time})")
        return snapshots

    def fetch_sector_minute_kline(self, sector_code: str) -> list[MinuteKlinePoint]:
        """抓取单板块日内分钟级资金流历史分时 (用于迟到自愈补数)

        :param sector_code: 板块代码 (如 'BK1036')
        :return: 历史分钟分时线列表 (按时间升序)
        """
        secid = f"90.{sector_code}" if not sector_code.startswith("90.") else sector_code
        params = {
            "secid": secid,
            "klt": "1",
            "ut": self.UT_TOKEN,
            "fields1": "f1,f2,f3,f7",
            "fields2": "f51,f52,f53,f54,f55,f56,f57",
        }

        raw = self._get_with_retry(self.BASE_URL_KLINE, params)
        raw_klines = raw.get("data", {}).get("klines", [])
        if not raw_klines:
            logger.debug(f"板块 {sector_code} 暂无历史分钟分时数据")
            return []

        points: list[MinuteKlinePoint] = []
        for line in raw_klines:
            parts = line.split(",")
            if len(parts) < 6:
                continue

            try:
                dt = datetime.strptime(parts[0], "%Y-%m-%d %H:%M").replace(
                    tzinfo=ZoneInfo("Asia/Shanghai")
                )
            except ValueError:

                continue

            point = MinuteKlinePoint(
                dt=dt,
                trade_date=dt.date(),
                snapshot_time=dt.time().replace(microsecond=0),
                main_net_inflow=safe_float(parts[1]),
                small_inflow=safe_float(parts[2]),
                middle_inflow=safe_float(parts[3]),
                large_inflow=safe_float(parts[4]),
                super_large_inflow=safe_float(parts[5]),
            )
            points.append(point)

        return points
