# NBA Prediction Agent System - 项目详细文档

## 一、项目概述

本项目是一个基于 **多智能体协作架构（Multi-Agent System）** 的 NBA 比赛结果预测系统。系统使用 **LangGraph** 编排 6 个 AI Agent 并行工作，从多个维度（近期表现、历史对战、伤病新闻、赔率市场、战术对位）收集和分析信息，最终由决策 Agent 综合所有报告给出结构化的比赛预测。

### 核心技术栈

| 技术 | 用途 | 说明 |
|------|------|------|
| **Python 3.10+** | 主语言 | 项目开发语言 |
| **LangGraph** | Agent 编排 | 基于有向图的多 Agent 工作流引擎，支持并行执行和状态管理 |
| **LangChain** | LLM 框架 | 提供 LLM 调用、Tool Calling、Structured Output 等能力 |
| **Qwen3-Max (通义千问)** | 大语言模型 | 通过阿里云 DashScope API 调用，作为所有 Agent 的推理引擎 |
| **FastAPI** | Web 框架 | 高性能异步 API 服务，提供 RESTful 接口 |
| **Streamlit** | 前端 UI | 快速构建数据应用的 Python 前端框架 |
| **ChromaDB** | 向量数据库 | 存储 NBA 历史对战数据的向量库，用于 RAG 检索 |
| **SQLite + SQLAlchemy** | 关系数据库 | 存储预测记录和评估结果，支持 ORM 操作 |
| **Tavily Search** | 实时搜索 | AI 原生的网络搜索 API，获取实时 NBA 数据 |
| **DashScope Embeddings** | 文本嵌入 | 阿里云的文本向量化服务，用于 RAG 中的文档向量化 |
| **Pydantic** | 数据验证 | 用于结构化输出、请求验证、配置管理 |
| **Tenacity** | 重试机制 | 提供指数退避的自动重试能力 |
| **Uvicorn** | ASGI 服务器 | 高性能的异步 Web 服务器 |

---

## 二、项目结构总览

```
project/
├── .gitignore                          # Git 忽略规则
├── requirements.txt                    # Python 依赖清单
├── nba_prediction.db                   # SQLite 数据库文件（运行时生成）
├── nba_knowledge_db/                   # ChromaDB 向量数据库目录（运行时生成）
│
├── scripts/
│   └── ingest_data.py                  # 数据摄入脚本：从 Basketball-Reference 抓取历史数据写入向量库
│
└── app/                                # 主应用目录
    ├── main.py                         # FastAPI 应用入口
    ├── frontend_ui.py                  # Streamlit 前端界面
    │
    ├── core/                           # 核心基础设施
    │   ├── config.py                   # 全局配置管理（Pydantic BaseSettings）
    │   ├── logger.py                   # 结构化日志系统
    │   └── cache.py                    # TTL 内存缓存
    │
    ├── graph/                          # LangGraph 工作流
    │   ├── __init__.py
    │   ├── workflow.py                 # 工作流定义 + 优雅降级封装
    │   └── nodes/                      # Agent 节点
    │       ├── __init__.py
    │       ├── state.py                # 共享状态定义（AgentState）
    │       ├── models.py              # 所有 Agent 的结构化输出模型
    │       ├── recent_analyst.py       # Agent 1: 近期表现分析师
    │       ├── history_analyst.py      # Agent 2: 历史对战分析师（RAG）
    │       ├── team_reporter.py        # Agent 3: 球队记者（ReAct 模式）
    │       ├── odds_analyst.py         # Agent 4: 赔率分析师
    │       ├── strategy_analyst.py     # Agent 5: 战术教练
    │       └── final_predictor.py      # Agent 6: 最终决策者
    │
    ├── tools/                          # 外部工具封装
    │   ├── __init__.py
    │   ├── nba_client.py              # NBA 数据客户端（搜索 + 缓存 + 重试）
    │   └── retriever.py               # RAG 检索管道（查询改写 + 重排序）
    │
    ├── prompts/                        # Prompt 模板管理
    │   ├── __init__.py
    │   └── templates.py               # 所有 Agent 的 Prompt 模板
    │
    ├── api/                            # API 路由层
    │   ├── deps.py                    # FastAPI 依赖注入
    │   └── routes.py                  # API 路由定义（6 个端点）
    │
    ├── db/                             # 数据库层
    │   ├── __init__.py
    │   ├── models.py                  # SQLAlchemy ORM 模型
    │   └── session.py                 # 数据库会话管理
    │
    └── utils/                          # 工具函数
        ├── __init__.py
        └── helpers.py                 # 辅助函数
```

