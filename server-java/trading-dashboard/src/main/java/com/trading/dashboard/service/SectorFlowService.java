package com.trading.dashboard.service;

import com.trading.dashboard.vo.SectorRankVO;
import com.trading.dashboard.vo.SectorTimelineVO;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;

/**
 * 板块资金流向业务中台服务接口
 */
public interface SectorFlowService {

    /**
     * 获取板块资金流最新实时排行榜
     *
     * @param topN 前 N 个板块 (默认 10)
     * @return 榜单视图对象
     */
    SectorRankVO getRealtimeRank(Integer topN);

    /**
     * 获取指定时间切片的历史快照排行榜 (支持时间滑块拖拽联动)
     *
     * @param tradeDate    交易日期 (YYYY-MM-DD，缺省为最新交易日)
     * @param snapshotTime 快照时刻 (HH:MM:SS)
     * @param topN         前 N 个板块 (默认 10)
     * @return 榜单视图对象
     */
    SectorRankVO getSnapshotRank(LocalDate tradeDate, LocalTime snapshotTime, Integer topN);

    /**
     * 获取板块日内 240 点全天分时主力资金累积走势折线图
     *
     * @param tradeDate   交易日期 (缺省为最新交易日)
     * @param sectorCodes 指定对比的板块代码列表 (若为空则默认呈现当日净流入 Top 5 板块)
     * @return 走势图完整视图对象
     */
    SectorTimelineVO getTimeline(LocalDate tradeDate, List<String> sectorCodes);
}
