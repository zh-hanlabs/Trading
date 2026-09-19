package com.trading.dashboard.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.trading.dashboard.entity.SectorSnapshot;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;

/**
 * 板块资金流快照数据访问层 (基于 PostgreSQL 覆盖索引与排序索引)
 */
@Mapper
public interface SectorSnapshotMapper extends BaseMapper<SectorSnapshot> {

    /**
     * 查询库中最近的一个交易日
     */
    @Select("SELECT MAX(trade_date) FROM sector_fund_flow_snapshots")
    LocalDate selectLatestTradeDate();

    /**
     * 查询指定交易日已记录的最新快照时刻
     */
    @Select("SELECT MAX(snapshot_time) FROM sector_fund_flow_snapshots WHERE trade_date = #{tradeDate}")
    LocalTime selectLatestSnapshotTime(@Param("tradeDate") LocalDate tradeDate);

    /**
     * 走 idx_sector_flow_snapshot_rank 索引极速拉取某一切片的资金流入榜
     */
    List<SectorSnapshot> selectTopInflowBySnapshot(
            @Param("tradeDate") LocalDate tradeDate,
            @Param("snapshotTime") LocalTime snapshotTime,
            @Param("limit") int limit
    );

    /**
     * 走 idx_sector_flow_snapshot_rank 索引极速拉取某一切片的资金流出榜
     */
    List<SectorSnapshot> selectTopOutflowBySnapshot(
            @Param("tradeDate") LocalDate tradeDate,
            @Param("snapshotTime") LocalTime snapshotTime,
            @Param("limit") int limit
    );

    /**
     * 走 idx_sector_flow_timeline 覆盖索引拉取指定板块全天分时走势
     */
    List<SectorSnapshot> selectTimelineBySectors(
            @Param("tradeDate") LocalDate tradeDate,
            @Param("sectorCodes") List<String> sectorCodes
    );
}