---

## 三、每个文件的详细说明

---

### 根目录文件

---

#### `.gitignore`
**功能**：定义 Git 版本控制忽略的文件和目录。

**内容说明**：
- 忽略 `.env` 等敏感配置文件（防止 API 密钥泄露）
- 忽略 `__pycache__/` Python 编译缓存
- 忽略 `venv/` 虚拟环境目录
- 忽略 `.DS_Store`（macOS 系统文件）和 IDE 配置

**涉及技术**：Git 版本控制

---

#### `requirements.txt`
**功能**：声明项目所有 Python 依赖包及其精确版本号。

**核心依赖说明**：
| 依赖包 | 版本 | 用途 |
|--------|------|------|
| `fastapi` | 0.121.2 | Web API 框架 |
| `uvicorn` | 0.38.0 | ASGI 异步服务器 |
| `langchain` | 1.0.7 | LLM 应用框架 |
| `langchain-core` | 1.0.5 | LangChain 核心抽象层 |
| `langchain-openai` | 1.0.3 | OpenAI 兼容的 LLM 客户端（用于调用 DashScope） |
| `langgraph` | 1.0.3 | 多 Agent 工作流编排引擎 |
| `pydantic` | 2.12.4 | 数据验证和序列化 |
| `pydantic-settings` | 2.9.1 | 基于环境变量的配置管理 |
| `tenacity` | 9.1.2 | 重试机制（指数退避） |
| `python-dotenv` | 1.2.1 | 从 `.env` 文件加载环境变量 |
| `requests` | 2.32.5 | HTTP 客户端（前端和数据抓取用） |
| `tiktoken` | 0.12.0 | OpenAI 的 Token 计数器 |
| `openai` | 2.8.1 | OpenAI API 客户端 |
| `httpx` | 0.28.1 | 异步 HTTP 客户端 |

**涉及技术**：pip 包管理、语义化版本控制

---

### `scripts/` 目录 — 数据摄入脚本

---

#### `scripts/ingest_data.py`
**功能**：从 Basketball-Reference 网站抓取 NBA 真实历史比赛数据，转化为向量并写入 ChromaDB，构建 RAG 知识库。

**详细流程**：
1. 使用 `requests` 模拟浏览器请求 Basketball-Reference 网站
2. 用 `pandas.read_html()` 解析 HTML 表格提取比赛数据
3. 将每场比赛数据转换为结构化文本（日期、对阵、比分、胜负）
4. 封装为 LangChain `Document` 对象（包含 `page_content` 和 `metadata`）
5. 通过 DashScope Embeddings 向量化后存入 ChromaDB
6. 分批写入（batch_size=50）防止内存溢出

**涉及技术**：
- `requests` — HTTP 请求（带 User-Agent 伪装绕过反爬）
- `pandas` — HTML 表格解析（`pd.read_html()`）
- `LangChain Document` — 文档抽象（page_content + metadata）
- `ChromaDB` — 向量数据库持久化存储
- `DashScope Embeddings` — 阿里云文本向量化 API
- `time.sleep()` — 请求间隔（避免触发网站反爬限制）

---

### `app/main.py` — 应用入口

---

#### `app/main.py`
**功能**：FastAPI 应用的主入口文件，负责应用初始化、中间件配置、路由注册。

**详细说明**：
1. 调用 `init_db()` 初始化数据库（创建表结构）
2. 创建 FastAPI 实例，配置应用元信息（标题、描述、版本号）
3. 添加 **CORS 中间件**，允许 Streamlit 前端跨域访问后端 API
4. 注册 API 路由到 `/api/v1` 前缀下
5. 根路由 `/` 返回系统信息和所有可用端点列表
6. 支持通过 `python -m app.main` 直接启动服务

