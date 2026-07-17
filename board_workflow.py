#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
板块 Top5 真实测试工作流
参考 gitcn.org/top 板块分类，对每个热门板块的 top5 项目进行真实测试
额外增加：黑科技工具、大模型训练、学习网站 三个精品板块
复用现有 modules，不影响每日 TOP5 工作流
"""

import os
import re
import sys
import json
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import requests
import yaml

from modules.analyzer import ProjectAnalyzer
from modules.installer import ProjectInstaller
from modules.runner import ProjectRunner
from modules.tester import ProjectTester
from modules.screenshot import ScreenshotTaker
from modules.performance import PerformanceAnalyzer
from modules.competitor import CompetitorAnalyzer
from modules.documenter import DocumentGenerator
from modules.architect import ArchitectureGenerator
from modules.scoring import ProjectScorer
from modules.failure_handler import FailureHandler

Path('workspace/logs').mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'workspace/logs/board_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# 11 个板块定义（8 核心 + 3 精品）
# 每个板块用 GitHub Search API 关键词采集，按 star 排序取 top，评分筛选后测 top5
BOARDS = [
    # ===== 8 个核心板块（参考 gitcn.org 分类） =====
    {
        'id': 'frontend',
        'name': '前端开发',
        'name_en': 'Frontend',
        'keywords': ['frontend framework', 'react ui component', 'vue admin', 'frontend build tool'],
        'min_stars': 5000,
        'category': '核心板块',
    },
    {
        'id': 'backend',
        'name': '后端开发',
        'name_en': 'Backend',
        'keywords': ['backend framework', 'web server framework', 'api gateway', 'microservice'],
        'min_stars': 5000,
        'category': '核心板块',
    },
    {
        'id': 'database',
        'name': '数据库',
        'name_en': 'Database',
        'keywords': ['database', 'sqlite alternative', 'vector database', 'redis alternative'],
        'min_stars': 5000,
        'category': '核心板块',
    },
    {
        'id': 'automation',
        'name': '自动化',
        'name_en': 'Automation',
        'keywords': ['workflow automation', 'task scheduler', 'rpa', 'n8n workflow'],
        'min_stars': 3000,
        'category': '核心板块',
    },
    {
        'id': 'self-hosting',
        'name': '自托管服务',
        'name_en': 'Self-Hosting',
        'keywords': ['self-hosted', 'homelab', 'self-hosted dashboard', 'self-hosted app'],
        'min_stars': 5000,
        'category': '核心板块',
    },
    {
        'id': 'devtools',
        'name': '开发工具',
        'name_en': 'DevTools',
        'keywords': ['developer tool', 'cli tool', 'git tool', 'terminal tool'],
        'min_stars': 5000,
        'category': '核心板块',
    },
    {
        'id': 'security',
        'name': '安全',
        'name_en': 'Security',
        'keywords': ['security tool', 'pentest tool', 'vulnerability scanner', 'ctf tool'],
        'min_stars': 3000,
        'category': '核心板块',
    },
    {
        'id': 'editor',
        'name': '编辑器',
        'name_en': 'Editor',
        'keywords': ['text editor', 'code editor', 'note app', 'markdown editor'],
        'min_stars': 5000,
        'category': '核心板块',
    },
    # ===== 3 个精品板块（用户额外要求） =====
    {
        'id': 'black-tech',
        'name': '黑科技工具',
        'name_en': 'BlackTech',
        'keywords': ['browser use agent', 'computer use agent', 'screen control', 'desktop automation agent'],
        'min_stars': 1000,
        'category': '精品板块',
    },
    {
        'id': 'llm-training',
        'name': '大模型训练',
        'name_en': 'LLM-Training',
        'keywords': ['llm training framework', 'llm fine-tuning', 'rlhf alignment', 'distributed training'],
        'min_stars': 2000,
        'category': '精品板块',
    },
    {
        'id': 'learning',
        'name': '学习网站',
        'name_en': 'Learning',
        'keywords': ['learn to code', 'coding interview', 'computer science course', 'programming tutorial'],
        'min_stars': 10000,
        'category': '精品板块',
    },
]


def extract_token() -> str:
    """从环境变量或本地 git remote 提取 GitHub token"""
    token = os.environ.get('GITHUB_TOKEN', '').strip()
    if token:
        return token
    try:
        r = subprocess.run(['git', 'remote', 'get-url', 'origin'],
                           capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            m = re.search(r'https://[^:/@]+:([^/@]+)@', r.stdout.strip())
            if m:
                return m.group(1)
    except Exception:
        pass
    return ''


class BoardCollector:
    """按板块用 GitHub Search API 采集 top 项目"""

    def __init__(self, token: str):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'application/vnd.github+json',
        })
        if token:
            self.session.headers['Authorization'] = f'token {token}'
        self.token = token

    def collect_board(self, board: Dict, top_n: int = 10) -> List[Dict]:
        """采集单个板块的候选项目（取 top_n 候选供后续筛选）"""
        candidates = []
        seen = set()
        for kw in board['keywords']:
            try:
                url = "https://api.github.com/search/repositories"
                params = {
                    'q': f'{kw} stars:>{board["min_stars"]} pushed:>2024-06-01',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 20,
                }
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code == 403:
                    logger.warning(f"GitHub API 限速，等待 30s")
                    time.sleep(30)
                    continue
                data = resp.json()
                for item in data.get('items', []):
                    full_name = item.get('full_name', '')
                    if not full_name or full_name in seen:
                        continue
                    seen.add(full_name)
                    candidates.append({
                        'name': full_name,
                        'url': item.get('html_url', ''),
                        'description': item.get('description', '') or '',
                        'stars': item.get('stargazers_count', 0),
                        'daily_stars': 0,
                        'forks': item.get('forks_count', 0),
                        'language': item.get('language', '') or '',
                        'author': item.get('owner', {}).get('login', ''),
                        'license': (item.get('license') or {}).get('name', ''),
                        'topics': item.get('topics', []) or [],
                        'updated_at': item.get('updated_at', ''),
                        'open_issues': item.get('open_issues_count', 0),
                        'source': f'board_{board["id"]}',
                        'board_id': board['id'],
                        'board_name': board['name'],
                        'collected_at': datetime.now().isoformat(),
                    })
                time.sleep(2)
            except Exception as e:
                logger.error(f"板块 {board['id']} 关键词 '{kw}' 采集失败: {e}")
                continue
        # 按 star 排序取候选
        candidates.sort(key=lambda x: x.get('stars', 0), reverse=True)
        return candidates[:top_n]


def quick_score(project: Dict) -> float:
    """快速评分用于筛选（star + 活跃度 + 文档完整度近似）"""
    stars = project.get('stars', 0)
    forks = project.get('forks', 0)
    issues = project.get('open_issues', 0)
    desc_len = len(project.get('description', ''))
    topics = len(project.get('topics', []))
    # 归一化
    s_score = min(stars / 50000, 1.0) * 40
    f_score = min(forks / 5000, 1.0) * 20
    a_score = min(issues / 500, 1.0) * 15
    d_score = min(desc_len / 200, 1.0) * 15
    t_score = min(topics / 10, 1.0) * 10
    return round(s_score + f_score + a_score + d_score + t_score, 1)


def filter_blacklist(project: Dict) -> bool:
    """过滤 awesome/tutorial/learning 等纯列表项目（学习板块除外）"""
    name_lower = project.get('name', '').lower()
    desc_lower = project.get('description', '').lower()
    blacklist = ['awesome', 'tutorial', 'cheatsheet', 'interview', 'course']
    # 学习板块保留 interview/course 类
    if project.get('board_id') == 'learning':
        blacklist = ['awesome']
    for w in blacklist:
        if w in name_lower or w in desc_lower:
            return False
    return True


class BoardWorkflow:
    def __init__(self, config_path='config.yaml'):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.token = extract_token()

        # 复用现有 modules
        self.analyzer = ProjectAnalyzer(self.config)
        self.installer = ProjectInstaller(self.config)
        self.runner = ProjectRunner(self.config)
        self.tester = ProjectTester(self.config)
        self.screenshot_taker = ScreenshotTaker(self.config)
        self.perf_analyzer = PerformanceAnalyzer(self.config)
        self.competitor_analyzer = CompetitorAnalyzer(self.config)
        self.documenter = DocumentGenerator(self.config)
        self.architect = ArchitectureGenerator(self.config)
        self.scorer = ProjectScorer(self.config)
        self.failure_handler = FailureHandler(self.config)

        self.collector = BoardCollector(self.token)
        self.boards_dir = Path('Boards-Reports')
        self.boards_dir.mkdir(parents=True, exist_ok=True)

    def run(self):
        logger.info("=" * 60)
        logger.info(f"板块 Top5 真实测试工作流启动 - {self.today}")
        logger.info(f"共 {len(BOARDS)} 个板块（8 核心 + 3 精品）")
        logger.info("=" * 60)

        all_board_results = []
        for idx, board in enumerate(BOARDS, 1):
            logger.info(f"\n[{idx}/{len(BOARDS)}] 板块: {board['name']} ({board['id']})")
            try:
                result = self._process_board(board)
                all_board_results.append(result)
            except Exception as e:
                logger.error(f"板块 {board['id']} 处理失败: {e}", exc_info=True)
                all_board_results.append({
                    'board': board,
                    'projects': [],
                    'stats': {'collected': 0, 'tested': 0, 'install_ok': 0, 'run_ok': 0, 'demo_ok': 0},
                    'error': str(e),
                })

        self._generate_summary(all_board_results)

        # 同步到 GitHub（wuqijin442 账号 → main 分支）
        try:
            self._sync_to_github(all_board_results)
        except Exception as e:
            logger.error(f"GitHub 同步失败: {e}", exc_info=True)

        logger.info("=" * 60)
        logger.info("板块测试工作流执行完成！")
        logger.info(f"汇总报告: {self.boards_dir / f'{self.today}_Boards-Summary.md'}")
        logger.info("=" * 60)

    def _sync_to_github(self, all_results: List[Dict]):
        """将板块报告同步到 GitHub main 分支（账号 wuqijin442，禁止 traeagent）"""
        logger.info("开始同步板块报告到 GitHub...")
        git_dir = Path('.')

        # 1. git add（仅板块报告 + README + 脚本，排除 workspace/clones 等运行时产物）
        add_targets = ['Boards-Reports/', 'README.md', 'board_workflow.py']
        for target in add_targets:
            if Path(target).exists():
                subprocess.run(['git', 'add', target],
                               cwd=str(git_dir), capture_output=True, text=True, timeout=60)

        # 2. 检查是否有待提交内容
        status = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'],
                                cwd=str(git_dir), capture_output=True, text=True, timeout=30)
        staged = [l for l in status.stdout.splitlines()
                  if l.startswith(('A', 'M', 'D', 'R')) and 'workspace/clones' not in l]
        if not staged:
            logger.info("无新增板块报告需要提交")
            return

        # 3. commit（强制 wuqijin442 账号）
        total_tested = sum(r['stats']['tested'] for r in all_results)
        total_run = sum(r['stats']['run_ok'] for r in all_results)
        commit_msg = (
            f"[{self.today}] Daily Boards Top5 Update\n\n"
            f"板块测试: {len(all_results)} 板块 × top5 = {total_tested} 项目, "
            f"运行成功 {total_run}\n"
            f"8 核心板块 + 3 精品板块（黑科技/大模型训练/学习网站）"
        )
        commit = subprocess.run(
            ['git', '-c', 'user.name=wuqijin442',
             '-c', 'user.email=wuqijin442@users.noreply.github.com',
             'commit', '-m', commit_msg],
            cwd=str(git_dir), capture_output=True, text=True, timeout=60
        )
        if commit.returncode != 0:
            logger.warning(f"提交失败: {commit.stderr}")
            return

        # 4. push 到 main
        push = subprocess.run(['git', 'push', 'origin', 'main'],
                              cwd=str(git_dir), capture_output=True, text=True, timeout=120)
        if push.returncode == 0:
            logger.info(f"板块报告已推送到 GitHub main 分支（账号 wuqijin442）")
        else:
            logger.error(f"推送失败: {push.stderr}")

    def _process_board(self, board: Dict) -> Dict:
        """处理单个板块：采集 → 筛选 → 测试 top5 → 生成报告"""
        stats = {'collected': 0, 'tested': 0, 'install_ok': 0, 'run_ok': 0, 'demo_ok': 0, 'recommended': 0}
        # 采集候选
        candidates = self.collector.collect_board(board, top_n=15)
        stats['collected'] = len(candidates)
        logger.info(f"  采集候选 {len(candidates)} 个")

        # 过滤 + 快速评分筛选
        filtered = [p for p in candidates if filter_blacklist(p)]
        for p in filtered:
            p['quick_score'] = quick_score(p)
        filtered.sort(key=lambda x: x['quick_score'], reverse=True)
        top5 = filtered[:5]
        logger.info(f"  筛选后 top5: {[p['name'] for p in top5]}")

        # 真实测试每个项目
        tested = []
        for project in top5:
            try:
                result = self._test_project(project, board)
                tested.append(result)
                stats['tested'] += 1
                if result.get('install_success'):
                    stats['install_ok'] += 1
                if result.get('run_success'):
                    stats['run_ok'] += 1
                if result.get('demo_success'):
                    stats['demo_ok'] += 1
                if result.get('score', 0) >= 90 and result.get('stars_count', 0) >= 4:
                    stats['recommended'] += 1
            except Exception as e:
                logger.error(f"  测试 {project.get('name')} 失败: {e}")
                project['test_error'] = str(e)
                tested.append(project)
                self.failure_handler.record_failure(
                    project.get('name', 'unknown'), 'board_test', e,
                    suggestion='检查项目依赖与运行环境'
                )

        # 生成板块报告
        self._generate_board_report(board, tested, stats)
        return {'board': board, 'projects': tested, 'stats': stats}

    def _test_project(self, project: Dict, board: Dict) -> Dict:
        """复用现有 modules 测试单个项目"""
        name = project.get('name', 'unknown')
        logger.info(f"  -> 测试: {name}")

        # 1. 分析(Clone)
        result = self.analyzer.analyze(project)
        if not result.get('cloned', False):
            logger.warning(f"  Clone 失败: {name}")
            return result

        # 2. 安装
        result = self.installer.install(result)
        # 3. 运行
        if result.get('install_success', False):
            result = self.runner.run(result)
        # 4. 测试
        if result.get('run_success', False):
            result = self.tester.test(result)
        # 5. 截图
        try:
            result = self.screenshot_taker.take_screenshots(result)
        except Exception as e:
            logger.debug(f"截图失败: {e}")
        # 6. 性能
        try:
            result = self.perf_analyzer.analyze(result)
        except Exception as e:
            logger.debug(f"性能分析失败: {e}")
        # 7. 竞品
        try:
            result = self.competitor_analyzer.analyze(result)
        except Exception as e:
            logger.debug(f"竞品分析失败: {e}")
        # 8. 文档
        try:
            result = self.documenter.generate(result)
        except Exception as e:
            logger.debug(f"文档生成失败: {e}")
        # 9. 架构图
        try:
            result = self.architect.generate(result)
        except Exception as e:
            logger.debug(f"架构图失败: {e}")
        # 10. 评分
        result = self.scorer.score(result)

        # 标记板块归属
        result['board_id'] = board['id']
        result['board_name'] = board['name']
        logger.info(f"  完成: {name} | 安装:{result.get('install_success', False)} "
                    f"运行:{result.get('run_success', False)} "
                    f"Demo:{result.get('demo_success', False)} "
                    f"评分:{result.get('score', 0)}")
        return result

    def _generate_board_report(self, board: Dict, projects: List[Dict], stats: Dict):
        """生成单个板块报告"""
        board_dir = self.boards_dir / board['id']
        board_dir.mkdir(parents=True, exist_ok=True)

        sorted_projects = sorted(projects, key=lambda x: x.get('score', 0), reverse=True)
        content = f"""# {board['name']} 板块 Top5 测试报告 - {self.today}

