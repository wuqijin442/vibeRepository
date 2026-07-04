#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import subprocess
import shutil
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
        self.workspace = Path(config.get('paths', {}).get('workspace', './workspace'))
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
            
            synced_files = self._copy_files(repo_dir)
            
            if synced_files > 0:
                self._commit_and_push(repo_dir, date_str)
            
            logger.info(f"同步完成，共 {synced_files} 个文件")
            return synced_files
            
        except Exception as e:
            logger.error(f"GitHub 同步失败: {e}")
            return 0

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
