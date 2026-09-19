from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field


class SectorSnapshot(BaseModel):
    """板块资金流快照数据模型 (对应 PostgreSQL 表 sector_fund_flow_snapshots)"""

    model_config = ConfigDict(from_attributes=True)

    trade_date: date = Field(..., description="交易日期 (YYYY-MM-DD)")
    snapshot_time: time = Field(..., description="快照时刻 (HH:MM:SS)")
    sector_code: str = Field(..., description="东方财富板块代码 (如 BK1036)")
    sector_name: str = Field(..., description="板块名称 (如 半导体)")
    change_pct: float = Field(..., description="板块实时涨跌幅 (%)")
    main_net_inflow: float = Field(..., description="累计主力净流入额 (元，超大单+大单)")
    minute_net_inflow: float = Field(default=0.0, description="本分钟瞬时净流入额 (Δ，元)")

    super_large_inflow: float = Field(default=0.0, description="累计超大单净流入 (元)")
    large_inflow: float = Field(default=0.0, description="累计大单净流入 (元)")
    middle_inflow: float = Field(default=0.0, description="累计中单净流入 (元)")
    small_inflow: float = Field(default=0.0, description="累计小单净流入 (元)")
    main_inflow_ratio: float = Field(default=0.0, description="主力净流入占比 (%)")

    lead_stock_code: str | None = Field(default=None, description="领涨股代码")
    lead_stock_name: str | None = Field(default=None, description="领涨股名称")
    lead_stock_change_pct: float | None = Field(default=None, description="领涨股涨幅 (%)")


class MinuteKlinePoint(BaseModel):
    """单板块日内 1 分钟分时资金流历史切片 (用于迟到自愈补数)"""

    model_config = ConfigDict(from_attributes=True)

    dt: datetime = Field(..., description="分钟线时间戳 (YYYY-MM-DD HH:MM)")
    trade_date: date = Field(..., description="交易日期")
    snapshot_time: time = Field(..., description="快照时刻")
    main_net_inflow: float = Field(..., description="累计主力净流入 (元)")
    small_inflow: float = Field(default=0.0, description="累计小单净流入 (元)")
    middle_inflow: float = Field(default=0.0, description="累计中单净流入 (元)")
    large_inflow: float = Field(default=0.0, description="累计大单净流入 (元)")
    super_large_inflow: float = Field(default=0.0, description="累计超大单净流入 (元)")
