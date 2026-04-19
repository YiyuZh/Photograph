# 给 Codex 的第一版开发 Prompt

你现在是该项目的开发代理。请基于当前项目文档与以下要求，完成 **智摄** 首版项目的初始化开发工作。

你的目标不是做一个重型视频云处理平台，而是实现一个 **适配 2 核 2 GB 云服务器、单用户、Docker 部署、以“本地预处理 + 云端轻服务 + 手动 AI 深分析 + 结果回填归档”为核心工作流** 的可运行版本。

请先完整阅读项目中的相关文档，再开始实现。你必须先理解整体目标、边界和约束，再动手写代码。

---

## 一、必须先理解的项目定位

项目名：**智摄**

这是一个面向个人使用的视频 AI 分析工作流系统，不是重型视频分析平台。

核心工作流是：

1. 用户在本地对原视频进行预处理，生成分析包
2. 云端服务接收分析包并解析摘要
3. 云端生成标准 Prompt
4. 用户手动把 Prompt 和素材提交给 ChatGPT / DeepSeek
5. 用户把模型输出结果回填到项目
6. 项目生成结构化报告并保存历史记录

系统重点不在于自动处理原视频，而在于：
- 组织分析流程
- 生成高质量 Prompt
- 归档分析结果
- 沉淀个人知识库

---

## 二、你必须遵守的硬约束

### 1. 服务器约束
云服务器配置只有：
- 2 核 CPU
- 2 GB RAM

因此你**不能**设计或默认引入以下重型方案：
- Redis
- Celery
- PostgreSQL
- MinIO
- 向量数据库
- 重型前后端分离架构
- 云端视频抽帧 / 云端镜头切分 / 云端转写
- 原视频上传后在服务器上做重处理

### 2. 首版架构约束
首版必须采用：
- **FastAPI** 作为后端
- **Jinja2** 作为页面模板渲染方案，优先不要上前后端分离
- **SQLite** 作为数据库
- **宿主机挂载目录** 作为文件存储
- **Docker Compose** 部署
- 单用户登录保护

### 3. 功能边界约束
首版必须只围绕这条链路展开：

**上传分析包 → 生成 Prompt → 回填结果 → 生成报告 → 保存历史**

不要超范围去做：
- 自动调用大模型 API
- 视频编辑器
- 多人系统
- 社区功能
- 支付系统
- 原视频云端分析
- 批量任务处理

---

## 三、你要先阅读并对齐的文档

开始编码前，请先在项目中找到并理解这些文档，然后按文档落地：

1. **智摄 PRD V2.0**
2. **本地预处理工具设计文档**
3. **云端轻服务架构设计文档**
4. **数据库表结构草案**
5. **API 接口清单**

如果代码实现和文档发生冲突：
- 优先保证项目定位与资源约束正确
- 保证首版最小可用链路跑通
- 不要为了“看起来更高级”擅自上重架构

---

## 四、你的首版开发任务目标

你需要完成的是：

### 第一阶段：初始化项目骨架
搭建一个可运行的云端轻服务项目，具备：
- FastAPI 应用入口
- Jinja2 模板页面
- SQLite 数据库初始化
- 基础登录保护
- Docker / Docker Compose 配置
- 基础目录结构
- 配置管理
- 日志能力

### 第二阶段：打通首版核心链路
实现以下核心能力：
- 创建任务
- 上传并解析分析包 ZIP
- 展示分析包摘要
- 生成 Prompt
- 回填 AI 结果
- 生成结构化报告
- 保存历史任务并支持查看

### 第三阶段：知识库与模板基础能力
实现：
- 知识库静态加载
- 知识库浏览和搜索
- Prompt 模板读取
- 默认模板配置

---

## 五、你必须产出的项目结构

请创建一个适合首版维护的项目结构。推荐如下：

```text
server/
  app/
    main.py
    config.py
    db.py
    deps.py
    models/
    schemas/
    routers/
    services/
    templates/
    static/
    utils/
  storage/
  logs/
  knowledge/
  migrations/
  tests/
  requirements.txt
  Dockerfile
  docker-compose.yml
  README.md
  .env.example
```

