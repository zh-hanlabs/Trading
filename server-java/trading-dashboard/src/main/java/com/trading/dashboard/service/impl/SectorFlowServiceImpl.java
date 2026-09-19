package com.trading.dashboard.service.impl;

import com.trading.dashboard.entity.SectorSnapshot;
import com.trading.dashboard.mapper.SectorSnapshotMapper;
import com.trading.dashboard.service.SectorFlowService;
import com.trading.dashboard.vo.SectorRankItemVO;
import com.trading.dashboard.vo.SectorRankVO;
import com.trading.dashboard.vo.SectorTimelineSeriesVO;
import com.trading.dashboard.vo.SectorTimelineVO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 板块资金流中台业务实现类
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SectorFlowServiceImpl implements SectorFlowService {

    private static final BigDecimal YI = new BigDecimal("100000000");
    private static final DateTimeFormatter TIME_SEC_FORMATTER = DateTimeFormatter.ofPattern("HH:mm:ss");
    private static final DateTimeFormatter TIME_MIN_FORMATTER = DateTimeFormatter.ofPattern("HH:mm");

    private final SectorSnapshotMapper sectorSnapshotMapper;

    @Override
    public SectorRankVO getRealtimeRank(Integer topN) {
        int limit = (topN == null || topN <= 0) ? 10 : topN;

        LocalDate latestDate = sectorSnapshotMapper.selectLatestTradeDate();
        if (latestDate == null) {
            log.info("数据库暂无任何交易日快照数据");
            return emptyRankVO(null, null);
        }

        LocalTime latestTime = sectorSnapshotMapper.selectLatestSnapshotTime(latestDate);
        if (latestTime == null) {
            return emptyRankVO(latestDate, null);
        }

        return buildRankVO(latestDate, latestTime, limit);
    }

    @Override
    public SectorRankVO getSnapshotRank(LocalDate tradeDate, LocalTime snapshotTime, Integer topN) {
        int limit = (topN == null || topN <= 0) ? 10 : topN;

        LocalDate targetDate = tradeDate != null ? tradeDate : sectorSnapshotMapper.selectLatestTradeDate();
        if (targetDate == null) {
            return emptyRankVO(null, null);
        }

        LocalTime targetTime = snapshotTime != null ? snapshotTime : sectorSnapshotMapper.selectLatestSnapshotTime(targetDate);
        if (targetTime == null) {
            return emptyRankVO(targetDate, null);
        }

        return buildRankVO(targetDate, targetTime, limit);
    }

    @Override
    public SectorTimelineVO getTimeline(LocalDate tradeDate, List<String> sectorCodes) {
        LocalDate targetDate = tradeDate != null ? tradeDate : sectorSnapshotMapper.selectLatestTradeDate();
        if (targetDate == null) {
            return SectorTimelineVO.builder()
                    .tradeDate(null)
                    .timeline(Collections.emptyList())
                    .series(Collections.emptyList())
                    .build();
        }

        List<String> targetCodes = sectorCodes;
        // 若未指定板块代码，则默认提取该交易日最新切片资金流入前 5 的核心主线板块
        if (targetCodes == null || targetCodes.isEmpty()) {
            LocalTime latestTime = sectorSnapshotMapper.selectLatestSnapshotTime(targetDate);
            if (latestTime != null) {
                List<SectorSnapshot> topSectors = sectorSnapshotMapper.selectTopInflowBySnapshot(targetDate, latestTime, 5);
                targetCodes = topSectors.stream().map(SectorSnapshot::getSectorCode).toList();
            }
        }

        if (targetCodes == null || targetCodes.isEmpty()) {
            return SectorTimelineVO.builder()
                    .tradeDate(targetDate)
                    .timeline(Collections.emptyList())
                    .series(Collections.emptyList())
                    .build();
        }

        List<SectorSnapshot> records = sectorSnapshotMapper.selectTimelineBySectors(targetDate, targetCodes);
        if (records.isEmpty()) {
            return SectorTimelineVO.builder()
                    .tradeDate(targetDate)
                    .timeline(Collections.emptyList())
                    .series(Collections.emptyList())
                    .build();
        }

        // 1. 提取所有时间刻度 (有序排列 "09:31", "09:32"...)
        List<String> timeline = records.stream()
                .map(r -> r.getSnapshotTime().format(TIME_MIN_FORMATTER))
                .distinct()
                .sorted()
                .toList();

        // 2. 按 sectorCode 分组归集
        Map<String, List<SectorSnapshot>> groupedBySector = records.stream()
                .collect(Collectors.groupingBy(SectorSnapshot::getSectorCode));

        List<SectorTimelineSeriesVO> seriesList = new ArrayList<>();
        for (String code : targetCodes) {
            List<SectorSnapshot> sectorRecords = groupedBySector.get(code);
            if (sectorRecords == null || sectorRecords.isEmpty()) {
                continue;
            }

            String sectorName = sectorRecords.get(0).getSectorName();

            // 构建时刻映射 map: "09:31" -> 资金流入 (亿元)
            Map<String, BigDecimal> timeToInflow = new HashMap<>();
            for (SectorSnapshot r : sectorRecords) {
                String timeStr = r.getSnapshotTime().format(TIME_MIN_FORMATTER);
                BigDecimal inflowYi = r.getMainNetInflow() != null
                        ? r.getMainNetInflow().divide(YI, 2, RoundingMode.HALF_UP)
                        : BigDecimal.ZERO;
                timeToInflow.put(timeStr, inflowYi);
            }

            // 按 timeline 刻度依次对齐填补 points
            List<BigDecimal> points = new ArrayList<>(timeline.size());
            BigDecimal lastVal = BigDecimal.ZERO;
            for (String t : timeline) {
                BigDecimal val = timeToInflow.get(t);
                if (val != null) {
                    lastVal = val;
                }
                points.add(lastVal);
            }

            seriesList.add(SectorTimelineSeriesVO.builder()
                    .sectorCode(code)
                    .sectorName(sectorName)
                    .points(points)
                    .build());
        }

        return SectorTimelineVO.builder()
                .tradeDate(targetDate)
                .timeline(timeline)
                .series(seriesList)
                .build();
    }

    private SectorRankVO buildRankVO(LocalDate date, LocalTime time, int limit) {
        List<SectorSnapshot> inflowList = sectorSnapshotMapper.selectTopInflowBySnapshot(date, time, limit);
        List<SectorSnapshot> outflowList = sectorSnapshotMapper.selectTopOutflowBySnapshot(date, time, limit);

        return SectorRankVO.builder()
                .tradeDate(date)
                .snapshotTime(time.format(TIME_SEC_FORMATTER))
                .topInflow(inflowList.stream().map(this::convertItem).toList())
                .topOutflow(outflowList.stream().map(this::convertItem).toList())
                .build();
    }

    private SectorRankItemVO convertItem(SectorSnapshot s) {
        BigDecimal mainInflow = s.getMainNetInflow() != null ? s.getMainNetInflow() : BigDecimal.ZERO;
        BigDecimal mainInflowYi = mainInflow.divide(YI, 2, RoundingMode.HALF_UP);

        return SectorRankItemVO.builder()
                .sectorCode(s.getSectorCode())
                .sectorName(s.getSectorName())
                .changePct(s.getChangePct())
                .mainNetInflow(mainInflow)
                .mainNetInflowYi(mainInflowYi)
                .minuteNetInflow(s.getMinuteNetInflow())
                .mainInflowRatio(s.getMainInflowRatio())
                .leadStockCode(s.getLeadStockCode())
                .leadStockName(s.getLeadStockName())
                .leadStockChangePct(s.getLeadStockChangePct())
                .build();
    }

    private SectorRankVO emptyRankVO(LocalDate date, LocalTime time) {
        return SectorRankVO.builder()
                .tradeDate(date)
                .snapshotTime(time != null ? time.format(TIME_SEC_FORMATTER) : null)
                .topInflow(Collections.emptyList())
                .topOutflow(Collections.emptyList())
                .build();
    }
}
