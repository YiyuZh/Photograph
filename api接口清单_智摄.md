# API 接口清单

## 1. 文档定位

本文档用于定义 **智摄项目首版云端轻服务** 的 API 接口清单。

本清单的目标不是覆盖未来所有扩展能力，而是服务于首版最小可用闭环：

**分析包上传 → Prompt 生成 → 手动 AI 深分析 → 结果回填 → 报告查看与归档**

当前接口设计严格基于以下前提：
- 单用户个人使用
- 云服务器 2 核 2 GB
- FastAPI 作为后端框架
- SQLite 作为数据库
- 云端不处理原视频
- 云端主要处理分析包、文本、图片、报告和知识库
- 服务部署目录固定为 `/opt/apps/photography`
- 先通过 `127.0.0.1` 预览端口验证，再接入统一公网网关
- 正式公网入口由 `/opt/apps/hiremate/Caddyfile` 中的统一 Caddy 路由承接

---

## 2. 接口设计原则

### 2.1 设计目标

首版 API 需要满足：
- 结构清晰
- 路径稳定
- 与页面流程一致
- 便于后续扩展
- 不引入过度复杂的 REST 设计

### 2.2 返回格式约定

首版建议统一返回 JSON，基本格式如下：

```json
{
  "success": true,
  "message": "ok",
  "data": {}
}
```

错误返回建议：

```json
{
  "success": false,
  "message": "error message",
  "error_code": "SOME_ERROR",
  "data": null
}
```

### 2.3 时间字段约定

所有时间字段统一使用 ISO 8601 字符串，例如：

```text
2026-04-18T12:34:56+08:00
```

### 2.4 认证约定

首版建议采用基于 Session / Cookie 的登录态。

因此：
- 页面访问接口走 Cookie 鉴权
- JSON API 也默认依赖登录态
- 暂不设计复杂 OAuth / 多端 Token 体系
- 正式公网环境下 Cookie 需开启 `HttpOnly`、`Secure`、`SameSite=Lax`

### 2.5 生产部署访问约定

- 预览访问建议：`http://127.0.0.1:18120`
- 正式访问建议：`https://<PHOTOGRAPHY_DOMAIN>`
- 首版不单独拆独立公网 API 域名，统一走同域 `/api/*`
- 上传、导出与静态文件访问需与网关规则保持一致，至少覆盖 `/api/*`、`/uploads/*`、`/exports/*`
- 如域名、备案或 HTTPS 尚未准备完成，可先停留在本机预览阶段，不直接开放公网

---

## 3. 接口分组总览

首版接口建议分成以下几组：

1. 认证接口
2. 任务接口
3. 分析包接口
4. Prompt 接口
5. 回填结果接口
6. 报告接口
7. 知识库接口
8. 设置接口
9. 文件与导出接口
10. 健康检查接口

---

## 4. 认证接口

## 4.1 登录

### 接口
`POST /api/auth/login`

### 用途
提交用户名和密码，建立登录会话。

### 请求体

```json
{
  "username": "admin",
  "password": "your_password"
}
```

### 成功响应

```json
{
  "success": true,
  "message": "login success",
  "data": {
    "username": "admin",
    "display_name": "Zenithy"
  }
}
```

### 失败响应
- 用户名错误
- 密码错误
- 账户被禁用

---

## 4.2 登出

### 接口
`POST /api/auth/logout`

### 用途
清除当前登录会话。

### 成功响应

```json
{
  "success": true,
  "message": "logout success",
  "data": null
}
```

---

## 4.3 获取当前登录用户

### 接口
`GET /api/auth/me`

