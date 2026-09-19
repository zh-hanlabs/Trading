package com.trading.dashboard.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDate;
import java.util.List;

/**
 * 板块日内 240 点全天资金流时序折线图完整视图对象
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "板块资金流 240 点分时累积走势时序视图")
public class SectorTimelineVO implements Serializable {

    @Schema(description = "交易日期", example = "2026-09-18")
    @JsonProperty("trade_date")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate tradeDate;

    /**
     * 横轴刻度列表 (如 "09:31", "09:32", ...)
     */
    @Schema(description = "横轴时间刻度列表 (240 个点，如 ['09:31', '09:32', ...])")
    @JsonProperty("timeline")
    private List<String> timeline;

    /**
     * 各板块时序数据折线集
     */
    @Schema(description = "各板块时序数据折线集")
    @JsonProperty("series")
    private List<SectorTimelineSeriesVO> series;
}
