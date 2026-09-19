package com.trading.dashboard.vo;

import com.fasterxml.jackson.annotation.JsonProperty;
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
public class SectorRankItemVO implements Serializable {

    @JsonProperty("sector_code")
    private String sectorCode;

    @JsonProperty("sector_name")
    private String sectorName;

    @JsonProperty("change_pct")
    private BigDecimal changePct;

    @JsonProperty("main_net_inflow")
    private BigDecimal mainNetInflow;

    @JsonProperty("main_net_inflow_yi")
    private BigDecimal mainNetInflowYi;

    @JsonProperty("minute_net_inflow")
    private BigDecimal minuteNetInflow;

    @JsonProperty("main_inflow_ratio")
    private BigDecimal mainInflowRatio;

    @JsonProperty("lead_stock_name")
    private String leadStockName;

    @JsonProperty("lead_stock_code")
    private String leadStockCode;

    @JsonProperty("lead_stock_change_pct")
    private BigDecimal leadStockChangePct;
}