### 用途
获取当前登录用户基础信息，用于页面初始化。

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "id": 1,
    "username": "admin",
    "display_name": "Zenithy",
    "last_login_at": "2026-04-18T12:34:56+08:00"
  }
}
```

---

## 5. 任务接口

## 5.1 创建任务

### 接口
`POST /api/tasks`

### 用途
创建一个新任务，用于后续上传分析包、生成 Prompt、回填结果。

### 请求体

```json
{
  "task_type": "reference",
  "title": "沈阳旅行视频拆解",
  "description": "分析镜头结构和调色方向"
}
```

### 字段说明
- `task_type`：必填，`reference` 或 `improve`
- `title`：可选
- `description`：可选

### 成功响应

```json
{
  "success": true,
  "message": "task created",
  "data": {
    "id": 1,
    "task_uuid": "xxxx-xxxx",
    "task_type": "reference",
    "status": "created"
  }
}
```

---

## 5.2 获取任务列表

### 接口
`GET /api/tasks`

### 用途
获取任务列表，支持分页、筛选和搜索。

### 查询参数
- `task_type`：可选，`reference` / `improve`
- `status`：可选
- `keyword`：可选，按标题或视频名搜索
- `page`：可选，默认 1
- `page_size`：可选，默认 20

### 示例
`GET /api/tasks?task_type=reference&status=report_ready&page=1&page_size=20`

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 1,
        "task_uuid": "xxxx-xxxx",
        "task_type": "reference",
        "title": "沈阳旅行视频拆解",
        "status": "report_ready",
        "source_video_name": "demo.mp4",
        "created_at": "2026-04-18T12:34:56+08:00"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 1
    }
  }
}
```

---

## 5.3 获取任务详情

### 接口
`GET /api/tasks/{task_id}`

### 用途
获取单个任务的完整详情，包括当前分析包、Prompt、回填结果、报告摘要。

### 响应结构建议

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "id": 1,
    "task_uuid": "xxxx-xxxx",
    "task_type": "reference",
    "title": "沈阳旅行视频拆解",
    "description": "分析镜头结构和调色方向",
    "status": "prompt_generated",
    "source_video_name": "demo.mp4",
    "package": {
      "id": 3,
      "video_name": "demo.mp4",
      "duration_sec": 28.5,
      "resolution": "1920x1080",
      "fps": 60.0,
      "frame_count": 18,
      "segment_count": 7
    },
    "current_prompt": {
      "id": 5,
      "prompt_type": "reference",
      "created_at": "2026-04-18T12:50:00+08:00"
    },
    "current_result": null,
    "current_report": null,
    "created_at": "2026-04-18T12:34:56+08:00",
    "updated_at": "2026-04-18T12:50:00+08:00"
  }
}
```

---

## 5.4 更新任务基础信息

### 接口
`PATCH /api/tasks/{task_id}`

### 用途
更新任务标题、描述等基础信息。

### 请求体

```json
{
  "title": "城市夜景视频拆解",
  "description": "重点分析风格、调色和AI生成镜头"
}
```

---

## 5.5 删除任务

### 接口
`DELETE /api/tasks/{task_id}`

### 用途
删除任务。首版建议做软删除。

### 成功响应

```json
{
  "success": true,
  "message": "task deleted",
  "data": null
}
```

---

## 5.6 更新任务状态（内部接口，可选）

### 接口
`PATCH /api/tasks/{task_id}/status`

### 用途
用于系统内部更新任务状态，首版可以不对前端开放。

### 请求体

```json
{
  "status": "prompt_generated"
}
```

---

## 6. 分析包接口

## 6.1 上传分析包

### 接口
`POST /api/tasks/{task_id}/package`

### 用途
为某个任务上传本地预处理工具生成的 ZIP 分析包。

### 请求类型
`multipart/form-data`

### 字段
- `file`：ZIP 文件，必填

### 成功响应

```json
{
  "success": true,
  "message": "package uploaded",
  "data": {
    "package_id": 3,
    "package_status": "parsed",
    "task_status": "package_uploaded"
  }
}
```

### 失败场景
- ZIP 无法解压
- 缺少核心文件
- 文件过大
- 文件类型不合法

---

## 6.2 获取分析包摘要

### 接口
`GET /api/tasks/{task_id}/package`

### 用途
获取当前任务绑定的分析包摘要信息。

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "id": 3,
    "video_name": "demo.mp4",
    "duration_sec": 28.5,
    "resolution": "1920x1080",
    "fps": 60.0,
    "bitrate_kbps": 32000,
    "frame_count": 18,
    "segment_count": 7,
    "has_transcript": true,
    "contact_sheet_path": "/files/tasks/1/package/contact_sheet.jpg",
    "created_at": "2026-04-18T12:40:00+08:00"
  }
}
```

