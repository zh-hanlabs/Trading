package com.trading.dashboard.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;

/**
 * 行业板块资金流分时快照持久化实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@TableName("sector_fund_flow_snapshots")
public class SectorSnapshot implements Serializable {

    @TableId(type = IdType.AUTO)
    private Long id;

    /**
     * 交易日期 (YYYY-MM-DD)
     */
    @TableField("trade_date")
    private LocalDate tradeDate;

    /**
     * 快照时刻 (HH:MM:SS)
     */
    @TableField("snapshot_time")
    private LocalTime snapshotTime;

    /**
     * 东方财富板块代码 (如 BK1036)
     */
    @TableField("sector_code")
    private String sectorCode;

    /**
     * 板块名称 (如 半导体)
     */
    @TableField("sector_name")
    private String sectorName;

    /**
     * 板块实时涨跌幅 (%)
     */
    @TableField("change_pct")
    private BigDecimal changePct;

    /**
     * 今日累计主力净流入额 (元，超大单+大单累计)
     */
    @TableField("main_net_inflow")
    private BigDecimal mainNetInflow;

    /**
     * 本分钟瞬时净流入额 (Δ，元)
     */
    @TableField("minute_net_inflow")
    private BigDecimal minuteNetInflow;

    /**
     * 累计超大单净流入额 (元)
     */
    @TableField("super_large_inflow")
    private BigDecimal superLargeInflow;

    /**
     * 累计大单净流入额 (元)
     */
    @TableField("large_inflow")
    private BigDecimal largeInflow;

    /**
     * 累计中单净流入额 (元)
     */
    @TableField("middle_inflow")
    private BigDecimal middleInflow;

    /**
     * 累计小单净流入额 (元)
     */
    @TableField("small_inflow")
    private BigDecimal smallInflow;

    /**
     * 主力净流入占比 (%)
     */
    @TableField("main_inflow_ratio")
    private BigDecimal mainInflowRatio;

    /**
     * 领涨股代码
     */
    @TableField("lead_stock_code")
    private String leadStockCode;

    /**
     * 领涨股名称
     */
    @TableField("lead_stock_name")
    private String leadStockName;

    /**
     * 领涨股涨幅 (%)
     */
    @TableField("lead_stock_change_pct")
    private BigDecimal leadStockChangePct;

    /**
     * 记录创建时间
     */
    @TableField("created_at")
    private LocalDateTime createdAt;
}
