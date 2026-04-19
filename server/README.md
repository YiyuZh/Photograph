# 智摄首版云端轻服务

智摄首版是一个适配低配置云服务器的单用户工作流系统，主链路为：

`上传分析包 -> 生成 Prompt -> 手动 AI 深分析 -> 回填结果 -> 生成报告 -> 保存历史`

生产部署请看根目录的《本地预览与云服务器部署手册_智摄.md》。

## 目录说明

```text
server/
  app/                FastAPI 应用
  knowledge/          静态知识库与 Prompt 模板
  logs/               运行日志
  migrations/         迁移占位目录
  sample_data/        最小示例分析包
  storage/            SQLite、任务文件、报告导出
  tests/              基础测试
```

## 本地安装

1. 创建虚拟环境并安装依赖

```bash
cd D:/apps/Photography/server
python -m venv .venv
.venv/Scripts/activate
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

2. 配置环境变量

```bash
copy .env.example .env
```

建议至少修改：

- `SECRET_KEY`
- `DEFAULT_PASSWORD`
- `APP_BASE_URL`
- `PIP_INDEX_URL`（默认已写成清华 PyPI，可按需覆盖）

3. 启动开发环境

```bash
uvicorn app.main:app --reload
```

访问：

- 登录页：`http://127.0.0.1:8000/login`
- 健康检查：`http://127.0.0.1:8000/api/health`

默认账号来自 `.env`：

- 用户名：`DEFAULT_USERNAME`
- 密码：`DEFAULT_PASSWORD`

## Docker 启动

1. 复制环境变量

```bash
cp .env.example .env
```

`.env.example` 已经把 Docker build 默认源设成清华 PyPI：

- `PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple`
- `PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn`
- `PIP_DEFAULT_TIMEOUT=120`
- `PIP_RETRIES=8`
- `SHARED_CADDY_NETWORK=shared_gateway`

2. 启动

```bash
docker compose up -d --build
docker compose ps
```

默认预览端口：

- `http://127.0.0.1:18120`

如果你要接入现有 `hiremate-caddy` 统一公网网关，智摄容器必须同时加入 `shared_gateway`，这样 Caddy 才能通过 `photography-app:8000` 访问它。

## 数据库初始化

首版启动时自动执行：

- 创建 SQLite 表
- 写入默认管理员
- 写入默认设置
- 导入静态知识库
- 导入默认 Prompt 模板

SQLite 默认位置：

- `storage/sqlite/photography.db`

## 知识库导入

知识库静态文件位置：

- `knowledge/items.json`
- `knowledge/prompt_templates.json`
- `knowledge/**/*.md`

修改这两个文件后，重启服务即可同步更新到数据库。

## 示例分析包

最小示例目录：

- `sample_data/minimal_analysis_package/`

最小示例 zip：

- `sample_data/minimal_analysis_package.zip`

可直接在“新建任务”页面上传这个 zip 做完整链路验证。

## 一条完整流程

1. 登录系统
2. 打开“新建任务”
3. 选择任务类型并上传 `sample_data/minimal_analysis_package.zip`
4. 进入任务详情页确认分析包摘要与 segments
5. 进入 Prompt 页面点击“生成 Prompt”
6. 到回填页粘贴 AI 输出，或上传 `.txt` / `.md`
7. 到报告页点击“生成报告”
8. 返回任务列表确认历史记录保留

## 基础测试

```bash
pytest
```

测试覆盖：

- 登录
- 创建任务
- 上传分析包
- 生成 Prompt
- 提交结果
- 生成报告

## 生产部署建议

- 服务器目录建议：`/opt/apps/photography`
- 预览端口建议：`127.0.0.1:18120`
- 统一网关网络建议：`shared_gateway`
- SQLite 与 `storage/` 应做宿主机持久化挂载
- 正式公网入口建议通过统一 Caddy 网关转发