---

## 6.3 获取分析包文件列表

### 接口
`GET /api/tasks/{task_id}/package/files`

### 用途
获取分析包内文件索引，例如关键帧、Contact Sheet、transcript、音频等。

### 查询参数
- `file_type`：可选，例如 `frame` / `contact_sheet` / `transcript` / `audio`

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 11,
        "file_type": "frame",
        "file_name": "frame_0001.jpg",
        "file_path": "/files/tasks/1/package/frames/frame_0001.jpg",
        "sort_order": 1
      }
    ]
  }
}
```

---

## 6.4 获取片段列表

### 接口
`GET /api/tasks/{task_id}/segments`

### 用途
获取该任务分析包中的片段摘要。

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 21,
        "segment_index": 0,
        "start_sec": 0.0,
        "end_sec": 2.3,
        "duration_sec": 2.3,
        "keyframe_path": "/files/tasks/1/package/segment_keyframes/seg_000_01.jpg"
      }
    ]
  }
}
```

---

## 6.5 重新解析分析包（内部接口，可选）

### 接口
`POST /api/tasks/{task_id}/package/reparse`

### 用途
当分析包元信息异常时，允许重新执行解析逻辑。

---

## 7. Prompt 接口

## 7.1 生成 Prompt

### 接口
`POST /api/tasks/{task_id}/prompts`

### 用途
基于任务类型、分析包摘要、知识库和模板生成 Prompt。

### 请求体

```json
{
  "template_id": 2,
  "use_knowledge": true,
  "regenerate": false
}
```

### 字段说明
- `template_id`：可选，指定模板
- `use_knowledge`：是否启用知识库
- `regenerate`：是否重新生成新版本 Prompt

### 成功响应

```json
{
  "success": true,
  "message": "prompt generated",
  "data": {
    "prompt_id": 5,
    "task_status": "prompt_generated",
    "prompt_type": "reference",
    "created_at": "2026-04-18T12:50:00+08:00"
  }
}
```

---

## 7.2 获取当前 Prompt

### 接口
`GET /api/tasks/{task_id}/prompts/current`

### 用途
获取当前任务正在使用的 Prompt。

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "id": 5,
    "prompt_type": "reference",
    "title": "默认拆解模式 Prompt",
    "content": "请根据以下关键帧...",
    "extra_questions": "1. 请补充说明...",
    "attachment_guide": "请附带 contact_sheet.jpg 和前 12 张关键帧",
    "fillback_template": "请按以下结构输出...",
    "knowledge_snapshot": "已引用：旅行vlog调色、夜景镜头组织",
    "version": 1,
    "created_at": "2026-04-18T12:50:00+08:00"
  }
}
```

---

## 7.3 获取 Prompt 历史列表

### 接口
`GET /api/tasks/{task_id}/prompts`

### 用途
查看该任务历史生成过的 Prompt 版本。

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 5,
        "version": 1,
        "is_current": true,
        "created_at": "2026-04-18T12:50:00+08:00"
      }
    ]
  }
}
```

---

## 7.4 获取单个 Prompt 详情

### 接口
`GET /api/prompts/{prompt_id}`

### 用途
根据 Prompt ID 查看完整内容。

---

## 7.5 设为当前 Prompt（可选）

### 接口
`PATCH /api/prompts/{prompt_id}/set-current`

### 用途
当一个任务生成过多个 Prompt 时，手动切换当前版本。

---

## 7.6 获取 Prompt 模板列表

### 接口
`GET /api/prompt-templates`

### 用途
获取可用 Prompt 模板。