### 模块职责建议
- `main.py`：FastAPI 应用入口
- `config.py`：环境变量与配置管理
- `db.py`：数据库连接与初始化
- `deps.py`：登录态依赖、通用依赖
- `models/`：数据库模型
- `schemas/`：请求响应模型
- `routers/`：接口和页面路由
- `services/`：业务逻辑
- `templates/`：Jinja2 页面模板
- `static/`：基础静态资源
- `utils/`：通用工具
- `knowledge/`：静态知识库文件
- `storage/`：任务数据、Prompt、报告等文件存储根目录

---

## 六、你必须实现的数据库对象

请基于数据库草案实现首版必须表。

首批必须实现：
- `users`
- `tasks`
- `packages`
- `package_files`
- `segments`
- `prompt_templates`
- `prompts`
- `results`
- `reports`
- `knowledge_items`
- `settings`

首版可以暂缓：
- 标签表
- 审计日志表

但请在代码结构上为后续扩展保留空间。

---

## 七、你必须实现的接口

请优先实现以下首批接口：

### 认证
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

### 任务
- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `PATCH /api/tasks/{task_id}`
- `DELETE /api/tasks/{task_id}`

### 分析包
- `POST /api/tasks/{task_id}/package`
- `GET /api/tasks/{task_id}/package`
- `GET /api/tasks/{task_id}/package/files`
- `GET /api/tasks/{task_id}/segments`

### Prompt
- `POST /api/tasks/{task_id}/prompts`
- `GET /api/tasks/{task_id}/prompts/current`
- `GET /api/tasks/{task_id}/prompts`
- `GET /api/prompt-templates`

### 回填结果
- `POST /api/tasks/{task_id}/results`
- `POST /api/tasks/{task_id}/results/upload`
- `GET /api/tasks/{task_id}/results/current`
- `GET /api/tasks/{task_id}/results`

### 报告
- `POST /api/tasks/{task_id}/report`
- `GET /api/tasks/{task_id}/report/current`
- `GET /api/tasks/{task_id}/reports`
- `GET /api/reports/{report_id}`

### 知识库
- `GET /api/knowledge-items`
- `GET /api/knowledge-items/{item_id}`
- `GET /api/knowledge-items/search`

### 设置
- `GET /api/settings`
- `PATCH /api/settings`

### 系统
- `GET /api/health`

---

## 八、你必须实现的页面

请使用 Jinja2 完成首版页面，页面不需要华丽，但必须结构清晰、可用、可联通。

### 1. 登录页
路由：`/login`
功能：
- 用户登录
- 错误提示

### 2. 首页 / 仪表盘
路由：`/`
功能：
- 新建任务入口
- 最近任务
- 当前默认模板摘要
- 知识库数量摘要

### 3. 任务列表页
路由：`/tasks`
功能：
- 查看历史任务
- 按类型、状态筛选
- 进入任务详情

### 4. 新建任务页
路由：`/tasks/new`
功能：
- 选择任务类型
- 填写标题与说明
- 创建任务
- 上传分析包

### 5. 任务详情页
路由：`/tasks/{task_id}`
功能：
- 查看任务基础信息
- 查看分析包摘要
- 查看 segments 摘要
- 跳转生成 Prompt
- 跳转回填结果
- 跳转查看报告

### 6. Prompt 页面
路由：`/tasks/{task_id}/prompt`
功能：
- 展示当前 Prompt
- 展示推荐附带素材说明
- 展示推荐追问
- 展示回填模板
- 提供复制按钮

### 7. 回填页面
路由：`/tasks/{task_id}/fillback`
功能：
- 粘贴 AI 输出结果
- 或上传 TXT / Markdown
- 记录来源模型
- 保存结果

### 8. 报告页面
路由：`/tasks/{task_id}/report`
功能：
- 查看结构化报告
- 显示总体结论
- 显示拆解 / 优化内容
- 导出 Markdown / TXT

### 9. 知识库页面
路由：`/knowledge`
功能：
- 分类浏览
- 搜索
- 查看知识详情

