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
 * 板块资金流入与流出排行榜响应视图
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SectorRankVO implements Serializable {

    @JsonProperty("trade_date")
    @JsonFormat(pattern = "yyyy-MM-dd")
    private LocalDate tradeDate;

    @JsonProperty("snapshot_time")
    private String snapshotTime;

    @JsonProperty("top_inflow")
    private List<SectorRankItemVO> topInflow;

    @JsonProperty("top_outflow")
    private List<SectorRankItemVO> topOutflow;
}