**涉及技术**：
- `FastAPI` — Web 框架，自动生成 OpenAPI 文档
- `CORSMiddleware` — 跨域资源共享中间件
- `Uvicorn` — ASGI 异步服务器
- 结构化日志（`get_logger`）

---

### `app/frontend_ui.py` — 前端界面

---

#### `app/frontend_ui.py`
**功能**：基于 Streamlit 构建的交互式前端界面，包含项目介绍、架构图、技术说明和实时预测演示。

**详细说明**：
1. **页面配置**：设置页面标题、宽布局、自定义 CSS 样式
2. **侧边栏导航**：项目路线图目录，可快速跳转到各章节
3. **项目介绍**：解释为什么传统机器学习模型在体育预测上的局限性
4. **架构图**：使用 **Mermaid** 语法渲染系统架构流程图
5. **技术深度讲解**：6 个 Agent 各自的工作原理和代码片段
6. **实时演示**：
   - 从 **ESPN API** 获取当日 NBA 赛程
   - 用户选择比赛后点击预测
   - 调用后端 API 执行预测
   - 展示预测结果（赢家、胜率、比分预测、关键因素等）
7. **后端基础设施说明**：数据库设计和反馈循环

**涉及技术**：
- `Streamlit` — Python 前端框架（`st.columns`, `st.metric`, `st.status` 等组件）
- `streamlit-mermaid` — Mermaid 图表渲染组件
- `requests` — 调用后端 API 和 ESPN API
- `st.cache_data` — Streamlit 数据缓存（TTL=3600s）
- ESPN API — `site.api.espn.com` 获取 NBA 赛程
- CSS — 自定义页面样式
- Mermaid — 架构流程图描述语言

---

### `app/core/` 目录 — 核心基础设施

---

#### `app/core/config.py`
**功能**：集中管理全局配置，使用 Pydantic BaseSettings 从环境变量和 `.env` 文件加载配置。

**详细说明**：
1. 定义 `Settings` 类，继承 `BaseSettings`，所有配置项支持环境变量覆盖
2. **LLM 配置**：API Key、模型名称、温度参数、Base URL
3. **Agent 配置**：超时时间（默认 60s）、最大重试次数（默认 2 次）
4. **搜索配置**：Tavily 搜索最大结果数
5. **RAG 配置**：检索数量（top_k）、重排序保留数量（rerank_top_n）
6. **缓存配置**：预测缓存 TTL、搜索缓存 TTL
7. **数据库配置**：SQLite 连接 URL
8. **日志配置**：日志级别
9. 初始化日志系统和 LLM 实例

**涉及技术**：
- `Pydantic BaseSettings` — 类型安全的配置管理，支持环境变量自动绑定
- `python-dotenv` — `.env` 文件加载
- `ChatOpenAI` — LangChain 的 OpenAI 兼容 LLM 客户端（此处用于调用 DashScope API）
- 十二因子应用（12-Factor App）配置原则

---

#### `app/core/logger.py`
**功能**：提供结构化日志系统，替代所有 `print()` 语句，支持 Agent 执行计时。

**详细说明**：
1. `setup_logging()` — 初始化日志系统，设置统一格式（时间 | 级别 | 模块 | 消息），抑制第三方库的噪音日志
2. `get_logger(name)` — 获取命名空间化的 Logger（如 `nba.agent.recent_analyst`）
3. `log_execution_time()` — 上下文管理器，自动记录操作的开始、完成和耗时
4. `log_agent(agent_name)` — 装饰器，自动为 Agent 节点函数添加日志和计时功能，记录比赛对阵信息

**涉及技术**：
- `logging` — Python 标准库日志模块
- Context Manager（`@contextmanager`） — 上下文管理器模式
- Decorator（装饰器） — 用 `@wraps` 保留原函数元信息
- `asyncio.iscoroutinefunction` — 支持同步/异步函数的自动检测

---

#### `app/core/cache.py`
**功能**：线程安全的 TTL（Time-To-Live）内存缓存，避免对相同比赛重复调用 LLM 和搜索 API。

**详细说明**：
1. `TTLCache` 类 — 基于字典的缓存实现，每个条目有独立的过期时间
2. `_make_key()` — 使用 MD5 哈希生成确定性的缓存键
3. `get()` — 获取缓存值，自动清除过期条目
4. `set()` — 存储值并设置 TTL
5. `cleanup_expired()` — 批量清理过期缓存
6. 两个全局缓存实例：
   - `prediction_cache`（TTL=600s）— 缓存完整预测结果
   - `search_cache`（TTL=300s）— 缓存网络搜索结果

