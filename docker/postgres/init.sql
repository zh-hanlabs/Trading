-- ==============================================================================
-- A股行业板块资金流分时快照表 (1分钟切片)
-- ==============================================================================

CREATE TABLE IF NOT EXISTS sector_fund_flow_snapshots (
    id BIGSERIAL PRIMARY KEY,
    
    -- 核心时间维度 (1分钟粒度切片)
    trade_date DATE NOT NULL,                         -- 交易日期 (YYYY-MM-DD)
    snapshot_time TIME(0) WITHOUT TIME ZONE NOT NULL,    -- 快照时刻 (HH:MM:SS，如 10:00:00)
    
    -- 板块标识
    sector_code VARCHAR(32) NOT NULL,                 -- 东方财富板块代码 (如 BK0420)
    sector_name VARCHAR(64) NOT NULL,                 -- 板块名称 (如 光伏设备)
    
    -- 行情指标
    change_pct NUMERIC(6, 2) NOT NULL,                -- 板块实时涨跌幅 (%)，如 +2.45
    
    -- 核心资金流指标 (单位: 元，正进负出)
    main_net_inflow NUMERIC(18, 2) NOT NULL,          -- 今日累计主力净流入 (东财 f62，超大单+大单累计)
    minute_net_inflow NUMERIC(18, 2) DEFAULT 0,       -- 【增量指标】本分钟瞬时净流入 (当前点 main_net_inflow - 上一点)
    
    -- 细分订单资金分布 (对应东财 f66, f72, f78, f84)
    super_large_inflow NUMERIC(18, 2) DEFAULT 0,      -- 今日累计超大单净流入 (>=100万元)
    large_inflow NUMERIC(18, 2) DEFAULT 0,            -- 今日累计大单净流入 (20万~100万元)
    middle_inflow NUMERIC(18, 2) DEFAULT 0,           -- 今日累计中单净流入 (4万~20万元)
    small_inflow NUMERIC(18, 2) DEFAULT 0,            -- 今日累计小单净流入 (<4万元，散户)
    main_inflow_ratio NUMERIC(6, 2) DEFAULT 0,        -- 主力净流入占比 (东财 f184，单位: %)
    
    -- 领涨股联动 (东财 f204 等)
    lead_stock_code VARCHAR(32),                      -- 领涨股代码 (如 688981)
    lead_stock_name VARCHAR(64),                      -- 领涨股名称 (如 中芯国际)
    lead_stock_change_pct NUMERIC(6, 2),              -- 领涨股涨幅 (%)
    
    -- 审计字段
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 核心业务索引
-- 【防重与幂等索引】：保证同一交易日、同一时间点、同一板块绝不重复入库 (支持 ON CONFLICT 批量安全写入)
CREATE UNIQUE INDEX IF NOT EXISTS uq_sector_flow_date_time_code 
ON sector_fund_flow_snapshots (trade_date, snapshot_time, sector_code);

-- 【分时走势聚合索引】：前端画“某板块全天 240 根分钟分时折线”时走覆盖索引
CREATE INDEX IF NOT EXISTS idx_sector_flow_timeline 
ON sector_fund_flow_snapshots (sector_code, trade_date, snapshot_time ASC);

-- 【全市场瞬间排行榜索引】：前端拖动滑块拉取“某特定时刻全市场 Top 榜”时极速排序
CREATE INDEX IF NOT EXISTS idx_sector_flow_snapshot_rank 
ON sector_fund_flow_snapshots (trade_date, snapshot_time, main_net_inflow DESC);

-- 表和字段注释
COMMENT ON TABLE sector_fund_flow_snapshots IS 'A股行业板块资金流分时快照表 (1分钟切片)';
COMMENT ON COLUMN sector_fund_flow_snapshots.trade_date IS '交易日期 (YYYY-MM-DD)';
COMMENT ON COLUMN sector_fund_flow_snapshots.snapshot_time IS '快照时刻 (HH:MM:SS)';
COMMENT ON COLUMN sector_fund_flow_snapshots.sector_code IS '板块代码 (如 BK0420)';
COMMENT ON COLUMN sector_fund_flow_snapshots.sector_name IS '板块名称 (如 光伏设备)';
COMMENT ON COLUMN sector_fund_flow_snapshots.change_pct IS '板块实时涨跌幅 (%)';
COMMENT ON COLUMN sector_fund_flow_snapshots.main_net_inflow IS '累计主力净流入额 (元)';
COMMENT ON COLUMN sector_fund_flow_snapshots.minute_net_inflow IS '本分钟瞬时净流入额 (元)';
COMMENT ON COLUMN sector_fund_flow_snapshots.super_large_inflow IS '累计超大单净流入额 (元)';
COMMENT ON COLUMN sector_fund_flow_snapshots.large_inflow IS '累计大单净流入额 (元)';
COMMENT ON COLUMN sector_fund_flow_snapshots.middle_inflow IS '累计中单净流入额 (元)';
COMMENT ON COLUMN sector_fund_flow_snapshots.small_inflow IS '累计小单净流入额 (元)';
COMMENT ON COLUMN sector_fund_flow_snapshots.main_inflow_ratio IS '主力净流入占比 (%)';
COMMENT ON COLUMN sector_fund_flow_snapshots.lead_stock_name IS '领涨股名称';
