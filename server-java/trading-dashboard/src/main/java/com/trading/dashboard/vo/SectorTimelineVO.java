package com.trading.dashboard.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
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
public class SectorTimelineVO implements Serializable {

    @JsonProperty("trade_date")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate tradeDate;

    /**
     * 横轴刻度列表 (如 "09:31", "09:32", ...)
     */
    @JsonProperty("timeline")
    private List<String> timeline;

    /**
     * 各板块时序数据折线集
     */
    @JsonProperty("series")
    private List<SectorTimelineSeriesVO> series;
}