### 10. 设置页面
路由：`/settings`
功能：
- 查看系统设置
- 修改部分可调项
- 查看当前默认模板绑定

---

## 九、分析包处理要求

你必须实现分析包 ZIP 上传与解析逻辑，但要遵守以下规则：

### 支持的最小核心文件
至少识别：
- `task_manifest.json`
- `metadata.json`
- `contact_sheet.jpg` 或至少一张关键帧

### 尽量识别的文件
- `segments.json`
- `transcript.txt`
- `frames/`
- `segment_keyframes/`
- `audio.wav`

### 解析要求
- 解压到任务专属目录
- 校验文件结构
- 将摘要写入数据库
- 将文件索引写入 `package_files`
- 将 segments 写入 `segments`

### 降级要求
- 缺 transcript 可以继续
- 缺 audio 可以继续
- 缺 segments 可以继续，但要有提示
- 缺关键核心文件必须报错并拒绝导入

---

## 十、Prompt 生成要求

Prompt 生成模块必须按模板化思路实现，不允许把 Prompt 拼接写死在路由里。

### 你需要做的事
1. 从任务中读取：
   - 任务类型
   - metadata 摘要
   - segments 摘要
   - transcript 摘要
2. 从知识库中检索：
   - 与任务类型和关键词相关的知识条目
3. 从模板中读取：
   - 默认拆解模板或优化模板
4. 组装生成：
   - Prompt 正文
   - 推荐附带素材清单
   - 推荐追问
   - 回填模板

### 要求
- 支持重复生成新版本 Prompt
- 当前版本要可切换
- 页面要能复制全文

---

## 十一、结果回填与报告生成要求

### 结果回填
你必须实现：
- 粘贴文本提交
- 上传 txt / md 文件提交
- 保存原文到数据库和文件系统（至少一种）
- 记录来源模型

### 报告生成
首版不要做复杂 NLP 解析器。

正确做法是：
- 基于任务类型使用一个结构化报告模板
- 优先保留原始分析内容
- 尽量提取“总体结论”
- 将整理后的结果保存为：
  - `structured_content`
  - Markdown 文件
  - 可选 TXT 文件

### 报告结构
#### 拆解模式报告
- 总体结论
- 风格标签
- 调色推测
- 剪辑结构分析
- 片段拆解
- 疑似 AI 生成片段提示
- 仿拍方案

#### 优化模式报告
- 总体判断
- 必须改
- 建议改
- 可选优化
- 调色建议
- 剪辑建议
- 风格提升建议

---

## 十二、知识库实现要求

首版知识库必须轻量实现。

### 数据来源
- 优先从项目内静态文件加载
- 支持 Markdown / JSON / YAML

### 首版能力
- 启动时加载到数据库或内存索引
- 页面列表浏览
- 关键词搜索
- 按分类筛选

### 不要做
- embedding 服务
- 向量数据库
- 复杂排序系统

---

## 十三、配置与安全要求

### 配置
请通过 `.env` + 配置模块管理以下内容：
- `APP_ENV`
- `APP_HOST`
- `APP_PORT`
- `SECRET_KEY`
- `DEFAULT_USERNAME`
- `DEFAULT_PASSWORD`
- `STORAGE_ROOT`
- `MAX_PACKAGE_UPLOAD_MB`
- `DATABASE_URL`

### 安全要求
- 登录保护必须生效
- 未登录不能访问任务、知识库、设置页面
- 上传文件要校验扩展名和大小
- 解压 ZIP 时要防止路径穿越
- 不要把敏感配置写死在模板或前端中

---

## 十四、Docker 与部署要求

请提供：
- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `README.md`

### 要求
- 一条命令可启动
- SQLite 文件和 storage 目录可通过 volume 挂载持久化
- 日志目录可挂载
- 静态文件与上传文件路径清晰

### 推荐容器
首版尽量只用：
- `app`
- `proxy`（可选，如果你认为首版可直接让 app 暴露，也可先不加）

如果加 `proxy`，优先考虑简单方案。

---

## 十五、测试与验收要求

你需要至少提供：