**涉及技术**：
- `threading.Lock` — 线程锁，保证并发安全
- `hashlib.md5` — 哈希算法生成缓存键
- TTL 缓存模式 — 基于时间的缓存失效策略
- 单例模式 — 全局缓存实例

---

### `app/graph/` 目录 — LangGraph 工作流

---

#### `app/graph/workflow.py`
**功能**：定义 LangGraph 多 Agent 工作流，实现 Fan-out/Fan-in（扇出/扇入）执行模式，并添加优雅降级包装。

**详细说明**：
1. `with_graceful_degradation()` — 核心封装函数，为每个 Agent 添加：
   - **超时控制**：使用 `ThreadPoolExecutor` 实现超时，超过配置时间自动跳过
   - **异常捕获**：Agent 崩溃时返回降级消息，不影响其他 Agent
   - **状态记录**：在 `agent_status` 中记录每个 Agent 的执行结果（success/timeout/failed）
2. 5 个分析 Agent 用降级包装器包装
3. 构建 `StateGraph`：
   - `START → 5 个 Agent`（并行扇出）
   - `5 个 Agent → final_predictor`（扇入汇聚）
   - `final_predictor → END`
4. `workflow.compile()` — 编译为可执行的工作流图

**涉及技术**：
- `LangGraph StateGraph` — 基于状态的有向图工作流引擎
- `concurrent.futures.ThreadPoolExecutor` — 线程池 + 超时控制
- Fan-out/Fan-in 并行模式 — 5 个 Agent 并行执行后汇聚
- 优雅降级（Graceful Degradation） — 部分失败不影响整体
- 装饰器模式 + `@wraps` — 保留原函数签名

---

#### `app/graph/nodes/state.py`
**功能**：定义 LangGraph 工作流的共享状态结构（AgentState）。

**详细说明**：
- 使用 `TypedDict` 定义状态字典的类型约束
- **输入字段**：`team_home`（主队）、`team_away`（客队）
- **Agent 输出字段**：5 个 `Optional[str]` 字段存储各 Agent 的分析报告（Optional 支持优雅降级）
- **最终输出**：`final_prediction` 存储最终预测结果
- **元数据**：`agent_status` 字典跟踪每个 Agent 的执行状态

**涉及技术**：
- `TypedDict` — Python 类型化字典（LangGraph 状态管理要求）
- `Optional` — 类型标注，支持 None 值（Agent 失败时）

---

#### `app/graph/nodes/models.py`
**功能**：定义所有 6 个 Agent 的结构化输出 Pydantic 模型，确保 LLM 返回格式统一可解析。

**详细说明**：
| 模型名 | 对应 Agent | 关键字段 |
|--------|-----------|---------|
| `RecentAnalysis` | Agent 1 | 主客场动量、胜率、场均得分、优势方 |
| `HistoryAnalysis` | Agent 2 | 历史战绩、风格匹配、关键因素、战术趋势 |
| `NewsAnalysis` | Agent 3 | 主客场伤病列表、重大新闻、伤病影响方向 |
| `OddsAnalysis` | Agent 4 | 热门/冷门、盘口、公众投注趋势、市场信心 |
| `StrategyAnalysis` | Agent 5 | 关键对位、主客场优势、替补深度 |
| `GamePrediction` | Agent 6 | 赢家、胜率、比分预测、信心等级、关键因素、风险预警、Agent 共识度 |

**涉及技术**：
- `Pydantic BaseModel` — 数据验证和序列化
- `Field(description=...)` — 字段描述，作为 LLM 的输出指令
- `with_structured_output()` — LangChain 的结构化输出功能，强制 LLM 按 Schema 返回 JSON

---

#### `app/graph/nodes/recent_analyst.py`
**功能**：**Agent 1 — 近期表现分析师**。分析两队最近 5 场比赛的状态和势头。

