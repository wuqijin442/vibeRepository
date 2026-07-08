#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import subprocess
import shutil
import os
import re
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class GitHubSyncer:
    def __init__(self, config):
        self.config = config
        sync_config = config.get('github_sync', {})
        self.enabled = sync_config.get('enabled', False)
        self.repo_url = sync_config.get('repo_url', '')
        self.branch = sync_config.get('branch', 'main')
        # 提交账号：默认使用 wuqijin442，禁止使用 traeagent
        self.author_name = sync_config.get('author_name', 'wuqijin442')
        self.author_email = sync_config.get('author_email', 'wuqijin442@users.noreply.github.com')
        self.workspace = Path(config.get('paths', {}).get('workspace', './workspace'))
        # 解析带认证的 URL（优先级：环境变量 > 本地 git remote > config）
        self.authed_repo_url = self._resolve_authed_url()
        self.local_root = Path('.')
        self.sync_dirs = [
            'Daily-Reports',
            'Weekly-Reports',
            'Monthly-Reports',
            'Awesome-Projects',
            'Knowledge-Base',
            'Benchmarks',
            'Logs',
            'Screenshots',
            'Reviews',
            'Architecture',
            'Metadata'
        ]
        self.ignore_patterns = [
            '.git',
            'node_modules',
            'venv',
            '.venv',
            '__pycache__',
            'dist',
            'build',
            'target',
            '.next',
            '.cache',
            '*.log',
            '*.env',
        ]

    def _resolve_authed_url(self) -> str:
        """解析带认证信息的仓库 URL，确保 push 不会因交互式输入失败。
        优先级：环境变量 GH_TOKEN/GITHUB_TOKEN > 本地 git remote 中已含 token 的 URL > config.repo_url
        """
        base = self.repo_url
        # 1. 环境变量 token
        token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if token and base:
            return self._inject_token(base, token, 'x-access-token')
        # 2. 从本地 git remote 读取带 token 的 URL
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                if '@github.com/' in url and '://' in url:
                    logger.info("已从本地 git remote 获取带认证的 URL")
                    return url
        except Exception as e:
            logger.debug(f"读取本地 git remote 失败: {e}")
        # 3. 回退到 config（push 可能失败）
        return base

    @staticmethod
    def _inject_token(url: str, token: str, username: str = 'x-access-token') -> str:
        """把 token 注入 https URL，形如 https://x-access-token:TOKEN@github.com/..."""
        m = re.match(r'(https?://)([^@]+@)?(.+)', url)
        if not m:
            return url
        return f"{m.group(1)}{username}:{token}@{m.group(3)}"

    def sync(self, date_str: str) -> int:
        if not self.enabled:
            logger.info("GitHub 同步已禁用")
            return 0

        logger.info(f"同步到 GitHub: {date_str}")

        try:
            repo_dir = self.workspace / 'sync_repo'

            if not (repo_dir / '.git').exists():
                self._clone_repo(repo_dir)
            else:
                self._pull_repo(repo_dir)

            # 强制设置提交账号为 wuqijin442（禁止使用 traeagent）
            self._set_git_author(repo_dir)

            # 确保 sync_repo 的 origin remote 指向带认证的 URL
            self._ensure_authed_remote(repo_dir)

            synced_files = self._copy_files(repo_dir)

            # 每次新增内容时更新仓库根 README
            readme_updated = self._update_repo_readme(repo_dir, date_str)

            if synced_files > 0 or readme_updated:
                self._commit_and_push(repo_dir, date_str)

            logger.info(f"同步完成，共 {synced_files} 个文件更新，README 更新: {readme_updated}")
            return synced_files

        except Exception as e:
            logger.error(f"GitHub 同步失败: {e}")
            return 0

    def _ensure_authed_remote(self, repo_dir: Path):
        """把 sync_repo 的 origin remote 设置为带认证的 URL，避免 push 时交互式输入失败"""
        if not self.authed_repo_url or self.authed_repo_url == self.repo_url:
            return
        try:
            subprocess.run(
                ['git', 'remote', 'set-url', 'origin', self.authed_repo_url],
                cwd=str(repo_dir), capture_output=True, text=True, timeout=10
            )
            logger.info("已更新 origin remote 为带认证的 URL")
        except Exception as e:
            logger.warning(f"设置 origin remote 失败: {e}")

    def _set_git_author(self, repo_dir: Path):
        """在仓库内设置 wuqijin442 账号，确保提交不使用 traeagent"""
        for key, val in [('user.name', self.author_name), ('user.email', self.author_email)]:
            try:
                subprocess.run(
                    ['git', 'config', key, val],
                    cwd=str(repo_dir),
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            except Exception as e:
                logger.warning(f"设置 git {key} 失败: {e}")
        logger.info(f"已设置提交账号: {self.author_name} <{self.author_email}>")

    def _clone_repo(self, repo_dir: Path):
        logger.info(f"Clone 仓库: {self.repo_url}")
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        
        result = subprocess.run(
            ['git', 'clone', '--branch', self.branch, self.repo_url, str(repo_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            raise Exception(f"Clone 失败: {result.stderr}")

    def _pull_repo(self, repo_dir: Path):
        logger.info("Pull 最新代码")
        result = subprocess.run(
            ['git', 'pull', 'origin', self.branch],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.warning(f"Pull 失败: {result.stderr}")

    def _copy_files(self, repo_dir: Path) -> int:
        count = 0
        
        for sync_dir in self.sync_dirs:
            src = Path('.') / sync_dir
            dst = repo_dir / sync_dir
            
            if not src.exists():
                continue
            
            dst.mkdir(parents=True, exist_ok=True)
            
            if src.is_dir():
                for item in src.rglob('*'):
                    if item.is_file() and not self._should_ignore(item):
                        rel_path = item.relative_to(src)
                        dst_file = dst / rel_path
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        if not dst_file.exists() or item.stat().st_mtime > dst_file.stat().st_mtime:
                            shutil.copy2(item, dst_file)
                            count += 1
        
        return count

    def _should_ignore(self, path: Path) -> bool:
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern.startswith('*.'):
                if path.name.endswith(pattern[1:]):
                    return True
            elif pattern in path.parts:
                return True
        return False

    def _update_repo_readme(self, repo_dir: Path, date_str: str) -> bool:
        """每次新增内容时同步更新仓库根 README，展示知识库统计与最近推荐项目"""
        try:
            import json as _json
            kb_root = self.local_root / 'Knowledge-Base'
            project_files = []
            if kb_root.exists():
                for pj in kb_root.rglob('project.json'):
                    try:
                        with open(pj, 'r', encoding='utf-8') as f:
                            project_files.append(_json.load(f))
                    except Exception:
                        continue

            daily_root = self.local_root / 'Daily-Reports'
            latest_report = ''
            report_count = 0
            if daily_root.exists():
                reports = sorted([p.name for p in daily_root.glob('*_Report.md')])
                report_count = len(reports)
                if reports:
                    latest_report = reports[-1].replace('_Report.md', '')

            recommended = [p for p in project_files if p.get('score', 0) >= 90]
            recommended_sorted = sorted(recommended, key=lambda x: x.get('score', 0), reverse=True)

            content = f"""# vibeRepository - AI 开源项目每日研究知识库

> 自动化 AI 开源项目研究、真实测试与知识库维护系统。每日从 GitHub、HuggingFace、HackerNews、Reddit 等平台采集热门 AI 项目，经过多轮筛选、真实安装运行测试，最终生成完整评测报告与知识库。

## 📊 知识库总览

| 指标 | 数值 |
|------|------|
| 最近更新日期 | {date_str} |
| 累计日报数 | {report_count} |
| 知识库项目数 | {len(project_files)} |
| 推荐项目数(≥90分) | {len(recommended)} |

## 🏆 最近推荐项目 TOP 10

| # | 项目 | 评分 | 推荐指数 | 总 Star | 分类 |
|---|------|------|----------|---------|------|
"""
            for i, p in enumerate(recommended_sorted[:10], 1):
                content += (f"| {i} | [{p.get('name', 'N/A')}]({p.get('url', '#')}) | "
                            f"{p.get('score', 0)} | {p.get('stars_display', '☆☆☆☆☆')} | "
                            f"{p.get('stars', 0)} | {p.get('category', 'N/A')} |\n")

            if not recommended_sorted:
                content += "| - | 暂无 90 分以上项目，持续测试中 | - | - | - | - |\n"

            content += f"""
## 📁 目录结构

```
Daily-Reports/        # 每日报告（今日 TOP5/TOP10）
Weekly-Reports/       # 每周 TOP10 报告
Monthly-Reports/      # 月度报告
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

最近一次日报: `{latest_report or '暂无'}`

## 🔗 相关链接

- 工作流源码: 本仓库根目录 `main.py` + `modules/`
- 配置文件: `config.yaml`
- 提交规范: `[{date_str}] Daily AI Project Update`

---

*本 README 由 AI 工作流自动维护，每次同步自动更新统计与推荐列表。最后更新: {date_str}*
"""
            readme_path = repo_dir / 'README.md'
            old_content = ''
            if readme_path.exists():
                with open(readme_path, 'r', encoding='utf-8') as f:
                    old_content = f.read()
            if old_content != content:
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                logger.info(f"仓库 README 已更新: {readme_path}")
                return True
            logger.info("仓库 README 无变化")
            return False
        except Exception as e:
            logger.error(f"更新仓库 README 失败: {e}")
            return False

    def _commit_and_push(self, repo_dir: Path, date_str: str):
        commit_msg = f"[{date_str}] Daily AI Project Update"
        
        result = subprocess.run(
            ['git', 'add', '-A'],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.warning(f"git add 失败: {result.stderr}")
            return
        
        result = subprocess.run(
            ['git', 'commit', '-m', commit_msg],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            if 'nothing to commit' in result.stdout:
                logger.info("无新内容可提交")
                return
            logger.warning(f"git commit 失败: {result.stderr}")
            return
        
        result = subprocess.run(
            ['git', 'push', 'origin', self.branch],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            logger.warning(f"git push 失败: {result.stderr}")
        else:
            logger.info("Push 成功")
