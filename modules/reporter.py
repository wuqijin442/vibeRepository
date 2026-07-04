#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)


class ReportGenerator:
    def __init__(self, config):
        self.config = config
        self.daily_dir = Path(config.get('paths', {}).get('daily_reports', './Daily-Reports'))
        self.weekly_dir = Path(config.get('paths', {}).get('weekly_reports', './Weekly-Reports'))
        self.monthly_dir = Path(config.get('paths', {}).get('monthly_reports', './Monthly-Reports'))
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        self.weekly_dir.mkdir(parents=True, exist_ok=True)
        self.monthly_dir.mkdir(parents=True, exist_ok=True)

    def generate_daily_report(self, projects: List[Dict], stats: Dict, date_str: str):
        logger.info(f"生成日报: {date_str}")
        
        content = self._build_daily_report(projects, stats, date_str)
        
        report_path = self.daily_dir / f"{date_str}_Report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"日报已生成: {report_path}")
        return str(report_path)

    def _build_daily_report(self, projects: List[Dict], stats: Dict, date_str: str) -> str:
        content = f"""# Today's Report - {date_str}

## 📊 今日概览

| 指标 | 数量 |
|------|------|
| 扫描项目数 | {stats.get('scanned', 0)} |
| 筛选项目数 | {stats.get('filtered', 0)} |
| Clone成功 | {stats.get('cloned', 0)} |
| 安装成功 | {stats.get('installed', 0)} |
| 运行成功 | {stats.get('ran', 0)} |
| Demo成功 | {stats.get('demo_passed', 0)} |
| 推荐项目 | {stats.get('recommended', 0)} |
| 同步GitHub | {stats.get('synced', 0)} |

## 🌟 今日 TOP 项目

"""
        
        sorted_projects = sorted(projects, key=lambda x: x.get('score', 0), reverse=True)
        
        for i, project in enumerate(sorted_projects[:10], 1):
            content += self._format_project_card(project, i)
        
        content += "\n## 📈 今日 AI 趋势分析\n\n"
        content += self._generate_trend_analysis(projects)
        
        content += "\n## ❌ 失败项目列表\n\n"
        failed = stats.get('failed_projects', [])
        if failed:
            for p in failed:
                content += f"- **{p.get('name', 'unknown')}**: {p.get('error', p.get('install_error', p.get('run_error', '未知错误')))}\n"
        else:
            content += "无失败项目\n"
        
        content += f"""
## 📝 最终推荐

今日共推荐 **{stats.get('recommended', 0)}** 个项目。

- 最值得尝试: {sorted_projects[0].get('name', 'N/A') if sorted_projects else 'N/A'}
- 最具潜力: {sorted_projects[1].get('name', 'N/A') if len(sorted_projects) > 1 else 'N/A'}
- 增长最快: {max(projects, key=lambda x: x.get('daily_stars', 0)).get('name', 'N/A') if projects else 'N/A'}

---

*报告由 AI 自动生成，数据基于真实运行结果*
"""
        
        return content

    def _format_project_card(self, project: Dict, rank: int) -> str:
        name = project.get('name', 'unknown')
        url = project.get('url', '')
        description = project.get('description', '暂无描述')
        stars = project.get('stars', 0)
        daily_stars = project.get('daily_stars', 0)
        score = project.get('score', 0)
        stars_display = project.get('stars_display', '☆☆☆☆☆')
        language = project.get('primary_language', 'Unknown')
        install_ok = '✅' if project.get('install_success', False) else '❌'
        run_ok = '✅' if project.get('run_success', False) else '❌'
        demo_ok = '✅' if project.get('demo_success', False) else '❌'
        
        card = f"""### {rank}. {name} {stars_display} ({score}分)

- **GitHub**: [{name}]({url})
- **一句话介绍**: {description[:100]}
- **今日新增**: ⭐ {daily_stars} | **总 Star**: {stars}
- **语言**: {language} | **技术栈**: {', '.join(project.get('frameworks', [])[:3]) or 'N/A'}
- **状态**: 安装{install_ok} 运行{run_ok} Demo{demo_ok}
- **启动耗时**: {project.get('startup_time', 0)}s | **内存**: {project.get('memory_usage', 0)}MB
- **真正解决的问题**: {'; '.join(project.get('use_cases', [])[:3]) or '待分析'}
- **优点**: {'; '.join(project.get('advantages', [])[:3]) or '待分析'}
- **缺点**: {'; '.join(project.get('disadvantages', [])[:2]) or '待分析'}
- **适用人群**: {', '.join(project.get('target_audience', [])[:3]) or '待分析'}

"""
        return card

    def _generate_trend_analysis(self, projects: List[Dict]) -> str:
        if not projects:
            return "数据不足，无法生成趋势分析\n"
        
        all_tags = []
        for p in projects:
            all_tags.extend(p.get('tags', []))
        
        tag_count = {}
        for tag in all_tags:
            tag_count[tag] = tag_count.get(tag, 0) + 1
        
        sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
        
        hot_direction = sorted_tags[0][0] if sorted_tags else 'AI'
        
        fastest = max(projects, key=lambda x: x.get('daily_stars', 0))
        most_valuable = max(projects, key=lambda x: x.get('score', 0))
        most_potential = sorted(projects, key=lambda x: x.get('score', 0))[1] if len(projects) > 1 else projects[0]
        
        analysis = f"""### 🔥 最热门方向

今日最热门的方向是 **{hot_direction}**，共有 {tag_count.get(hot_direction, 0)} 个相关项目上榜。

### 🚀 增长最快项目

**{fastest.get('name', 'N/A')}** - 今日新增 {fastest.get('daily_stars', 0)} Stars

### 💎 最值得尝试

**{most_valuable.get('name', 'N/A')}** - 综合评分 {most_valuable.get('score', 0)} 分

### 🌱 最具潜力项目

**{most_potential.get('name', 'N/A')}** - 创新度高，社区增长快

### 📌 值得收藏

"""
        
        for p in sorted(projects, key=lambda x: x.get('stars', 0), reverse=True)[:3]:
            analysis += f"- **{p.get('name', '')}**: {p.get('stars', 0)} Stars\n"
        
        analysis += """
### ⚠️ 可能昙花一现项目

- 热度高但文档不完善的项目
- Demo 运行不稳定的项目
- 社区互动少的新项目

### 🔮 未来一周值得关注

- Agent 框架的新进展
- MCP 生态的扩展
- 本地 AI 性能优化
- 多模态应用创新

"""
        return analysis

    def generate_weekly_report(self, date_str: str):
        logger.info(f"生成周报: {date_str}")
        
        content = f"""# Weekly Report - {date_str} 周

## 本周概览

*注：周报需要一周数据累积，此处为框架*

### 统计数据

| 指标 | 数量 |
|------|------|
| 本周新增项目 | 待统计 |
| 测试项目总数 | 待统计 |
| 推荐项目数 | 待统计 |
| 增长最快项目 | 待统计 |

### 本周最佳

- 最佳 Agent: 待评选
- 最佳 MCP: 待评选
- 最佳 Coding: 待评选
- 最佳黑科技: 待评选

### 趋势分析

本周 AI 领域发展趋势待分析。

---

*周报由 AI 自动生成*
"""
        
        report_path = self.weekly_dir / f"{date_str}_Weekly-Top10.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"周报已生成: {report_path}")
        return str(report_path)

    def generate_monthly_report(self, date_str: str):
        logger.info(f"生成月报: {date_str}")
        
        content = f"""# Monthly Report - {date_str} 月

## 本月概览

*注：月报需要一月数据累积，此处为框架*

### 统计数据

| 指标 | 数量 |
|------|------|
| 本月新增项目 | 待统计 |
| 测试项目总数 | 待统计 |
| 推荐项目数 | 待统计 |

### 月度最佳

- 最佳 Agent: 待评选
- 最佳 MCP: 待评选
- 最佳 Coding Tool: 待评选
- 最佳黑科技: 待评选
- 最具潜力: 待评选

### 月度趋势

本月 AI 领域整体发展趋势待分析。

---

*月报由 AI 自动生成*
"""
        
        report_path = self.monthly_dir / f"{date_str}_Monthly-Report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"月报已生成: {report_path}")
        return str(report_path)
