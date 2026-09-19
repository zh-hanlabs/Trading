# A 股全栈数据源与原生接口地址字典 (全网原生 URL 清单)

> **版本**：v1.0.0  
> **定位**：记录底层爬取与对接的**第三方原生真实外网接口（EastMoney/Tencent/Baidu/Sina/巨潮等）**。  
> **用途**：后端开发者查阅底层通信协议、请求头（Header）、参数加密逻辑与原始响应格式。

---

## 目录
1. [行情层原生接口（腾讯 CDN / 百度 / 通达信 / 新浪）](#1-行情层原生接口)
2. [资金面与板块资金流原生接口（东财 push2）](#2-资金面与板块资金流原生接口)
3. [研报与一致预期原生接口（东财 / 同花顺 / i问财）](#3-研报与一致预期原生接口)
4. [新闻资讯与快讯原生接口（财联社 / 东财）](#4-新闻资讯与快讯原生接口)
5. [基础数据与财务原生接口（新浪三表 / 巨潮公告）](#5-基础数据与财务原生接口)
6. [超短打板与异动池原生接口（东财 push2ex）](#6-超短打板与异动池原生接口)

---

## 1. 行情层原生接口

### 1.1 腾讯极速实时行情与盘口 (首推，毫秒级，永不封 IP)
- **原生 URL**：`http://qt.gtimg.cn/q={symbols}`
- **请求方式**：`GET`
- **请求头要求**：无特殊要求，标准 HTTP 即可
- **参数说明**：
  - `symbols`：股票/指数代码，英文逗号分隔（如 `sh600519,sz000001,sh000001`）
- **原生返回示例** (字符串分号分隔)：
  ```text
  v_sh600519="1~贵州茅台~600519~1428.50~1412.30~1415.00~28910~...~23.40~...~17942.50~";
  ```
- **字段解析**：
  - 下标 1: 股票名称
  - 下标 2: 股票代码
  - 下标 3: 最新现价
  - 下标 4: 昨收盘价
  - 下标 5: 今开盘价
  - 下标 6: 成交量 (手)
  - 下标 31: 涨跌额 (元)
  - 下标 32: 涨跌幅 (%)
  - 下标 33: 最高价
  - 下标 34: 最低价
  - 下标 37: 成交额 (万元)
  - 下标 39: 市盈率 PE(TTM)
  - 下标 45: 总市值 (亿元)

---

### 1.2 百度股市通日 K 线 (带 MA5/10/20 均线，免本地计算)
- **原生 URL**：`https://finance.pae.baidu.com/vapi/v1/getquotation`
- **请求方式**：`GET`
- **请求参数**：
  - `srcid`: `5353`
  - `pointType`: `string`
  - `group`: `share_index_minute` (分时) 或 `share_index_day` (日K)
  - `all`: `1`
  - `code`: 股票代码（如 `600519`）
  - `market`: `ab` (A股)
- **原生返回核心结构**：JSON 格式，直接包含 `price`、`ma5`、`ma10`、`ma20`、`volume` 数组。

---

### 1.3 通达信底层行情协议 (mootdx)
- **底层协议**：`TCP Socket` 直连通达信行情总站
- **默认端口**：`7709`
- **通信特点**：二进制数据流解包，拉取全量历史日K、5分钟K线和逐笔委托，无 HTTP 防火墙限制。

---

## 2. 资金面与板块资金流原生接口

### 2.1 东方财富板块实时资金流向排行榜 (首期核心)
- **原生 URL**：`http://push2.eastmoney.com/api/qt/clist/get`
- **请求方式**：`GET`
- **必须携带的请求头**：
  ```http
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
  Referer: http://quote.eastmoney.com/
  ```
- **核心查询参数**：
  - `pn`: `1`（**页码，必须传，缺省会导致返回 data: null**）
  - `pz`: `100`（每页条数，传 100 即可覆盖全市场行业板块）
  - `po`: `1`（排序方向，1 为从大到小降序）
  - `np`: `1`
  - `fltt`: `2`
  - `invt`: `2`
  - `fid`: `f62`（排序依据字段，`f62` 表示今日主力净流入金额）
  - `fs`: `m:90+t:2`（`m:90+t:2` 为行业板块，`m:90+t:3` 为概念板块，`m:90+t:1` 为地域板块）
  - `fields`: `f12,f14,f3,f62,f184,f66,f72,f78,f84,f204`
- **字段含义对照表**：
  | 字段代码 | 业务含义 | 数据单位 |
  | :--- | :--- | :--- |
  | `f12` | 板块代码 (如 BK1036) | 字符串 |
  | `f14` | 板块名称 (如 半导体) | 字符串 |
  | `f3` | 板块今日涨跌幅 | % |
  | `f62` | **主力净流入额 (超大单+大单)** | 元 |
  | `f184`| 主力净流入占比 | % |
  | `f66` | 超大单净流入额 | 元 |
  | `f72` | 大单净流入额 | 元 |
  | `f78` | 中单净流入额 | 元 |
  | `f84` | 小单净流入额 | 元 |
  | `f204`| 今日板块领涨龙头股名称 | 字符串 |

---

### 2.2 东方财富板块/个股日内分钟级资金曲线 (日内走势神器)
- **原生 URL**：`http://push2.eastmoney.com/api/qt/stock/fflow/kline/get`
- **请求方式**：`GET`
- **请求头**：同 2.1
- **参数说明**：
  - `secid`: `90.{板块代码}`（如 `90.BK1036` 代表半导体板块；个股如 `1.600519` 沪市、`0.000001` 深市）
  - `klt`: `1`（1 代表分钟级分时）
  - `fields1`: `f1,f2,f3,f7`
  - `fields2`: `f51,f52,f53,f54,f55,f56,f57`
- **原生响应格式 (`data.klines`)**：
  ```text
  "2026-09-18 09:31,183158202.0,-75462693.0,-10705720.0,39565567.0,143592634.0"
  ```
  - `CSV项 0`: 时间点 `YYYY-MM-DD HH:MM`
  - `CSV项 1`: 主力累积净流入 (元)
  - `CSV项 2`: 小单累积净流入 (元)
  - `CSV项 3`: 中单累积净流入 (元)
  - `CSV项 4`: 大单累积净流入 (元)
  - `CSV项 5`: 超大单累积净流入 (元)

---

### 2.3 东方财富数据中心通用查询接口 (龙虎榜 / 解禁 / 两融 / 股东户数)
- **原生 URL**：`https://datacenter-web.eastmoney.com/api/data/v1/get`
- **请求方式**：`GET`
- **通用参数**：
  - `reportName`: 报表代码（例如 `RPT_DAILY_LHB` 龙虎榜、`RPT_LIFT_STAGE` 解禁、`RPTA_WEB_RZRQ_GG_LS` 个股两融）
  - `columns`: `ALL`
  - `filter`: 过滤条件字符串（如 `(SECURITY_CODE="600519")`）
  - `pageNumber`: `1`
  - `pageSize`: `50`
  - `sortColumns`: 排序字段
  - `sortTypes`: `-1` (降序)

---

## 3. 研报与一致预期原生接口

### 3.1 东方财富机构研报列表与 PDF
- **研报列表 URL**：`https://reportapi.eastmoney.com/report/list`
  - 参数：`qType=0`(个股) 或 `qType=1`(行业)；`code={symbol}`；`pageSize=20`
- **研报 PDF 原始直链**：`https://pdf.dfcfw.com/pdf/H3_{infoCode}_1.pdf`
  - **反爬注意**：下载 PDF 时必须带请求头 `Referer: https://data.eastmoney.com/`，否则返回 403。

### 3.2 同花顺机构一致预期 (EPS / 目标价)
- **原生 URL**：`https://basic.10jqka.com.cn/api/stock/finance/{code}_forecast.json`
- **返回数据**：各家券商对该股票未来三年的营业收入、净利润、每股收益（EPS）预测平均值。

---

## 4. 新闻资讯与快讯原生接口

### 4.1 财联社电报快讯 (毫秒级短讯)
- **原生 URL**：`https://m.cls.cn/v1/roll/get_roll_list`
- **请求方式**：`GET`
- **签名校验机制**：
  - 参数包含 `app=Cphone`, `os=android`, `sv=8.4.6`, `sign=...`
  - `sign` 计算规则：本地对参数按照 ASCII 排序后执行 `MD5(SHA1(query_string))`，无需向官方申请 Key。

### 4.2 东方财富 7x24 全球快讯
- **原生 URL**：`https://np-weblist.eastmoney.com/comm/web/getNewsList`
  - 参数：`client=web`, `biz=web_news_col`, `column=354`, `pageSize=20`

---

## 5. 基础数据与财务原生接口

### 5.1 新浪财报标准三表
- **原生 URL**：
  - 资产负债表：`https://quotes.sina.cn/cn/api/jsonp_v2.php/var%20report=/FinanceService.getFinanceReport?symbol={symbol}&type=zcfzb`
  - 利润表：`type=lrb`
  - 现金流量表：`type=xjllb`

### 5.2 巨潮资讯全量官方公告 (法定信披一手源)
- **原生 URL**：`http://www.cninfo.com.cn/new/hisAnnouncement/query`
- **请求方式**：`POST` (表单)
- **参数**：
  - `stock`: 股票代码与 orgId 映射（如 `600519,gssx0000519`）
  - `tabName`: `fulltext`
  - `pageSize`: `30`
  - `pageNum`: `1`
  - `column`: `sse` (沪市) 或 `szse` (深市)
- **附件直链**：`http://static.cninfo.com.cn/{adjunctUrl}` (官方 PDF 公告直接下载)

---

## 6. 超短打板与异动池原生接口

### 6.1 东方财富涨停板池 / 炸板池 / 跌停池
- **原生 URL**：`http://push2ex.eastmoney.com/getTopicZTPool`
- **请求方式**：`GET`
- **参数**：
  - `ut`: `7eea3edcaed7343ac4c544f48dd036b0`
  - `dpt`: `wz.ztzt`
  - `date`: 当前日期（如 `20260918`）
- **返回字段**：封板金额、首封时间、最后封板时间、几天几板（如 `3天2板`）、炸板次数、所属细分行业。
