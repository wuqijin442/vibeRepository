# vibeRepository - AI 开源项目每日研究知识库

> 自动化 AI 开源项目研究、真实测试与知识库维护系统。每日从 GitHub、HuggingFace、HackerNews、Reddit 等平台采集热门 AI 项目，经过多轮筛选、真实安装运行测试，最终生成完整评测报告与知识库。

## 📊 知识库总览

| 指标 | 数值 |
|------|------|
| 最近更新日期 | 2026-07-16 |
| 累计日报数 | 11 |
| 知识库项目数 | 7 |
| 推荐项目数(≥90分) | 0 |
| 板块测试项目数 | 55 |

## 🏆 最近推荐项目 TOP 10

| # | 项目 | 评分 | 推荐指数 | 总 Star | 分类 |
|---|------|------|----------|---------|------|
| - | 暂无 90 分以上项目，持续测试中 | - | - | - | - |

## 🗂️ 精品板块合集（参考 gitcn.org/top）

参考 gitcn.org/top 板块分类，对每个热门板块 top5 项目进行真实测试，额外增加 3 个精品板块。

### 核心板块（8 个）

| 板块 | 最佳项目 | 评分 | 报告 |
|------|----------|------|------|
| 前端开发 | [PanJiaChen/vue-element-admin](https://github.com/PanJiaChen/vue-element-admin) | 81.4 | [查看](Boards-Reports/frontend/2026-07-16_Report.md) |
| 后端开发 | [BerriAI/litellm](https://github.com/BerriAI/litellm) | 75.4 | [查看](Boards-Reports/backend/2026-07-16_Report.md) |
| 数据库 | [makeplane/plane](https://github.com/makeplane/plane) | 75.4 | [查看](Boards-Reports/database/2026-07-16_Report.md) |
| 自动化 | [activepieces/activepieces](https://github.com/activepieces/activepieces) | 89.4 | [查看](Boards-Reports/automation/2026-07-16_Report.md) |
| 自托管服务 | [coollabsio/coolify](https://github.com/coollabsio/coolify) | 72.4 | [查看](Boards-Reports/self-hosting/2026-07-16_Report.md) |
| 开发工具 | [cli/cli](https://github.com/cli/cli) | 71.4 | [查看](Boards-Reports/devtools/2026-07-16_Report.md) |
| 安全 | [usestrix/strix](https://github.com/usestrix/strix) | 73.4 | [查看](Boards-Reports/security/2026-07-16_Report.md) |
| 编辑器 | [toeverything/AFFiNE](https://github.com/toeverything/AFFiNE) | 64.4 | [查看](Boards-Reports/editor/2026-07-16_Report.md) |

### 精品板块（3 个）

| 板块 | 最佳项目 | 评分 | 报告 |
|------|----------|------|------|
| 🌟 黑科技工具 | [browser-use/browser-use](https://github.com/browser-use/browser-use) | 77.4 | [查看](Boards-Reports/black-tech/2026-07-16_Report.md) |
| 🌟 大模型训练 | [hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) | 72.4 | [查看](Boards-Reports/llm-training/2026-07-16_Report.md) |
| 🌟 学习网站 | [yangshun/tech-interview-handbook](https://github.com/yangshun/tech-interview-handbook) | 80.4 | [查看](Boards-Reports/learning/2026-07-16_Report.md) |

> 板块测试汇总: [2026-07-16 Boards-Summary](Boards-Reports/2026-07-16_Boards-Summary.md) · 共测试 55 个项目（11 板块 × top5），安装成功 30，运行成功 5

## 📁 目录结构

```
Daily-Reports/        # 每日报告（今日 TOP5/TOP10）
Weekly-Reports/       # 每周 TOP10 报告
Monthly-Reports/      # 月度报告
Boards-Reports/       # 板块 Top5 测试报告（参考 gitcn.org/top）
  └── <板块>/          # frontend/backend/database/...
      └── <日期>_Report.md
Knowledge-Base/       # 知识库（评分≥90 且测试通过的项目）
  └── <项目名>/
      ├── README_CN.md   # 中文说明
      ├── QuickStart.md  # 快速开始
      ├── Review.md      # 评测
      ├── Comparison.md  # 竞品对比
      ├── FAQ.md         # 常见问题
      ├── Benchmark.md   # 性能基准
      ├── Summary.md     # 总结
      └── project.json   # 元数据
Architecture/         # 架构图（Mermaid / PlantUML）
Metadata/             # 项目元数据
Screenshots/          # 截图与 Demo
Logs/                 # 运行日志
Reviews/              # 评测文章
Benchmarks/           # 基准测试
Awesome-Projects/     # 精选项目列表
```

## 🔄 自动更新机制

- **每日**: 自动扫描 300+ 项目 → 3 轮筛选 → TOP5 深度测试 → 生成日报
- **周日**: 按 GitHub 总 Star 排序 TOP10，生成周报
- **月末**: 汇总月度数据，生成月报
- **GitHub 同步**: 仅同步评分 ≥90 且测试通过的项目，提交账号 `wuqijin442`

## 📋 评分标准

| 维度 | 权重 | 说明 |
|------|------|------|
| 热度 | 20% | Star 数量、增长速度、Fork 数 |
| 创新 | 20% | 功能独特性、技术创新性 |
| 完整度 | 20% | 文档、Demo、Docker 支持 |
| 运行成功 | 20% | 安装、启动、Demo 实测 |
| 实际价值 | 20% | 解决问题的价值、适用场景 |

综合评分 ≥90 分且推荐指数 ≥★★★★☆ 的项目方可进入知识库。

## 📌 最近日报

最近一次日报: `2026-07-16`

## 🔗 相关链接

- 工作流源码: 本仓库根目录 `main.py` + `modules/`
- 配置文件: `config.yaml`
- 提交规范: `[2026-07-16] Daily AI Project Update`

---

*本 README 由 AI 工作流自动维护，每次同步自动更新统计与推荐列表。最后更新: 2026-07-16*
