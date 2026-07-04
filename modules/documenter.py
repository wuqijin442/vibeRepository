#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class DocumentGenerator:
    def __init__(self, config):
        self.config = config
        self.kb_dir = Path(config.get('paths', {}).get('knowledge_base', './Knowledge-Base'))
        self.kb_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        safe_name = name.replace('/', '_').replace('\\', '_')
        
        logger.info(f"生成中文文档: {name}")
        
        project['docs_generated'] = False
        project['docs_path'] = None
        
        proj_dir = self.kb_dir / safe_name
        proj_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self._generate_readme_cn(project, proj_dir)
            self._generate_quickstart(project, proj_dir)
            self._generate_review(project, proj_dir)
            self._generate_comparison(project, proj_dir)
            self._generate_faq(project, proj_dir)
            self._generate_benchmark(project, proj_dir)
            self._generate_summary(project, proj_dir)
            
            project['docs_generated'] = True
            project['docs_path'] = str(proj_dir)
            
        except Exception as e:
            logger.error(f"生成文档失败 {name}: {e}")
            project['docs_error'] = str(e)
        
        return project

    def _generate_readme_cn(self, project: Dict, proj_dir: Path):
        name = project.get('name', '')
        description = project.get('description', '')
        tags = project.get('tags', [])
        readme = project.get('readme_content', '')
        
        content = f"""# {name} - 中文文档

## 项目简介

{description if description else '暂无简介'}

**标签**: {', '.join(tags)}

**项目地址**: {project.get('url', '')}

## 技术栈

- **主要语言**: {project.get('primary_language', 'Unknown')}
- **框架**: {', '.join(project.get('frameworks', [])) or '暂无'}
- **License**: {project.get('license', 'Unknown')}
- **支持平台**: {', '.join(project.get('supported_platforms', ['Linux']))}

## 功能特性

根据项目分析，该项目主要功能包括：

"""
        
        for use_case in project.get('use_cases', []):
            content += f"- {use_case}\n"
        
        content += f"""
## 安装方式

推荐安装方式: **{project.get('install_method', '未知')}**

详细安装步骤请参考 [QuickStart.md](./QuickStart.md)

## 运行说明

- **启动耗时**: {project.get('startup_time', 0)}s
- **内存占用**: {project.get('memory_usage', 0)}MB
- **CPU占用**: {project.get('cpu_usage', 0)}%

## 社区数据

- **Stars**: {project.get('stars', 0)}
- **今日新增**: {project.get('daily_stars', 0)}
- **Forks**: {project.get('forks', 0)}

---

*本文档由 AI 自动生成，可能存在不准确之处，请以官方文档为准。*
"""
        
        with open(proj_dir / 'README_CN.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_quickstart(self, project: Dict, proj_dir: Path):
        name = project.get('name', '')
        install_method = project.get('install_method', '')
        
        content = f"""# {name} 快速开始

## 前置要求

- **操作系统**: {', '.join(project.get('supported_platforms', ['Linux']))}
- **主要语言环境**: {project.get('primary_language', 'Unknown')}
- **依赖管理工具**: {install_method}

## 安装步骤

### 1. Clone 项目

```bash
git clone {project.get('url', '')}
cd {name.split('/')[-1]}
```

### 2. 安装依赖

"""
        
        if install_method in ['pip_requirements', 'uv', 'pip_setup']:
            content += """```bash
# 使用 pip
pip install -r requirements.txt

# 或使用 uv（推荐）
uv pip install -r requirements.txt
```
"""
        elif install_method == 'poetry':
            content += """```bash
poetry install
```
"""
        elif install_method in ['npm', 'pnpm', 'yarn', 'bun']:
            content += f"""```bash
{install_method} install
```
"""
        elif install_method == 'cargo':
            content += """```bash
cargo build --release
```
"""
        elif install_method == 'go':
            content += """```bash
go build ./...
```
"""
        else:
            content += "请参考项目官方文档进行安装。\n"
        
        content += f"""
### 3. 运行项目

```bash
{project.get('run_command', '请参考官方文档')}
```

## 验证安装

- 运行 Demo: {'成功' if project.get('demo_success', False) else '待验证'}
- 启动时间: {project.get('startup_time', 0)}s
- 内存占用: {project.get('memory_usage', 0)}MB

## 常见问题

请参考 [FAQ.md](./FAQ.md)

---

*本文档由 AI 自动生成，仅供参考。*
"""
        
        with open(proj_dir / 'QuickStart.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_review(self, project: Dict, proj_dir: Path):
        name = project.get('name', '')
        
        content = f"""# {name} 评测报告

## 项目概述

**项目名称**: {name}
**项目地址**: {project.get('url', '')}
**一句话介绍**: {project.get('description', '')}

## 评测结果

| 维度 | 评分 | 说明 |
|------|------|------|
| 热度 | {"%.1f" % (project.get('heat_score', 0) * 2)} / 100 | 基于 Star 数量和增长速度 |
| 创新性 | 待评估 | 基于功能独特性 |
| 完整度 | 待评估 | 基于文档和功能完整性 |
| 运行成功率 | {'成功' if project.get('run_success', False) else '失败'} | 实际运行测试结果 |
| 实际价值 | 待评估 | 基于解决问题的实际价值 |

## 优点

"""
        
        for adv in project.get('advantages', []):
            content += f"- {adv}\n"
        
        content += """
## 缺点

"""
        
        for dis in project.get('disadvantages', []):
            content += f"- {dis}\n"
        
        content += f"""
## 适用人群

{', '.join(project.get('target_audience', []))}

## 适用场景

"""
        
        for uc in project.get('use_cases', []):
            content += f"- {uc}\n"
        
        content += f"""
## 性能数据

- 安装耗时: {project.get('install_time', 0)}s
- 启动耗时: {project.get('startup_time', 0)}s
- 内存占用: {project.get('memory_usage', 0)}MB
- CPU占用: {project.get('cpu_usage', 0)}%
- 磁盘占用: {project.get('perf_disk_usage', 0)}MB

## 推荐指数

{"★" * max(1, min(5, int(project.get('score', 0) / 20)))}{"☆" * max(0, 5 - max(1, min(5, int(project.get('score', 0) / 20))))} ({project.get('score', 0)}分)

---

*本评测由 AI 自动生成，基于真实运行数据。*
"""
        
        with open(proj_dir / 'Review.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_comparison(self, project: Dict, proj_dir: Path):
        name = project.get('name', '')
        competitors = project.get('competitors', [])
        
        content = f"""# {name} 竞品分析

## 同类项目

"""
        
        if competitors:
            for comp in competitors:
                content += f"- {comp}\n"
        else:
            content += "暂未发现直接竞品\n"
        
        content += f"""
## 对比分析

| 项目 | 优势 | 劣势 | 适用场景 |
|------|------|------|----------|
| {name} | {'; '.join(project.get('advantages', [])[:3])} | {'; '.join(project.get('disadvantages', [])[:2])} | {'; '.join(project.get('use_cases', [])[:2])} |
"""
        
        for comp in competitors[:3]:
            content += f"| {comp} | 待对比 | 待对比 | 待对比 |\n"
        
        content += f"""
## 本项目独特优势

"""
        
        for i, adv in enumerate(project.get('advantages', []), 1):
            content += f"{i}. {adv}\n"
        
        content += """
---

*本分析由 AI 自动生成，仅供参考。*
"""
        
        with open(proj_dir / 'Comparison.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_faq(self, project: Dict, proj_dir: Path):
        name = project.get('name', '')
        
        content = f"""# {name} 常见问题

## 安装相关

### Q: 安装失败怎么办？
A: 请检查以下几点：
1. 确保已安装正确版本的运行环境
2. 检查网络连接是否正常
3. 查看错误日志，根据具体错误信息解决

### Q: 支持哪些操作系统？
A: {', '.join(project.get('supported_platforms', ['Linux']))}

## 运行相关

### Q: 启动后无法访问？
A: 请检查：
1. 端口是否被占用
2. 防火墙设置
3. 配置文件中的端口设置

### Q: 内存占用过高？
A: 可以尝试：
1. 减少并发数量
2. 调整配置参数
3. 使用更小的模型（如适用）

## 其他

### Q: 项目还在维护吗？
A: 根据最后更新时间判断，建议查看 GitHub 项目页面确认。

### Q: 如何贡献代码？
A: 请参考项目官方 CONTRIBUTING 文档。

---

*本 FAQ 由 AI 自动生成，可能不完全准确。*
"""
        
        with open(proj_dir / 'FAQ.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_benchmark(self, project: Dict, proj_dir: Path):
        name = project.get('name', '')
        
        content = f"""# {name} 性能基准

## 测试环境

- 操作系统: Linux
- 测试时间: {project.get('collected_at', '未知')}

## 安装性能

| 指标 | 数值 |
|------|------|
| 安装方式 | {project.get('install_method', '未知')} |
| 安装耗时 | {project.get('install_time', 0)}s |
| 磁盘占用 | {project.get('perf_disk_usage', 0)}MB |
| 安装是否成功 | {'是' if project.get('install_success', False) else '否'} |

## 运行性能

| 指标 | 数值 |
|------|------|
| 启动耗时 | {project.get('startup_time', 0)}s |
| 内存占用 | {project.get('memory_usage', 0)}MB |
| CPU占用 | {project.get('cpu_usage', 0)}% |
| 运行是否成功 | {'是' if project.get('run_success', False) else '否'} |
| Demo是否成功 | {'是' if project.get('demo_success', False) else '否'} |

## 兼容性

| 平台 | 支持情况 |
|------|----------|
"""
        
        for plat in project.get('supported_platforms', ['Linux']):
            content += f"| {plat} | {'✓' if plat == 'Linux' else '待验证'} |\n"
        
        content += f"""
| Docker | {'✓' if project.get('has_docker', False) else '✗'} |

---

*本基准测试由 AI 自动生成，结果仅供参考。*
"""
        
        with open(proj_dir / 'Benchmark.md', 'w', encoding='utf-8') as f:
            f.write(content)

    def _generate_summary(self, project: Dict, proj_dir: Path):
        name = project.get('name', '')
        
        content = f"""# {name} 项目摘要

## 基本信息

- **项目名称**: {name}
- **项目地址**: {project.get('url', '')}
- **作者**: {project.get('author', '未知')}
- **License**: {project.get('license', '未知')}
- **主要语言**: {project.get('primary_language', '未知')}

## 一句话介绍

{project.get('description', '暂无介绍')}

## 核心数据

| 指标 | 数值 |
|------|------|
| Stars | {project.get('stars', 0)} |
| 今日新增 | {project.get('daily_stars', 0)} |
| Forks | {project.get('forks', 0)} |
| 综合评分 | {project.get('score', 0)} |
| 推荐指数 | {"★" * max(1, min(5, int(project.get('score', 0) / 20)))} |

## 主要标签

{', '.join(project.get('tags', []))}

## 快速判断

- ✅ 安装成功: {'是' if project.get('install_success', False) else '否'}
- ✅ 运行成功: {'是' if project.get('run_success', False) else '否'}
- ✅ Demo成功: {'是' if project.get('demo_success', False) else '否'}

## 适合谁

{', '.join(project.get('target_audience', []))}

## 主要用途

"""
        
        for uc in project.get('use_cases', []):
            content += f"- {uc}\n"
        
        content += f"""
## 技术栈

- 语言: {project.get('primary_language', '')}
- 框架: {', '.join(project.get('frameworks', [])) or '暂无'}
- 部署: {', '.join(project.get('deployment_methods', [])) or '未知'}

---

*本摘要由 AI 自动生成，快速了解项目全貌。*
"""
        
        with open(proj_dir / 'Summary.md', 'w', encoding='utf-8') as f:
            f.write(content)