> 板块类型: {board['category']} | 参考来源: gitcn.org/top 分类

## 📊 板块概览

| 指标 | 数量 |
|------|------|
| 采集候选数 | {stats['collected']} |
| 真实测试数 | {stats['tested']} |
| 安装成功 | {stats['install_ok']} |
| 运行成功 | {stats['run_ok']} |
| Demo成功 | {stats['demo_ok']} |
| 推荐项目(≥90分) | {stats['recommended']} |

## 🏆 板块 Top5 项目

"""
        for i, p in enumerate(sorted_projects[:5], 1):
            content += self._format_project(p, i)

        content += f"""
## 📈 板块趋势

- 板块热度: {'🔥 高' if stats['collected'] >= 10 else '⚡ 中'}
- 可运行比例: {stats['run_ok']}/{stats['tested']}
- 最佳项目: {sorted_projects[0].get('name', 'N/A') if sorted_projects else 'N/A'}

---

*报告由板块测试工作流自动生成，数据基于真实运行结果*
"""
        report_path = board_dir / f"{self.today}_Report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"  板块报告已生成: {report_path}")

    def _format_project(self, p: Dict, rank: int) -> str:
        name = p.get('name', 'unknown')
        url = p.get('url', '')
        desc = p.get('description', '暂无描述')[:100]
        stars = p.get('stars', 0)
        score = p.get('score', 0)
        stars_display = p.get('stars_display', '☆☆☆☆☆')
        lang = p.get('primary_language') or p.get('language', 'Unknown')
        install_ok = '✅' if p.get('install_success', False) else '❌'
        run_ok = '✅' if p.get('run_success', False) else '❌'
        demo_ok = '✅' if p.get('demo_success', False) else '❌'
        startup = p.get('startup_time', 0)
        mem = p.get('memory_usage', 0)
        frameworks = ', '.join(p.get('frameworks', [])[:3]) or 'N/A'
        advantages = '; '.join(p.get('advantages', [])[:3]) or '待分析'
        disadvantages = '; '.join(p.get('disadvantages', [])[:2]) or '待分析'
        use_cases = '; '.join(p.get('use_cases', [])[:3]) or '待分析'
        audience = ', '.join(p.get('target_audience', [])[:3]) or '待分析'
        return f"""### {rank}. {name} {stars_display} ({score}分)