### 1. 基础自测
- 登录流程正常
- 创建任务正常
- 上传分析包正常
- Prompt 生成正常
- 结果回填正常
- 报告生成正常
- 历史任务可查看

### 2. 至少一组示例数据
请准备一个最小示例分析包目录或测试夹具，供本地开发验证接口链路。

### 3. README 必须说明
- 如何安装依赖
- 如何配置环境变量
- 如何初始化数据库
- 如何启动开发环境
- 如何用 Docker 启动
- 如何导入知识库
- 如何测试一条完整流程

---

## 十六、开发顺序要求

请按以下顺序进行开发，不要乱序堆功能：

### 第 1 步
初始化项目骨架：
- FastAPI
- 配置模块
- 数据库初始化
- 登录页
- 基础模板

### 第 2 步
实现任务主流程：
- 创建任务
- 任务列表
- 任务详情

### 第 3 步
实现分析包上传与解析：
- 上传 ZIP
- 解压校验
- 解析 metadata / segments
- 展示摘要

### 第 4 步
实现 Prompt 模块：
- 模板读取
- Prompt 生成
- 页面展示
- 复制支持

### 第 5 步
实现结果回填与报告：
- 粘贴 / 上传结果
- 保存结果
- 生成报告
- 报告页展示

### 第 6 步
实现知识库与设置：
- 静态知识库导入
- 搜索浏览
- 默认模板设置

### 第 7 步
补充 Docker、README、测试夹具

---

## 十七、代码质量要求

你生成的代码必须：
- 结构清晰
- 命名明确
- 有必要的注释，但不要废话注释
- 路由层保持薄，业务逻辑放到 service 层
- 不把大量逻辑直接堆在模板或单个文件中
- 对文件上传、数据库写入、ZIP 解析做异常处理
- 页面样式保持简洁整齐即可，不追求复杂 UI

请优先追求：
- 稳定
- 可读
- 可维护
- 可跑通

而不是：
- 炫技
- 过度设计
- 提前抽象一堆未来根本用不到的能力

---

## 十八、明确禁止事项

请不要做以下事情：

1. 不要把系统做成前后端分离的大工程
2. 不要引入 Redis / Celery / PostgreSQL / MinIO / Elasticsearch / 向量数据库
3. 不要把原视频上传和云端处理做成首版主路径
4. 不要自动接入大模型 API 作为首版必要功能
5. 不要跳过登录保护
6. 不要把所有逻辑塞进一个文件
7. 不要忽视 README、Docker 和初始化脚本
8. 不要只生成接口不做页面
9. 不要写出和当前资源条件不匹配的架构

---

## 十九、你的最终交付物

你完成第一版开发后，应当至少交付：

1. 可运行的项目代码骨架
2. 可初始化的 SQLite 数据库模型
3. 完整的首版页面和接口
4. 可上传并解析分析包的流程
5. 可生成 Prompt 的流程
6. 可回填结果并生成报告的流程
7. Docker 部署文件
8. `.env.example`
9. README
10. 最小测试夹具 / 示例分析包

---

## 二十、最终验收目标

只有达到以下效果，才算首版开发成功：

1. 我可以登录系统
2. 我可以新建一个拆解或优化任务
3. 我可以上传一个本地预处理生成的分析包 ZIP
4. 我可以看到分析包摘要、关键帧和片段摘要
5. 我可以一键生成 Prompt
6. 我可以把 ChatGPT 的分析结果粘贴回来
7. 我可以生成并查看结构化报告
8. 我可以在历史列表中再次找到这个任务
9. 这一切可以在 2 核 2 GB 服务器的 Docker 环境下稳定运行

---

## 二十一、开始执行前的要求

开始编码前，你应先输出一份简洁的执行计划，说明：
- 你将创建哪些目录和文件
- 你将优先实现哪些模块
- 你会如何分步骤提交

然后再开始逐步实现，不要一上来无计划地同时改所有东西。

---

## 二十二、一句话要求

**请基于“轻量、可跑通、适配低配置服务器”的原则，直接把智摄首版云端轻服务做出来，先把完整主链路打通，不要过度设计。**