### 查询参数
- `task_type`：可选
- `is_active`：可选

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 2,
        "template_key": "reference_default",
        "template_name": "默认拆解模板",
        "task_type": "reference",
        "is_default": true,
        "version": 1
      }
    ]
  }
}
```

---

## 7.7 获取 Prompt 模板详情

### 接口
`GET /api/prompt-templates/{template_id}`

### 用途
查看模板详细内容。

---

## 8. 回填结果接口

## 8.1 提交回填结果

### 接口
`POST /api/tasks/{task_id}/results`

### 用途
提交从 ChatGPT / DeepSeek 获取的分析结果。

### 请求体

```json
{
  "prompt_id": 5,
  "source_model": "chatgpt",
  "source_model_detail": "gpt-5.4",
  "input_method": "paste",
  "raw_text": "以下是视频分析结果...",
  "notes": "这次重点看调色和镜头节奏"
}
```

### 成功响应

```json
{
  "success": true,
  "message": "result submitted",
  "data": {
    "result_id": 7,
    "task_status": "result_filled",
    "created_at": "2026-04-18T13:20:00+08:00"
  }
}
```

---

## 8.2 上传 Markdown / TXT 回填结果

### 接口
`POST /api/tasks/{task_id}/results/upload`

### 用途
通过上传文件方式提交回填结果。

### 请求类型
`multipart/form-data`

### 字段
- `file`：Markdown 或 TXT 文件
- `source_model`：可选
- `source_model_detail`：可选

---

## 8.3 获取当前结果

### 接口
`GET /api/tasks/{task_id}/results/current`

### 用途
获取当前任务最近或当前使用的结果记录。

---

## 8.4 获取结果历史列表

### 接口
`GET /api/tasks/{task_id}/results`

### 用途
查看某任务下所有回填结果记录。

---

## 8.5 获取单个结果详情

### 接口
`GET /api/results/{result_id}`

### 用途
查看单条回填结果详情，包括原文和摘要。

---

## 8.6 删除结果（可选）

### 接口
`DELETE /api/results/{result_id}`

### 用途
删除某条回填结果记录。

---

## 9. 报告接口

## 9.1 生成报告

### 接口
`POST /api/tasks/{task_id}/report`

### 用途
基于当前任务的当前结果，生成结构化报告。

### 请求体

```json
{
  "result_id": 7,
  "force_regenerate": false
}
```

### 成功响应

```json
{
  "success": true,
  "message": "report generated",
  "data": {
    "report_id": 9,
    "task_status": "report_ready",
    "created_at": "2026-04-18T13:25:00+08:00"
  }
}
```

---

## 9.2 获取当前报告

### 接口
`GET /api/tasks/{task_id}/report/current`

### 用途
查看当前任务的当前报告。

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "id": 9,
    "report_type": "reference",
    "title": "沈阳旅行视频拆解报告",
    "overview": "该视频整体偏暖色旅行vlog风格...",
    "structured_content": {
      "style_tags": ["旅行vlog", "暖色", "快节奏"],
      "sections": []
    },
    "version": 1,
    "created_at": "2026-04-18T13:25:00+08:00"
  }
}
```

---

## 9.3 获取报告历史列表

### 接口
`GET /api/tasks/{task_id}/reports`

### 用途
查看当前任务的历史报告版本。

---

## 9.4 获取单个报告详情

### 接口
`GET /api/reports/{report_id}`

### 用途
查看报告详情。

---

## 9.5 设为当前报告（可选）

### 接口
`PATCH /api/reports/{report_id}/set-current`

### 用途
切换当前报告版本。

---

## 9.6 删除报告（可选）

### 接口
`DELETE /api/reports/{report_id}`

### 用途
删除某个报告版本。

---

## 10. 知识库接口

## 10.1 获取知识库列表

### 接口
`GET /api/knowledge-items`

### 用途
获取知识库条目列表。

### 查询参数
- `category`：可选
- `keyword`：可选
- `is_active`：可选
- `page`：可选
- `page_size`：可选

---

## 10.2 获取知识库详情

### 接口
`GET /api/knowledge-items/{item_id}`

### 用途
查看单条知识库条目详细内容。