- **GitHub**: [{name}]({url})
- **一句话介绍**: {desc}
- **总 Star**: {stars} | **语言**: {lang}
- **技术栈**: {frameworks}
- **状态**: 安装{install_ok} 运行{run_ok} Demo{demo_ok}
- **启动耗时**: {startup}s | **内存**: {mem}MB
- **真正解决的问题**: {use_cases}
- **优点**: {advantages}
- **缺点**: {disadvantages}
- **适用人群**: {audience}

"""

    def _generate_summary(self, all_results: List[Dict]):
        """生成所有板块汇总报告"""
        total_tested = sum(r['stats']['tested'] for r in all_results)
        total_install = sum(r['stats']['install_ok'] for r in all_results)
        total_run = sum(r['stats']['run_ok'] for r in all_results)
        total_demo = sum(r['stats']['demo_ok'] for r in all_results)
        total_recommended = sum(r['stats']['recommended'] for r in all_results)

        content = f"""# 板块 Top5 测试汇总报告 - {self.today}

> 参考 gitcn.org/top 板块分类，对每个热门板块 top5 项目进行真实测试
> 8 个核心板块 + 3 个精品板块（黑科技工具、大模型训练、学习网站）

## 📊 总体统计

| 指标 | 数量 |
|------|------|
| 测试板块数 | {len(all_results)} |
| 真实测试项目总数 | {total_tested} |
| 安装成功 | {total_install} |
| 运行成功 | {total_run} |
| Demo成功 | {total_demo} |
| 推荐项目(≥90分) | {total_recommended} |

