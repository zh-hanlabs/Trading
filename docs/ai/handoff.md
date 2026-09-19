# AI 任务交接班便签 (Handoff)

> **说明**：本文件记录当前会话的动态开发状态与进度，供新开会话或更换模型时无缝接班。每次完成重要里程碑或会话结束前由副驾驶更新。

---

## 1. 当前任务目标 (Goal)
- **总体目标**：第一阶段（日内板块资金流向看板）全链路搭建（Python 采集 $\rightarrow$ PostgreSQL 存储 $\rightarrow$ Java 网关与中台 $\rightarrow$ Vue3 终端）。
- **当前小目标**：完成 Milestone 2 与 Milestone 3 的闭环联调与真实数据验证，准备推进 Milestone 4 前端工程化搭建。

## 2. 代码分支与环境 (Branch & Env)
- **当前目录**：`d:/Code/Trading`
- **代码分支**：`main`
- **核心组件**：
  - **Python 3.11 引擎** (`agent-python`:8000)：FastAPI + HTTPX + psycopg2 + ruff
  - **PostgreSQL 16 数据库** (`docker/docker-compose.yml`:5432)
  - **Java 21 业务中台与网关** (`server-java`: 网关 :8080, 看板 :8081)：Spring Boot 3.3.4 + Spring Cloud 2023 + MyBatis-Plus 3.5.7 + SpringDoc OpenAPI 3

## 3. 当前开发进度 (Current Status)
- [x] **架构设计与文档规范**：
  - 已就绪：`README.md`、`docs/项目计划书.md`、`docs/开发总纲与实施计划.md`、`docs/前后端接口对接规范.md`、`docs/A股数据源与原生接口字典.md`。
  - 已确立：`GEMINI.md`（长期持久化约束守则，零抢跑、结对编程、透明操作）。
- [x] **基础设施与数据库底座 (Milestone 1)**：
  - PostgreSQL 16 容器运行中，完成 `sector_fund_flow_snapshots` 表与 3 大核心索引创建验证。
- [x] **Python 数据挖掘机与采集引擎 (Milestone 2 核心就绪与接口服务化)**：
  - 完成 `app.collector`（models, eastmoney, storage, clock, backfill, engine）；
  - 核心客户端加固：切换为东财官方高可用数据中心域名 `push2delay.eastmoney.com`，增加 IPv4 socket 过滤与 `UT_TOKEN`，彻底免疫本地网络代理断连；
  - 暴露服务化接口：`POST /api/agent/collector/backfill` 与 `GET /api/agent/collector/status`，支持在线回补与监控；
  - 真实数据入库验证：成功拉取并入库 `2026-09-18` 全市场 200 个行业板块快照与重点主线板块分时走势线（共 1,870 条记录）。
- [x] **Java 业务中台与统一网关 (Milestone 3 已全部完成并联调通过)**：
  - 父工程 `trading-parent` 配置依赖仲裁（Java 21, Spring Boot 3.3.4, Spring Cloud 2023, SpringDoc 2.6.0）；
  - `trading-dashboard` (:8081)：
    - HikariCP 只读连接池配置与实体 `SectorSnapshot`（修正 `OffsetDateTime` 兼容 PostgreSQL `TIMESTAMPTZ`）；
    - Controller $\rightarrow$ Service $\rightarrow$ Mapper 三层架构与 MyBatis-Plus XML 排序联查；
    - 集成 SpringDoc OpenAPI 3，提供 Swagger 在线测试文档 (`/swagger-ui.html`)；
    - 成功联调返回实时/历史快照排行 (`/snapshot`) 与 240 点日内走势 (`/timeline`)。
  - `trading-gateway` (:8080)：
    - 基于响应式 WebFlux 底座；
    - 静态路由矩阵：`/api/dashboard/**` 直连 `:8081`，`/api/agent/**` 直连 `:8000`；
    - 全局 CORS 跨域配置已就绪。

## 4. 关键踩坑与技术沉淀 (Lessons Learned)
1. **东财网络断连 (Server disconnected)**：
   - 东方财富核心老节点 `push2.eastmoney.com` 部署了严格的反爬与 WAF 规则，且本地 VPN/Clash TUN 代理模式会通过 IPv6 Fake-IP 拦截流量触发重置；
   - 解决方案：切换至官方高可用节点 `push2delay.eastmoney.com`，并在网络层优先 IPv4 解析，增加 `ut` 安全令牌参数。
2. **PostgreSQL TIMESTAMPTZ 与 Java 时间类型映射**：
   - PostgreSQL 的 `TIMESTAMP WITH TIME ZONE` 在 pgjdbc 驱动中严格禁止隐式丢失时区转换为 `LocalDateTime`；
   - 必须使用 `java.time.OffsetDateTime` 映射，以保证时区与时间戳的强一致性。
3. **时序数据连续性权衡**：
   - 坚持落库全市场（或重点覆盖）板块数据，保证“流入前十”与“流出前十”双向计算，且避免日内突发拉升板块在早盘曲线出现空心断点。

## 5. 剩余待办清单 (Remaining Work)
1. 提交当前 Python 接口、Java 修复与交接文档至 Git；
2. 推进 **Milestone 4（前端终端看板与交互抽屉 `web-vue`）**：
   - 初始化 Vue 3 + Vite + TypeScript + Pinia + ECharts 6 工程；
   - 构建日内板块资金流看板三栏布局（顶部全局状态栏、左侧排行榜多维表格、右侧 ECharts 动态多折线时序图、右侧智能体抽屉）。

## 6. 建议下一步行动 (Suggested Next Step)
- 执行 Git 提交：`feat(java/agent): 完成东财高可用回补接口、Java中台Swagger集成与时区类型对齐`；
- 正式启动 `web-vue` 前端初始化。