---

## 10.3 搜索知识库

### 接口
`GET /api/knowledge-items/search`

### 用途
按关键词搜索知识条目。

### 查询参数
- `q`：关键词，必填
- `category`：可选

### 响应示例

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "items": [
      {
        "id": 5,
        "title": "旅行vlog常见暖色调色思路",
        "category": "color",
        "summary": "适合日落、街景、人物记录类内容"
      }
    ]
  }
}
```

---

## 10.4 获取知识分类列表

### 接口
`GET /api/knowledge-categories`

### 用途
获取所有知识库分类，用于页面筛选。

---

## 10.5 重新加载知识库（内部接口，可选）

### 接口
`POST /api/knowledge-items/reload`

### 用途
当仓库内知识文件更新后，重新载入知识库。

---

## 11. 设置接口

## 11.1 获取系统设置

### 接口
`GET /api/settings`

### 用途
获取系统设置与当前默认选项。

### 响应示例

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "storage_root": "./storage",
    "max_package_upload_mb": 50,
    "default_prompt_template_reference": 2,
    "default_prompt_template_improve": 3,
    "history_keep_days": 90
  }
}
```

---

## 11.2 更新系统设置

### 接口
`PATCH /api/settings`

### 用途
更新可调整的系统设置。

### 请求体

```json
{
  "history_keep_days": 120,
  "max_package_upload_mb": 80
}
```

### 备注
首版应限制可修改范围，避免影响核心运行逻辑。

---

## 11.3 获取当前默认模板配置

### 接口
`GET /api/settings/templates`

### 用途
获取当前默认 Prompt 模板配置。

---

## 11.4 更新默认模板配置

### 接口
`PATCH /api/settings/templates`

### 用途
更新默认拆解模式 / 优化模式模板。

### 请求体

```json
{
  "default_prompt_template_reference": 2,
  "default_prompt_template_improve": 3
}
```

---

## 12. 文件与导出接口

## 12.1 获取文件访问地址（可选）

### 接口
`GET /api/files/{file_id}`

### 用途
获取某个文件的访问元信息。若静态文件直接走 `/files/...`，则此接口可后置。

---

## 12.2 导出 Prompt 文本

### 接口
`GET /api/prompts/{prompt_id}/export`

### 用途
导出 Prompt 为 txt / md。

### 查询参数
- `format`：`txt` / `md`

---

## 12.3 导出报告

### 接口
`GET /api/reports/{report_id}/export`

### 用途
导出报告。

### 查询参数
- `format`：`md` / `txt`

### 首版建议
先支持：
- Markdown
- 纯文本

PDF 可后续再做。

---

## 12.4 下载原始回填结果

### 接口
`GET /api/results/{result_id}/export`

### 用途
导出某次回填结果原文。

---

## 13. 健康检查接口

## 13.1 服务健康检查

### 接口
`GET /api/health`

### 用途
用于 Docker、统一网关联调或人工排查时确认服务是否可用。

### 响应

```json
{
  "success": true,
  "message": "ok",
  "data": {
    "status": "healthy"
  }
}
```

---

## 13.2 系统摘要信息（可选）

### 接口
`GET /api/system/summary`

### 用途
获取简单系统摘要，例如任务总数、报告总数、知识条目数。

### 13.3 网关联调检查项（新增）

当智摄接入统一公网网关后，接口联调至少需要确认：

- `GET /api/health` 可通过内网预览端口访问
- `GET /api/health` 可通过正式域名访问
- `/api/*` 请求不会被页面路由吞掉
- 上传与导出路径能正确转发到应用容器

---

## 14. 页面路由建议（非 API）

为了和 API 配合，首版页面路由建议如下：

- `/login`：登录页
- `/`：首页 / 仪表盘
- `/tasks`：任务列表页
- `/tasks/new`：新建任务页
- `/tasks/{task_id}`：任务详情页
- `/tasks/{task_id}/prompt`：Prompt 页面
- `/tasks/{task_id}/fillback`：结果回填页
- `/tasks/{task_id}/report`：报告页
- `/knowledge`：知识库页
- `/settings`：设置页

