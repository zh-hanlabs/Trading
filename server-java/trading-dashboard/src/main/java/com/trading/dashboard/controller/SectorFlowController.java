package com.trading.dashboard.controller;

import com.trading.dashboard.common.Result;
import com.trading.dashboard.service.SectorFlowService;
import com.trading.dashboard.vo.SectorRankVO;
import com.trading.dashboard.vo.SectorTimelineVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;

/**
 * 行业板块资金流向看板中台 RESTful 接口控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/dashboard/sector-flow")
@RequiredArgsConstructor
public class SectorFlowController {

    private final SectorFlowService sectorFlowService;

    /**
     * 1. 获取板块资金流最新实时排行榜
     *
     * GET /api/dashboard/sector-flow/realtime?top_n=10
     */
    @GetMapping("/realtime")
    public Result<SectorRankVO> getRealtimeRank(
            @RequestParam(value = "top_n", defaultValue = "10") Integer topN
    ) {
        SectorRankVO vo = sectorFlowService.getRealtimeRank(topN);
        return Result.success(vo);
    }

    /**
     * 2. 获取特定历史时间切片快照排行榜 (时间滑块联动)
     *
     * GET /api/dashboard/sector-flow/snapshot?trade_date=2026-09-18&snapshot_time=10:00:00&top_n=10
     */
    @GetMapping("/snapshot")
    public Result<SectorRankVO> getSnapshotRank(
            @RequestParam(value = "trade_date", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate tradeDate,
            @RequestParam(value = "snapshot_time", required = false)
            @DateTimeFormat(pattern = "HH:mm:ss") LocalTime snapshotTime,
            @RequestParam(value = "top_n", defaultValue = "10") Integer topN
    ) {
        SectorRankVO vo = sectorFlowService.getSnapshotRank(tradeDate, snapshotTime, topN);
        return Result.success(vo);
    }

    /**
     * 3. 获取板块日内 240 点全天分时累积走势曲线
     *
     * GET /api/dashboard/sector-flow/timeline?trade_date=2026-09-18&sector_codes=BK1036,BK0420
     */
    @GetMapping("/timeline")
    public Result<SectorTimelineVO> getTimeline(
            @RequestParam(value = "trade_date", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate tradeDate,
            @RequestParam(value = "sector_codes", required = false) List<String> sectorCodes
    ) {
        SectorTimelineVO vo = sectorFlowService.getTimeline(tradeDate, sectorCodes);
        return Result.success(vo);
    }
}
