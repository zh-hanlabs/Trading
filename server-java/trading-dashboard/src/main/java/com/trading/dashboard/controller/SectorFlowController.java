package com.trading.dashboard.controller;

import com.trading.dashboard.common.Result;
import com.trading.dashboard.service.SectorFlowService;
import com.trading.dashboard.vo.SectorRankVO;
import com.trading.dashboard.vo.SectorTimelineVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
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
@Tag(name = "板块资金流接口", description = "提供实时板块资金流排行榜、历史切片快照与240点分时累积走势曲线")
public class SectorFlowController {

    private final SectorFlowService sectorFlowService;

    /**
     * 1. 获取板块资金流最新实时排行榜
     *
     * GET /api/dashboard/sector-flow/realtime?top_n=10
     */
    @Operation(summary = "获取板块资金流最新实时排行榜", description = "查询数据库中最新一个时间切片的全市场板块资金流排行，包含流入前N与流出前N")
    @GetMapping("/realtime")
    public Result<SectorRankVO> getRealtimeRank(
            @Parameter(description = "展示排名前 N 位板块，默认 10")
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
    @Operation(summary = "获取特定历史时间切片快照排行榜", description = "支持根据交易日和具体时刻回溯当时的市场板块资金流排行（供前端时间滑块联动使用）")
    @GetMapping("/snapshot")
    public Result<SectorRankVO> getSnapshotRank(
            @Parameter(description = "交易日期，格式 YYYY-MM-DD，为空则自动取数据库最新交易日")
            @RequestParam(value = "trade_date", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate tradeDate,
            @Parameter(description = "切片时刻，格式 HH:mm:ss，为空则自动取该交易日最新时刻")
            @RequestParam(value = "snapshot_time", required = false)
            @DateTimeFormat(pattern = "HH:mm:ss") LocalTime snapshotTime,
            @Parameter(description = "展示排名前 N 位板块，默认 10")
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
    @Operation(summary = "获取板块日内 240 点全天分时累积走势曲线", description = "支持查询指定日期下多个板块（如自选板块或Top流入板块）的240分钟分时累积净流入曲线")
    @GetMapping("/timeline")
    public Result<SectorTimelineVO> getTimeline(
            @Parameter(description = "交易日期，格式 YYYY-MM-DD，为空则自动取数据库最新交易日")
            @RequestParam(value = "trade_date", required = false)
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate tradeDate,
            @Parameter(description = "板块代码列表，多个以英文逗号分隔，如 BK1036,BK0420；为空则默认取流入前5与流出前5")
            @RequestParam(value = "sector_codes", required = false) List<String> sectorCodes
    ) {
        SectorTimelineVO vo = sectorFlowService.getTimeline(tradeDate, sectorCodes);
        return Result.success(vo);
    }
}