**执行流程**：
1. 通过 `nba_client.get_recent_games_stats()` 搜索两队近期数据（带缓存和重试）
2. 使用 `RECENT_ANALYST_PROMPT` 模板构建提示词
3. 调用 `llm.with_structured_output(RecentAnalysis)` 获取结构化输出
4. 如果结构化输出失败，自动回退到非结构化 LLM 调用
5. 返回分析结果和 Agent 执行状态

**涉及技术**：
- `@log_agent` 装饰器 — 自动记录执行时间和日志
- Tavily Search — 通过 `nba_client` 搜索实时 NBA 数据
- LLM Structured Output — 强制 LLM 返回 `RecentAnalysis` 格式
- Fallback 模式 — 结构化失败时降级为自由文本

---

#### `app/graph/nodes/history_analyst.py`
**功能**：**Agent 2 — 历史对战分析师**。使用增强 RAG 管道从向量数据库检索历史对战数据。

**执行流程**：
1. 构建检索查询（包含两队名称和关键词）
2. 调用增强 RAG 管道 `query_knowledge_base(query, k=3, llm=llm)`：
   - 查询改写（Query Rewriting）
   - 多查询检索（Multi-query Retrieval）
   - 文档去重（Deduplication）
   - LLM 重排序（Reranking）
3. 将检索到的历史数据注入 `HISTORY_ANALYST_PROMPT`
4. 生成结构化的战术分析报告

**涉及技术**：
- **RAG（检索增强生成）** — 用真实数据增强 LLM 输出，减少幻觉
- **ChromaDB 向量检索** — 语义相似度搜索
- **两阶段检索** — 先广泛检索再精准重排序
- Query Rewriting — LLM 改写查询提升召回率
- LLM Reranking — LLM 对检索结果重新排序提升精度

---

#### `app/graph/nodes/team_reporter.py`
**功能**：**Agent 3 — 球队记者**。自主决定是否搜索网络，使用 ReAct 模式（Reason + Act）。

**执行流程**：
1. 使用 `llm.bind_tools([search_tool])` 绑定搜索工具
2. **Phase 1（Reason）**：LLM 分析是否需要搜索
3. **Phase 2（Act）**：如果 LLM 产生了 `tool_calls`，执行搜索工具并返回结果
4. **Phase 3（Observe）**：LLM 综合搜索结果生成报告
5. **Phase 4（Structure）**：将报告转换为 `NewsAnalysis` 结构化格式

**涉及技术**：
- **ReAct 模式** — Reason + Act 循环（Agent 自主决策是否使用工具）
- **Tool Calling** — LLM 生成函数调用请求，系统执行后返回结果
- `llm.bind_tools()` — LangChain 的工具绑定 API
- `ToolMessage` — LangChain 的工具返回消息格式
- 自主 Agent — 与其他 Agent 不同，Agent 3 **自己决定**是否搜索

---

#### `app/graph/nodes/odds_analyst.py`
**功能**：**Agent 4 — 赔率分析师**。分析博彩市场的赔率和资金流向。

**执行流程**：
1. 通过 `search_web()` 搜索赔率数据（带缓存和重试）
2. 使用 `ODDS_ANALYST_PROMPT` 分析热门/冷门、盘口含义、公众投注趋势
3. 输出 `OddsAnalysis` 结构化报告

**涉及技术**：
- Tavily Search — 搜索实时赔率数据
- LLM Structured Output — `OddsAnalysis` 模型
- 搜索缓存 — 相同搜索复用缓存结果

---

#### `app/graph/nodes/strategy_analyst.py`
**功能**：**Agent 5 — 战术教练**。分析首发阵容、关键对位和替补深度。

**执行流程**：
1. 搜索首发阵容和对位信息
2. 分析关键球员对位、阵容弱点、替补深度
3. 输出 `StrategyAnalysis` 结构化报告

**涉及技术**：
- Tavily Search — 搜索阵容数据
- LLM Structured Output — `StrategyAnalysis` 模型
- 缓存搜索 — 避免重复搜索

---

#### `app/graph/nodes/final_predictor.py`
**功能**：**Agent 6 — 最终决策者**。综合 5 份专家报告，做出最终预测。