---

## 15. 状态码建议

首版可采用以下 HTTP 状态码习惯：

- `200 OK`：查询或操作成功
- `201 Created`：创建成功
- `400 Bad Request`：参数错误
- `401 Unauthorized`：未登录
- `403 Forbidden`：无权限
- `404 Not Found`：资源不存在
- `409 Conflict`：状态冲突，例如重复上传
- `422 Unprocessable Entity`：校验失败
- `500 Internal Server Error`：服务异常

---

## 16. 错误码建议

建议首版预留统一错误码，例如：

### 认证类
- `AUTH_REQUIRED`
- `AUTH_INVALID_CREDENTIALS`
- `AUTH_USER_DISABLED`

### 任务类
- `TASK_NOT_FOUND`
- `TASK_INVALID_TYPE`
- `TASK_STATUS_CONFLICT`

### 分析包类
- `PACKAGE_UPLOAD_FAILED`
- `PACKAGE_INVALID_FORMAT`
- `PACKAGE_PARSE_FAILED`
- `PACKAGE_FILE_TOO_LARGE`
- `PACKAGE_REQUIRED_FILE_MISSING`

### Prompt 类
- `PROMPT_TEMPLATE_NOT_FOUND`
- `PROMPT_GENERATE_FAILED`

### 结果类
- `RESULT_NOT_FOUND`
- `RESULT_EMPTY_CONTENT`
- `RESULT_UPLOAD_FAILED`

### 报告类
- `REPORT_NOT_FOUND`
- `REPORT_GENERATE_FAILED`

### 知识库类
- `KNOWLEDGE_NOT_FOUND`
- `KNOWLEDGE_RELOAD_FAILED`

### 系统类
- `SYSTEM_INVALID_SETTING`
- `SYSTEM_STORAGE_ERROR`
- `SYSTEM_DB_ERROR`

---

## 17. 首版开发优先级建议

## 17.1 第一批必须实现

优先实现以下接口：
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/tasks`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/package`
- `GET /api/tasks/{task_id}/package`
- `GET /api/tasks/{task_id}/segments`
- `POST /api/tasks/{task_id}/prompts`
- `GET /api/tasks/{task_id}/prompts/current`
- `POST /api/tasks/{task_id}/results`
- `GET /api/tasks/{task_id}/results/current`
- `POST /api/tasks/{task_id}/report`
- `GET /api/tasks/{task_id}/report/current`
- `GET /api/knowledge-items`
- `GET /api/settings`
- `GET /api/health`

## 17.2 第二批建议实现
- Prompt 历史
- 结果历史
- 报告历史
- 导出接口
- 搜索接口
- 模板配置接口

## 17.3 后续可扩展
- 自动调用模型 API
- 更细粒度模板管理
- 批量任务接口
- Webhook / 异步通知接口

---

## 18. 首版流程对应关系

为了方便开发，首版可以按页面流程理解接口组合：

### 登录流程
- `POST /api/auth/login`
- `GET /api/auth/me`

### 新建任务流程
- `POST /api/tasks`
- `POST /api/tasks/{task_id}/package`
- `GET /api/tasks/{task_id}`

### Prompt 生成流程
- `POST /api/tasks/{task_id}/prompts`
- `GET /api/tasks/{task_id}/prompts/current`
- `GET /api/prompt-templates`

### 回填流程
- `POST /api/tasks/{task_id}/results`
- `GET /api/tasks/{task_id}/results/current`

### 报告流程
- `POST /api/tasks/{task_id}/report`
- `GET /api/tasks/{task_id}/report/current`
- `GET /api/reports/{report_id}/export`

### 历史与知识库流程
- `GET /api/tasks`
- `GET /api/knowledge-items`
- `GET /api/knowledge-items/search`

---

## 19. 一句话总结

**智摄首版 API 的核心任务，不是做大而全，而是把“上传分析包、生成 Prompt、回填结果、生成报告”这条链路稳定打通。**
