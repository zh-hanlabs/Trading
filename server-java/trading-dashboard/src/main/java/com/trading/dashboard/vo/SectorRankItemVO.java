package com.trading.dashboard.vo;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.math.BigDecimal;

/**
 * 板块排行榜单项数据视图对象
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "板块资金流排行榜条目")
public class SectorRankItemVO implements Serializable {

    @Schema(description = "板块代码", example = "BK1036")
    @JsonProperty("sector_code")
    private String sectorCode;

    @Schema(description = "板块名称", example = "半导体")
    @JsonProperty("sector_name")
    private String sectorName;

    @Schema(description = "板块最新涨跌幅 (%)", example = "2.35")
    @JsonProperty("change_pct")
    private BigDecimal changePct;

    @Schema(description = "主力净流入 (元)", example = "1250000000.00")
    @JsonProperty("main_net_inflow")
    private BigDecimal mainNetInflow;

    @Schema(description = "主力净流入 (亿元，保留两位小数)", example = "12.50")
    @JsonProperty("main_net_inflow_yi")
    private BigDecimal mainNetInflowYi;

    @Schema(description = "最近一分钟边际净流入 (元)", example = "15000000.00")
    @JsonProperty("minute_net_inflow")
    private BigDecimal minuteNetInflow;

    @Schema(description = "主力资金净流入占比 (%)", example = "5.82")
    @JsonProperty("main_inflow_ratio")
    private BigDecimal mainInflowRatio;

    @Schema(description = "领涨龙头股名称", example = "中芯国际")
    @JsonProperty("lead_stock_name")
    private String leadStockName;

    @Schema(description = "领涨龙头股代码", example = "688981")
    @JsonProperty("lead_stock_code")
    private String leadStockCode;

    @Schema(description = "领涨龙头股涨跌幅 (%)", example = "6.18")
    @JsonProperty("lead_stock_change_pct")
    private BigDecimal leadStockChangePct;
}
