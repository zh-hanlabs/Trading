# A 股投研系统开发与交互规范 (GEMINI.md)

> **定位**：本文件为仓库级持久化全局约束，所有与本项目交互的 AI 助手（包括新会话、新模型）必须强制遵循。

---

## 1. 项目技术栈与目录职责划分

### 1.1 核心技术栈
- **数据与智能体引擎**：Python 3.11 + FastAPI (SSE) + HTTPX + Pandas + psycopg2
- **高频时序数据底座**：PostgreSQL 16（Docker 容器化部署）
- **业务中台与微服务网关**：JDK 21 + Spring Boot 3.3 + Spring Cloud Gateway + MyBatis-Plus
- **前端交互看盘终端**：Vue 3 + Vite + TypeScript + Pinia + ECharts 6

### 1.2 目录职责划分
```text
Trading/
├── docs/             # 核心设计文档库、接口字典与交接班便签 (docs/ai/handoff.md)
├── docker/           # 基础设施与数据库容器编排 (仅托管 PostgreSQL 16)
├── agent-python/     # Python 1分钟资金流采集机 + ReAct 智能体引擎 (SSE服务 :8000)
├── server-java/      # Java 业务中台 (gateway :8080, dashboard :8081)
└── web-vue/          # Vue 3 终端看板与智能体交互抽屉
```

---

## 2. 硬性禁止事项与架构约束

### 2.1 交互四大约束（最高优先级）
1. **绝对禁止擅自抢跑**：用户说一步做一步。未得到主程序员的明确指令，严禁擅自推进到下一个阶段，严禁编写未授权代码。
2. **坚持结对编程（Pair Programming）**：AI 仅为副驾驶（Co-pilot），用户才是主程序员。任何代码编写、技术选型变更、文件创建前，必须先与用户确认。
3. **保持操作克制与透明**：每次执行命令或修改前，先用一两句话简要说明“我接下来要执行什么”，得到认可后再执行。
4. **拒绝自作主张**：遇到多种实现路径或设计选择时，必须列出选项交由用户决策，严禁替用户拍板。

### 2.2 核心架构与数据流约束
- **严格读写分离**：`agent-python` 为数据库的**唯一写入端 (Writer)**；`server-java` 为**唯一只读端 (Reader)**；前端只允许对接网关 (`:8080`)，严禁跳过网关直连内部微服务或数据库。
- **高频写入幂等防重**：资金流快照写入必须强依赖 `(trade_date, snapshot_time, sector_code)` 联合唯一键，禁止重复插入导致脏数据。
- **零硬编码密钥**：严禁将真实密码、Token 提交至代码库，所有配置均通过 `.env` 或系统环境变量注入。

---

## 3. 常用运维、构建、测试与 Lint 命令

### 3.1 基础设施 (Docker)
```powershell
# 启动 PostgreSQL 16 数据库
docker compose -f docker/docker-compose.yml up -d
# 查看容器运行状态
docker compose -f docker/docker-compose.yml ps
# 停止容器
docker compose -f docker/docker-compose.yml down
```

### 3.2 Python 模块 (`agent-python`)
```powershell
pip install -r requirements.txt            # 安装依赖
ruff check .                               # 代码规范检查 (Lint)
ruff format .                              # 代码自动格式化
pytest                                     # 执行测试用例
uvicorn app.main:app --reload --port 8000  # 本地调试启动
```

### 3.3 Java 模块 (`server-java`)
```powershell
mvn clean package -DskipTests              # 打包所有模块
mvn test                                   # 执行单元测试
mvn -pl trading-gateway spring-boot:run    # 单独启动统一网关 (:8080)
mvn -pl trading-dashboard spring-boot:run  # 单独启动看板中台 (:8081)
```

### 3.4 前端模块 (`web-vue`)
```powershell
npm install        # 安装依赖
npm run dev        # 启动本地开发服务
npm run build      # 类型检查与生产打包
npm run lint       # ESLint 检查与修复
```

---

## 4. 代码风格与 Git 提交规范

### 4.1 代码风格
- **Python**：严格遵循 PEP 8 规范，函数与核心变量必须具备显式类型注解（Type Hints）。
- **Java**：遵循 Google Java Style / 阿里开发手册，使用 Lombok 消除冗余代码，保持三层架构分明。
- **Vue / TS**：统一采用 Vue 3 `<script setup lang="ts">` 组合式 API，严格声明 Props 与 Emits 类型。

### 4.2 Git 提交规范 (Conventional Commits)
每次提交格式必须为：`<type>(<scope>): <subject>`
- `feat`: 新增业务功能（如：`feat(collector): 增加12点迟到开机自愈补数逻辑`）
- `fix`: 修复 bug（如：`fix(db): 修复联合唯一索引重复写入冲突`）
- `docs`: 文档变动（如：`docs(spec): 更新前后端接口字段字典`）
- `refactor`: 重构或清理代码（无业务逻辑变更）
- `test`: 增加或修改测试用例

---

## 5. 人工审查边界（必须暂停并向主程序员请示）

遇到以下任何一种情况，AI **严禁自行实施**，必须输出方案后停下等待主程序员审查批准：
1. **数据库 DDL/DML 变更**：任何建表、删表、修改字段类型、DROP/TRUNCATE 操作；
2. **核心依赖与端口变更**：新增重型第三方库，或修改网关/服务端口分配；
3. **敏感凭据与配置暴露**：涉及真实鉴权 Token、数据库生产密码等变动；
4. **批量删除或重构现有文件**：任何涉及已有业务模块删除或破坏性改动。