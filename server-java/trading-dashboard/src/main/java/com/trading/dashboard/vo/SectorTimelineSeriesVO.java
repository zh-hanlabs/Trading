package com.trading.dashboard.vo;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.List;

/**
 * 单个板块全天时序走势折线数据点
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SectorTimelineSeriesVO implements Serializable {

    @JsonProperty("sector_code")
    private String sectorCode;

    @JsonProperty("sector_name")
    private String sectorName;

    /**
     * 对应 timeline 中每个时间点的累计主力净流入 (单位: 亿元)
     */
    @JsonProperty("points")
    private List<BigDecimal> points;
}