**执行流程**：
1. `_safe_get()` 安全提取各 Agent 报告（缺失时返回提示信息）
2. 统计 Agent 健康状况（多少个成功/失败/超时）
3. 使用 `FINAL_PREDICTOR_PROMPT` 综合分析，遵循决策优先级：
   - 伤病新闻 > 赔率 > 近期表现 > 战术 > 历史
4. 输出 `GamePrediction` 结构化预测（赢家、胜率、比分、信心、关键因素、风险预警）
5. 双层 Fallback：结构化失败 → 自由文本 → 错误兜底

**涉及技术**：
- LLM Structured Output — `GamePrediction` 模型（最核心的输出）
- 优雅降级 — 三级 Fallback 机制
- Agent 共识分析 — 统计 5 个 Agent 中多少个支持同一结论
- `model_dump_json()` — Pydantic V2 的 JSON 序列化

---

### `app/tools/` 目录 — 外部工具封装

---

#### `app/tools/nba_client.py`
**功能**：NBA 数据客户端，封装 Tavily 搜索 + 缓存 + 自动重试。

**详细说明**：
1. `_search_with_retry()` — 核心搜索函数，使用 Tenacity 装饰器实现：
   - 最大重试次数：`settings.agent_max_retries + 1`
   - 重试等待：指数退避（2s → 4s → 8s → 10s 上限）
   - 重试前日志记录
2. `get_recent_games_stats()` — 获取球队近期比赛数据
   - 先检查 `search_cache` 是否有缓存
   - 缓存未命中时执行搜索并缓存结果
3. `search_web()` — 通用搜索接口，供 Agent 4、5 使用

**涉及技术**：
- `Tenacity` — 声明式重试装饰器（`@retry`）
- 指数退避（Exponential Backoff） — `wait_exponential(multiplier=1, min=2, max=10)`
- TTL 缓存 — 搜索结果缓存 5 分钟
- `TavilySearchResults` — AI 原生搜索工具

---

#### `app/tools/retriever.py`
**功能**：增强 RAG 检索管道，实现两阶段检索（Retrieve → Rerank）。

**详细说明**：
1. `get_vector_store()` — 初始化 ChromaDB 向量数据库连接
2. `rewrite_query()` — **查询改写**：
   - 用 LLM 将原始查询改写为 2 个优化查询
   - 加上原始查询共 3 个查询，从不同角度检索
3. `deduplicate_docs()` — **文档去重**：
   - 基于 `page_content` 哈希去除重复文档
4. `rerank_documents()` — **LLM 重排序**：
   - 将检索到的文档交给 LLM 按相关性排序
   - 解析 LLM 返回的排序结果（如 "3,1,4,2,5"）
   - 保留 Top-N 最相关文档
5. `query_knowledge_base()` — **完整 RAG 管道**：
   ```
   Query Rewriting → Multi-query Retrieval → Deduplication → LLM Reranking → Format Output
   ```

**涉及技术**：
- **RAG（Retrieval-Augmented Generation）** — 检索增强生成
- **ChromaDB** — 向量数据库（`similarity_search`）
- **DashScope Embeddings** — 阿里云文本向量化
- **Query Rewriting** — 查询改写提升召回率
- **LLM Reranking** — 两阶段检索（粗排 + 精排）
- **Multi-query Retrieval** — 多查询检索扩大召回范围

---

### `app/prompts/` 目录 — Prompt 模板管理

---

#### `app/prompts/templates.py`
**功能**：集中管理所有 Agent 的 Prompt 模板，将提示词与业务逻辑分离。

**包含模板**：
| 模板名 | 用途 |
|--------|------|
| `RECENT_ANALYST_PROMPT` | Agent 1 的近期表现分析提示词 |
| `HISTORY_ANALYST_PROMPT` | Agent 2 的历史对战分析提示词 |
| `TEAM_REPORTER_PROMPT` | Agent 3 的新闻调查提示词 |
| `ODDS_ANALYST_PROMPT` | Agent 4 的赔率分析提示词 |
| `STRATEGY_ANALYST_PROMPT` | Agent 5 的战术分析提示词 |
| `FINAL_PREDICTOR_PROMPT` | Agent 6 的最终决策提示词（含决策优先级规则） |
| `QUERY_REWRITE_PROMPT` | RAG 查询改写提示词 |
| `RERANK_PROMPT` | RAG 文档重排序提示词 |

