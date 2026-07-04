# vibeRepository - AI 开源项目每日研究工作流

自动化 AI 开源项目研究、测试与知识库维护系统。每天自动从 GitHub、HuggingFace、HackerNews、Reddit 等平台采集热门 AI 项目，经过多轮筛选、真实安装运行测试，最终生成完整的评测报告和知识库。

## 功能特性

### 数据采集
- GitHub Trending / GitHub Search
- HuggingFace 热门模型
- Hacker News 热门话题
- Reddit AI 社区
- 支持扩展 Product Hunt、Papers With Code 等

### 项目筛选
- 多轮筛选机制（300 → 50 → 20 → TOP5/TOP10）
- 热度、创新度、完整度多维度评分
- 自动过滤 Awesome、Tutorial、Fork 等非原创项目
- 支持 AI / LLM / Agent / MCP / Coding / RAG / Workflow 等分类

### 真实测试
- 自动 Clone 项目仓库
- 智能识别安装方式（pip/poetry/uv/npm/pnpm/cargo/go/docker）
- 自动安装依赖并启动项目
- 真实运行 Demo 并验证功能
- 记录启动时间、CPU、内存、磁盘占用

### 文档与报告
- 自动生成中文 README、QuickStart、Review、Comparison、FAQ、Benchmark、Summary
- 自动生成 Mermaid / PlantUML 架构图
- 每日报告 / 每周 TOP10 / 月度报告
- AI 趋势分析

### 知识库管理
- 自动分类归档（Agent/Coding/MCP/Workflow/LLM/RAG 等）
- 90 分以上且通过测试的项目才能入库
- project.json 元数据管理
- GitHub 自动同步

## 系统架构

```
main.py (主入口)
├── modules/collector.py      # 数据采集
├── modules/filter.py         # 项目筛选
├── modules/analyzer.py       # 项目分析
├── modules/installer.py      # 自动安装
├── modules/runner.py         # 真实运行
├── modules/tester.py         # 功能测试
├── modules/screenshot.py     # 截图录屏
├── modules/performance.py    # 性能分析
├── modules/competitor.py     # 竞品分析
├── modules/documenter.py     # 文档生成
├── modules/architect.py      # 架构图生成
├── modules/scoring.py        # AI评分
├── modules/knowledge_base.py # 知识库管理
├── modules/reporter.py       # 报告生成
└── modules/github_sync.py    # GitHub同步
```

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置

编辑 `config.yaml`：

```yaml
github:
  token: "your_github_token"  # 可选，提高 API 限制

github_sync:
  enabled: false               # 是否启用 GitHub 同步
  repo_url: "https://github.com/your/repo"
```

### 运行

```bash
python main.py
```

### 运行测试

```bash
python test_system.py
```

## 输出目录

```
Daily-Reports/     # 每日报告
Weekly-Reports/    # 每周报告
Monthly-Reports/   # 每月报告
Knowledge-Base/    # 知识库（90分以上项目）
Architecture/      # 架构图
Metadata/          # 元数据
workspace/         # 工作目录
├── clones/        # Clone 的项目
├── screenshots/   # 截图
├── demos/         # Demo 视频
└── logs/          # 日志
```

## 评分标准

| 维度 | 权重 | 说明 |
|------|------|------|
| 热度 | 20% | Star 数量、增长速度、Fork 数 |
| 创新 | 20% | 功能独特性、技术创新性 |
| 完整度 | 20% | 文档、Demo、Docker 支持 |
| 运行成功 | 20% | 安装、启动、Demo 实测 |
| 实际价值 | 20% | 解决问题的价值、适用场景 |

- 综合评分 90 分以上且推荐指数 ≥ ★★★★☆ 的项目进入知识库
- 周一至周六按 24 小时新增 Star 排序 TOP5
- 周日按总 Star 排序 TOP10

## 技术栈

- **语言**: Python 3.10+
- **核心库**: requests, beautifulsoup4, Playwright, psutil, GitPython
- **配置**: YAML
- **输出**: Markdown, Mermaid, PlantUML

## License

MIT
