# AI Consultant App

一个面向售前/产品团队的内部 AI 顾问辅助工具。输入客户原始业务需求后，系统会调用大模型对需求进行功能原子化拆解，并输出按模块组织的工程实施建议、AI 能力要求和顾问侧的可行性建议。

## 当前目标

这个仓库目前展示的是一个可运行的 MVP / demo：
- 前端提供需求输入、任务轮询、报告展示和 Markdown 导出
- 后端通过 FastAPI 暴露分析接口和反馈接口
- 分析流程优先调用 GLM，失败时回退到 Qwen
- 输出重点面向高校/教育场景的 AI 方案拆解

## 主要功能

- 客户原始需求输入
- 后台异步分析任务
- 分模块结构化输出
- Markdown 报告导出
- 简单反馈收集
- 未来版本预告 UI

## 技术栈

- Frontend: 单文件 HTML + React 18 UMD + Babel Standalone + Tailwind CDN
- Backend: FastAPI
- Model Providers: GLM / DashScope(Qwen via OpenAI-compatible API)
- Runtime: Uvicorn

## 仓库结构

- `main.py`: FastAPI 服务入口，分析与反馈 API
- `ai_consultant_assistant_ui.html`: 主前端界面
- `feature_preview.html`: 版本预告/设计预览页
- `system_prompt.md`: 系统提示词与输出约束
- `requirements.txt`: Python 依赖
- `Procfile`: 部署入口
- `start_server.sh`: 启动脚本
- `意见反馈文件.txt`: 反馈落盘文件
- `feedback_rules.txt`: 示例反馈内容

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

建议使用环境变量，不要在代码中保留真实密钥：

```bash
DASHSCOPE_API_KEY=your_dashscope_key
GLM_API_KEY=your_glm_key
PORT=8000
```

### 3. 启动服务

```bash
python main.py
```

服务启动后访问：

```text
http://127.0.0.1:8000/
```

## API 概览

### `POST /api/analyze`

输入：

```json
{
  "requirement": "客户原始需求文本"
}
```

返回：

```json
{
  "task_id": "uuid",
  "status": "processing"
}
```

### `GET /api/status/{task_id}`

查询后台分析任务状态与结果。

### `POST /api/feedback`

输入：

```json
{
  "feedback": "反馈内容"
}
```

## 当前仓库仍缺少的基础协作信息

为了让 GitHub 仓库真正具备可协作性，建议继续补齐：

- 仓库描述与 topics
- `.env.example`
- LICENSE
- 运行截图或演示 GIF
- Roadmap / Milestones
- Issue 模板和 PR 模板
- 最小测试与部署说明

## 已知问题与建议

- `main.py` 当前包含硬编码 API key fallback，这不适合公开仓库
- 代码与资源全部平铺在根目录，后续应拆分为 `frontend/`、`backend/`、`docs/` 等目录
- 前端依赖 CDN + Babel Standalone，更适合 demo，不适合长期工程化维护
- 当前没有 README、贡献说明、Issue/PR 记录，外部很难理解项目意图与演进过程

## 建议的下一步

1. 先移除仓库中的硬编码密钥
2. 增加 `.env.example` 和部署说明
3. 用 Issues 跟踪需求、缺陷和 Roadmap
4. 用 Pull Requests 保留变更讨论和评审记录
5. 用 Releases / Tags 标记可运行版本
