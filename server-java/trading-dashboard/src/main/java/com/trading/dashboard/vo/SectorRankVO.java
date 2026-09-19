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
 * 板块资金流入与流出排行榜响应视图
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "板块资金流流入与流出排行榜视图")
public class SectorRankVO implements Serializable {

    @Schema(description = "交易日期", example = "2026-09-18")
    @JsonProperty("trade_date")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate tradeDate;

    @Schema(description = "快照时间点", example = "10:30:00")
    @JsonProperty("snapshot_time")
    private String snapshotTime;

    @Schema(description = "净流入排行前 N 板块列表")
    @JsonProperty("top_inflow")
    private List<SectorRankItemVO> topInflow;

    @Schema(description = "净流出排行前 N 板块列表")
    @JsonProperty("top_outflow")
    private List<SectorRankItemVO> topOutflow;
}
