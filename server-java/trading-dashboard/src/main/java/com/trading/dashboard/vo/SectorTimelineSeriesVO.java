package com.trading.dashboard.vo;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
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
@Schema(description = "单个板块分时时序折线数据")
public class SectorTimelineSeriesVO implements Serializable {

    @Schema(description = "板块代码", example = "BK1036")
    @JsonProperty("sector_code")
    private String sectorCode;

    @Schema(description = "板块名称", example = "半导体")
    @JsonProperty("sector_name")
    private String sectorName;

    /**
     * 对应 timeline 中每个时间点的累计主力净流入 (单位: 亿元)
     */
    @Schema(description = "对应 timeline 中各时间点的累积主力净流入数组 (单位: 亿元)")
    @JsonProperty("points")
    private List<BigDecimal> points;
}