**设计优势**：
- Prompt 版本管理（修改 Prompt 不需要改业务代码）
- 方便 A/B 测试不同 Prompt 效果
- 使用 Python f-string `{变量名}` 占位符

**涉及技术**：
- Prompt Engineering — 精心设计的角色设定和输出约束
- 模板方法模式 — 统一 Prompt 结构，变量通过 `.format()` 注入
- 关注点分离（Separation of Concerns）

---

### `app/api/` 目录 — API 路由层

---

#### `app/api/deps.py`
**功能**：FastAPI 依赖注入模块，提供数据库会话依赖。

**涉及技术**：
- FastAPI `Depends` — 依赖注入模式

---

#### `app/api/routes.py`
**功能**：定义所有 RESTful API 端点，是前后端交互的核心接口层。

**API 端点详细说明**：

| 方法 | 路径 | 功能 | 说明 |
|------|------|------|------|
| `POST` | `/predict` | 运行预测 | 检查缓存 → 执行多 Agent 工作流 → 存储结果 → 返回预测 |
| `GET` | `/predictions` | 预测历史 | 分页查询 + 按球队名筛选 |
| `GET` | `/predictions/{id}` | 预测详情 | 返回所有 Agent 报告 + 执行元数据 + 评估结果 |
| `POST` | `/evaluate/{id}` | 评估预测 | 比赛结束后回填实际结果，自动判断预测是否正确 |
| `GET` | `/stats` | 准确率统计 | 总预测数、已评估数、正确数、准确率、平均耗时 |
| `GET` | `/health` | 健康检查 | 服务状态 + 缓存大小 |

**`/predict` 端点核心流程**：
1. 检查 `prediction_cache` 是否有相同比赛的近期预测
2. 调用 `app_workflow.invoke(initial_state)` 执行整个 LangGraph 工作流
3. 记录执行时间
4. 解析最终预测 JSON
5. 存入 SQLite 数据库（包含执行元数据）
6. 缓存结果
7. 返回包含 `prediction_details` 和 `agent_status` 的响应

**`/evaluate` 端点**：
- 实现**评估闭环（Feedback Loop）**
- 将预测的赢家与实际赢家对比
- 防止重复评估
- 支持后续准确率追踪

**涉及技术**：
- `FastAPI APIRouter` — 路由模块化
- `Depends(get_db)` — 依赖注入管理数据库会话生命周期
- `Pydantic BaseModel` — 请求体验证（`MatchRequest`, `EvaluationRequest`）
- `Query()` — 查询参数验证（分页、筛选）
- `SQLAlchemy func` — 数据库聚合查询（`func.count`, `func.avg`）
- `desc()` — 按时间降序排列
- 缓存策略 — 缓存命中时跳过整个工作流
- JSON 安全解析 — `_safe_json_parse()` 防止解析异常

---

### `app/db/` 目录 — 数据库层

---

#### `app/db/models.py`
**功能**：定义 SQLAlchemy ORM 模型，映射数据库表结构。

**`PredictionRecord` 表字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer PK | 主键，自增 |
| `created_at` | DateTime | 创建时间（自动填充） |
| `team_home` | String（索引） | 主队名称 |
| `team_away` | String（索引） | 客队名称 |
| `recent_analysis` | Text | Agent 1 分析报告 |
| `history_analysis` | Text | Agent 2 分析报告 |
| `news_analysis` | Text | Agent 3 分析报告 |
| `odds_analysis` | Text | Agent 4 分析报告 |
| `strategy_analysis` | Text | Agent 5 分析报告 |
| `final_result` | Text | Agent 6 最终预测 JSON |
| `execution_time_seconds` | Float | 整体执行耗时 |
| `agent_status` | JSON | 各 Agent 执行状态 |
| `is_correct` | Boolean | 预测是否正确（评估后填充） |
| `actual_winner` | String | 实际赢家（评估后填充） |
| `actual_score` | String | 实际比分（评估后填充） |
| `evaluated_at` | DateTime | 评估时间 |

**涉及技术**：
- `SQLAlchemy ORM` — 对象关系映射
- `declarative_base()` — SQLAlchemy 声明式基类
- `Column` 类型系统 — `String`, `Text`, `Integer`, `Float`, `Boolean`, `DateTime`, `JSON`
- 索引（`index=True`） — 加速按球队名和时间的查询