## 📁 各板块报告

| 板块 | 类型 | 采集 | 测试 | 安装 | 运行 | Demo | 推荐 | 报告 |
|------|------|------|------|------|------|------|------|------|
"""
        for r in all_results:
            b = r['board']
            s = r['stats']
            report_link = f"[查看]({b['id']}/{self.today}_Report.md)"
            content += f"| {b['name']} | {b['category']} | {s['collected']} | {s['tested']} | {s['install_ok']} | {s['run_ok']} | {s['demo_ok']} | {s['recommended']} | {report_link} |\n"

        # 各板块最佳项目
        content += "\n## 🏆 各板块最佳项目\n\n"
        content += "| 板块 | 最佳项目 | 评分 | 状态 |\n|------|----------|------|------|\n"
        for r in all_results:
            b = r['board']
            projs = r.get('projects', [])
            if projs:
                best = max(projs, key=lambda x: x.get('score', 0))
                status = f"安装{'✅' if best.get('install_success') else '❌'}运行{'✅' if best.get('run_success') else '❌'}"
                content += f"| {b['name']} | [{best.get('name', 'N/A')}]({best.get('url', '#')}) | {best.get('score', 0)} | {status} |\n"
            else:
                content += f"| {b['name']} | 无 | - | - |\n"

        # 精品板块亮点
        content += "\n## ✨ 精品板块亮点\n\n"
        for r in all_results:
            b = r['board']
            if b.get('category') == '精品板块':
                projs = r.get('projects', [])
                content += f"### {b['name']}\n\n"
                if projs:
                    for p in sorted(projs, key=lambda x: x.get('score', 0), reverse=True)[:3]:
                        content += f"- **[{p.get('name', 'N/A')}]({p.get('url', '#')})** - {p.get('score', 0)}分, {p.get('stars', 0)}⭐, {p.get('description', '')[:60]}\n"
                else:
                    content += "- 暂无项目\n"
                content += "\n"

        content += f"""
## 📈 整体趋势

- 测试覆盖率: {total_tested}/{len(all_results) * 5} ({round(total_tested / (len(all_results) * 5) * 100, 1) if all_results else 0}%)
- 运行成功率: {round(total_run / total_tested * 100, 1) if total_tested else 0}%
- Demo成功率: {round(total_demo / total_tested * 100, 1) if total_tested else 0}%

## 🔮 板块洞察

- **核心板块**: 涵盖前端/后端/数据库/自动化/自托管/工具/安全/编辑器，覆盖开发者主流技术栈
- **黑科技工具**: 聚焦 browser use / computer use / 屏幕控制等前沿自动化方向
- **大模型训练**: 涵盖训练框架/微调/对齐/分布式训练，反映 LLM 训练生态
- **学习网站**: 汇总编程学习/面试/CS 课程类优质开源项目

---

*汇总报告由板块测试工作流自动生成，所有数据基于真实运行结果。最后更新: {self.today}*
"""
        summary_path = self.boards_dir / f"{self.today}_Boards-Summary.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"汇总报告已生成: {summary_path}")


def main():
    workflow = BoardWorkflow()
    workflow.run()


if __name__ == '__main__':
    main()
