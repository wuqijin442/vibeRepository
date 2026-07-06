#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import os
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
        self.kb_dir = Path(config.get('paths', {}).get('knowledge_base', './Knowledge-Base'))
        self.daily_dir.mkdir(parents=True, exist_ok=True)
        self.weekly_dir.mkdir(parents=True, exist_ok=True)
        self.monthly_dir.mkdir(parents=True, exist_ok=True)

    def generate_daily_report(self, projects: List[Dict], stats: Dict, date_str: str, failure_handler=None):
        logger.info(f"生成日报: {date_str}")
        
        content = self._build_daily_report(projects, stats, date_str, failure_handler)
        
        report_path = self.daily_dir / f"{date_str}_Report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"日报已生成: {report_path}")
        return str(report_path)

    def _build_daily_report(self, projects: List[Dict], stats: Dict, date_str: str, failure_handler=None) -> str:
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
        
        if failure_handler:
            failure_summary = failure_handler.generate_failure_report()
            content += "\n" + failure_summary + "\n"
        
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
        
        weekly_data = self._collect_weekly_data(date_str)
        content = self._build_weekly_report(weekly_data, date_str)
        
        report_path = self.weekly_dir / f"{date_str}_Weekly-Top10.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"周报已生成: {report_path}")
        return str(report_path)
    
    def _collect_weekly_data(self, date_str: str) -> Dict:
        data = {
            'daily_reports': [],
            'total_scanned': 0,
            'total_filtered': 0,
            'total_cloned': 0,
            'total_installed': 0,
            'total_ran': 0,
            'total_demo_passed': 0,
            'total_recommended': 0,
            'all_projects': [],
            'kb_projects': []
        }
        
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d')
            week_start = report_date - timedelta(days=report_date.weekday())
            
            for i in range(7):
                day = week_start + timedelta(days=i)
                day_str = day.strftime('%Y-%m-%d')
                report_file = self.daily_dir / f"{day_str}_Report.md"
                
                if report_file.exists():
                    daily_stats = self._parse_daily_report(report_file)
                    data['daily_reports'].append({
                        'date': day_str,
                        'stats': daily_stats
                    })
                    data['total_scanned'] += daily_stats.get('scanned', 0)
                    data['total_filtered'] += daily_stats.get('filtered', 0)
                    data['total_cloned'] += daily_stats.get('cloned', 0)
                    data['total_installed'] += daily_stats.get('installed', 0)
                    data['total_ran'] += daily_stats.get('ran', 0)
                    data['total_demo_passed'] += daily_stats.get('demo_passed', 0)
                    data['total_recommended'] += daily_stats.get('recommended', 0)
        except Exception as e:
            logger.error(f"收集周报数据失败: {e}")
        
        data['kb_projects'] = self._get_kb_projects()
        
        return data
    
    def _parse_daily_report(self, report_path: Path) -> Dict:
        stats = {}
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            import re
            patterns = {
                'scanned': r'扫描项目数\s*\|\s*(\d+)',
                'filtered': r'筛选项目数\s*\|\s*(\d+)',
                'cloned': r'Clone成功\s*\|\s*(\d+)',
                'installed': r'安装成功\s*\|\s*(\d+)',
                'ran': r'运行成功\s*\|\s*(\d+)',
                'demo_passed': r'Demo成功\s*\|\s*(\d+)',
                'recommended': r'推荐项目\s*\|\s*(\d+)',
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content)
                if match:
                    stats[key] = int(match.group(1))
        except Exception as e:
            logger.debug(f"解析日报失败 {report_path}: {e}")
        
        return stats
    
    def _get_kb_projects(self) -> List[Dict]:
        projects = []
        try:
            if self.kb_dir.exists():
                for cat_dir in self.kb_dir.iterdir():
                    if cat_dir.is_dir():
                        for proj_dir in cat_dir.iterdir():
                            meta_file = proj_dir / 'project.json'
                            if meta_file.exists():
                                with open(meta_file, 'r', encoding='utf-8') as f:
                                    projects.append(json.load(f))
        except Exception as e:
            logger.error(f"获取知识库项目失败: {e}")
        return projects
    
    def _build_weekly_report(self, data: Dict, date_str: str) -> str:
        kb_projects = data.get('kb_projects', [])
        daily_reports = data.get('daily_reports', [])
        
        best_agent = self._find_best_by_category(kb_projects, 'Agents')
        best_mcp = self._find_best_by_category(kb_projects, 'MCP')
        best_coding = self._find_best_by_category(kb_projects, 'Coding')
        fastest_growing = max(kb_projects, key=lambda x: x.get('daily_stars', 0)) if kb_projects else None
        
        content = f"""# Weekly Report - {date_str} 周

## 📊 本周概览

### 统计数据

| 指标 | 数量 |
|------|------|
| 本周扫描项目总数 | {data.get('total_scanned', 0)} |
| 本周筛选项目数 | {data.get('total_filtered', 0)} |
| 本周测试项目总数 | {data.get('total_cloned', 0)} |
| 安装成功 | {data.get('total_installed', 0)} |
| 运行成功 | {data.get('total_ran', 0)} |
| Demo通过 | {data.get('total_demo_passed', 0)} |
| 推荐项目数 | {data.get('total_recommended', 0)} |
| 知识库项目总数 | {len(kb_projects)} |

### 每日数据

| 日期 | 扫描 | 筛选 | 推荐 |
|------|------|------|------|
"""
        
        for daily in daily_reports:
            stats = daily.get('stats', {})
            content += f"| {daily.get('date', '')} | {stats.get('scanned', 0)} | {stats.get('filtered', 0)} | {stats.get('recommended', 0)} |\n"
        
        content += f"""
## 🏆 本周最佳

### 最佳 Agent
{best_agent.get('name', '待评选') if best_agent else '待评选'} - {best_agent.get('score', 0)} 分

### 最佳 MCP
{best_mcp.get('name', '待评选') if best_mcp else '待评选'} - {best_mcp.get('score', 0)} 分

### 最佳 Coding Tool
{best_coding.get('name', '待评选') if best_coding else '待评选'} - {best_coding.get('score', 0)} 分

### 增长最快
{fastest_growing.get('name', '待评选') if fastest_growing else '待评选'} - 本周新增 {fastest_growing.get('daily_stars', 0)} Stars

### 最佳黑科技
{self._find_best_black_tech(kb_projects)}

## 📈 本周趋势分析

### 热门方向
{self._analyze_weekly_trends(kb_projects)}

### 值得关注
"""
        
        top_projects = sorted(kb_projects, key=lambda x: x.get('score', 0), reverse=True)[:5]
        for i, p in enumerate(top_projects, 1):
            content += f"{i}. **{p.get('name', 'N/A')}** - {p.get('score', 0)} 分, {p.get('stars', 0)} Stars\n"
        
        content += f"""
## 📁 知识库分类统计

{self._generate_category_stats(kb_projects)}

---

*周报由 AI 自动生成，基于 {len(daily_reports)} 天的日报数据*
"""
        return content
    
    def _find_best_by_category(self, projects: List[Dict], category: str) -> Dict:
        cat_projects = [p for p in projects if p.get('category') == category]
        if cat_projects:
            return max(cat_projects, key=lambda x: x.get('score', 0))
        return {}
    
    def _find_best_black_tech(self, projects: List[Dict]) -> str:
        black_tech_tags = ['Image Gen', 'Video Gen', 'Voice', 'Browser Use', 'Computer Use']
        black_tech = [p for p in projects if any(tag in p.get('tags', []) for tag in black_tech_tags)]
        if black_tech:
            best = max(black_tech, key=lambda x: x.get('score', 0))
            return f"{best.get('name', 'N/A')} - {best.get('score', 0)} 分"
        return '待评选'
    
    def _analyze_weekly_trends(self, projects: List[Dict]) -> str:
        if not projects:
            return "数据不足，暂无法分析趋势"
        
        tag_count = {}
        for p in projects:
            for tag in p.get('tags', []):
                tag_count[tag] = tag_count.get(tag, 0) + 1
        
        sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
        top_tags = sorted_tags[:3]
        
        trends = "本周最热门的技术方向：\n"
        for tag, count in top_tags:
            trends += f"- **{tag}**: {count} 个项目\n"
        
        return trends
    
    def _generate_category_stats(self, projects: List[Dict]) -> str:
        cat_count = {}
        for p in projects:
            cat = p.get('category', 'Others')
            cat_count[cat] = cat_count.get(cat, 0) + 1
        
        stats = "| 分类 | 项目数 |\n|------|--------|\n"
        for cat, count in sorted(cat_count.items(), key=lambda x: x[1], reverse=True):
            stats += f"| {cat} | {count} |\n"
        
        return stats

    def generate_monthly_report(self, date_str: str):
        logger.info(f"生成月报: {date_str}")
        
        monthly_data = self._collect_monthly_data(date_str)
        content = self._build_monthly_report(monthly_data, date_str)
        
        report_path = self.monthly_dir / f"{date_str}_Monthly-Report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"月报已生成: {report_path}")
        return str(report_path)
    
    def _collect_monthly_data(self, date_str: str) -> Dict:
        data = {
            'total_scanned': 0,
            'total_filtered': 0,
            'total_cloned': 0,
            'total_installed': 0,
            'total_ran': 0,
            'total_demo_passed': 0,
            'total_recommended': 0,
            'new_projects_this_month': 0,
            'kb_projects': []
        }
        
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d')
            month_start = report_date.replace(day=1)
            
            for day in range(1, report_date.day + 1):
                day_date = month_start.replace(day=day)
                day_str = day_date.strftime('%Y-%m-%d')
                report_file = self.daily_dir / f"{day_str}_Report.md"
                
                if report_file.exists():
                    daily_stats = self._parse_daily_report(report_file)
                    data['total_scanned'] += daily_stats.get('scanned', 0)
                    data['total_filtered'] += daily_stats.get('filtered', 0)
                    data['total_cloned'] += daily_stats.get('cloned', 0)
                    data['total_installed'] += daily_stats.get('installed', 0)
                    data['total_ran'] += daily_stats.get('ran', 0)
                    data['total_demo_passed'] += daily_stats.get('demo_passed', 0)
                    data['total_recommended'] += daily_stats.get('recommended', 0)
        except Exception as e:
            logger.error(f"收集月报数据失败: {e}")
        
        data['kb_projects'] = self._get_kb_projects()
        data['new_projects_this_month'] = len(data['kb_projects'])
        
        return data
    
    def _build_monthly_report(self, data: Dict, date_str: str) -> str:
        kb_projects = data.get('kb_projects', [])
        
        content = f"""# Monthly Report - {date_str} 月

## 📊 本月概览

### 统计数据

| 指标 | 数量 |
|------|------|
| 本月扫描项目总数 | {data.get('total_scanned', 0)} |
| 本月筛选项目数 | {data.get('total_filtered', 0)} |
| 本月测试项目总数 | {data.get('total_cloned', 0)} |
| 安装成功 | {data.get('total_installed', 0)} |
| 运行成功 | {data.get('total_ran', 0)} |
| Demo通过 | {data.get('total_demo_passed', 0)} |
| 本月新增推荐 | {data.get('total_recommended', 0)} |
| 知识库项目总数 | {len(kb_projects)} |

## 🏆 月度最佳

### 最佳 Agent
{self._find_best_by_category(kb_projects, 'Agents').get('name', '待评选')}

### 最佳 MCP
{self._find_best_by_category(kb_projects, 'MCP').get('name', '待评选')}

### 最佳 Coding Tool
{self._find_best_by_category(kb_projects, 'Coding').get('name', '待评选')}

### 最佳黑科技
{self._find_best_black_tech(kb_projects)}

### 最具潜力
{self._find_most_potential(kb_projects)}

## 📈 月度趋势

{self._analyze_weekly_trends(kb_projects)}

## 📁 知识库分类统计

{self._generate_category_stats(kb_projects)}

---

*月报由 AI 自动生成*
"""
        return content
    
    def _find_most_potential(self, projects: List[Dict]) -> str:
        if len(projects) < 2:
            return '待评选'
        sorted_by_growth = sorted(projects, key=lambda x: x.get('daily_stars', 0), reverse=True)
        if len(sorted_by_growth) >= 2:
            return sorted_by_growth[1].get('name', '待评选')
        return '待评选'