---

#### `app/db/session.py`
**功能**：数据库会话管理，提供连接池和安全的会话生命周期管理。

**详细说明**：
1. `engine` — SQLAlchemy 引擎，配置：
   - `check_same_thread=False`（SQLite 多线程支持）
   - `pool_pre_ping=True`（使用前验证连接有效性）
2. `SessionLocal` — 会话工厂
3. `init_db()` — 创建所有数据库表
4. `get_db_context()` — 上下文管理器，用于脚本等非 FastAPI 场景
   - 自动 commit/rollback/close
5. `get_db()` — FastAPI 依赖注入专用的 generator
   - 配合 `Depends()` 使用，请求结束后自动关闭连接

**涉及技术**：
- `SQLAlchemy create_engine` — 数据库连接池
- `sessionmaker` — 会话工厂模式
- `contextmanager` — 上下文管理器（`with` 语句安全管理资源）
- Generator 依赖注入 — FastAPI 的 `yield` 模式
- 连接池预检（`pool_pre_ping`） — 防止使用已断开的连接

---

### `app/utils/` 目录

---

#### `app/utils/helpers.py`
**功能**：通用辅助函数（当前为空文件，预留扩展位）。

---

## 四、系统架构流程图

```
用户请求（Streamlit / curl）
        │
        ▼
   ┌─────────────┐
   │  FastAPI API │  POST /api/v1/predict
   │  (routes.py) │
   └──────┬──────┘
          │ 检查缓存 → 命中则直接返回
          ▼
   ┌─────────────────────────────────┐
   │     LangGraph Workflow          │
   │     (workflow.py)               │
   │                                 │
   │  ┌──── Fan-out (并行) ────┐    │
   │  │                        │    │
   │  │  Agent 1: 近期表现      │    │  ← Tavily Search + 缓存 + 重试
   │  │  Agent 2: 历史对战      │    │  ← ChromaDB RAG (改写+重排序)
   │  │  Agent 3: 新闻伤病      │    │  ← ReAct Tool Calling
   │  │  Agent 4: 赔率市场      │    │  ← Tavily Search + 缓存 + 重试
   │  │  Agent 5: 战术对位      │    │  ← Tavily Search + 缓存 + 重试
   │  │                        │    │
   │  └──── Fan-in (汇聚) ─────┘    │
   │           │                     │
   │           ▼                     │
   │  Agent 6: 最终决策              │  ← 综合 5 份报告 + 结构化输出
   │  (GamePrediction JSON)          │
   └──────────┬──────────────────────┘
              │
              ▼
   ┌─────────────────┐
   │  SQLite 数据库    │  存储预测记录 + 执行元数据
   │  (models.py)     │
   └──────┬──────────┘
          │
          ▼
     返回预测结果 JSON
```

---

## 五、关键技术亮点总结

| 技术亮点 | 文件位置 | 面试关键词 |
|---------|---------|-----------|
| 多 Agent 并行协作 | `workflow.py` | LangGraph, Fan-out/Fan-in, StateGraph |
| 优雅降级 + 超时控制 | `workflow.py` | Graceful Degradation, ThreadPoolExecutor |
| RAG 两阶段检索 | `retriever.py` | Query Rewriting, LLM Reranking |
| ReAct 自主 Agent | `team_reporter.py` | Tool Calling, Reason + Act |
| 全 Agent 结构化输出 | `models.py` + 各 Agent | Pydantic, with_structured_output |
| 搜索重试 + 指数退避 | `nba_client.py` | Tenacity, Exponential Backoff |
| TTL 内存缓存 | `cache.py` | 线程安全, TTL 缓存, 性能优化 |
| 评估闭环 | `routes.py` | Feedback Loop, 准确率追踪 |
| 配置管理 | `config.py` | Pydantic BaseSettings, 12-Factor App |
| 结构化日志 | `logger.py` | logging, 装饰器, 执行计时 |
| 依赖注入 | `deps.py` + `routes.py` | FastAPI Depends, 数据库会话管理 |
| Prompt 模板分离 | `templates.py` | 关注点分离, Prompt 版本管理 |
