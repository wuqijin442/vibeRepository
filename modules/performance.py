#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    def __init__(self, config):
        self.config = config

    def analyze(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        clone_path = project.get('clone_path')
        
        logger.info(f"性能分析: {name}")
        
        project['perf_disk_usage'] = 0
        project['perf_compatibility'] = ['Linux']
        project['perf_docker_support'] = project.get('has_docker', False)
        
        if clone_path and Path(clone_path).exists():
            try:
                disk_usage = self._get_dir_size(Path(clone_path))
                project['perf_disk_usage'] = round(disk_usage / 1024 / 1024, 2)
            except Exception as e:
                logger.error(f"计算磁盘占用失败: {e}")
        
        project['perf_compatibility'] = self._check_compatibility(project)
        
        return project

    def _get_dir_size(self, path: Path) -> int:
        total = 0
        try:
            for entry in os.scandir(str(path)):
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir() and '.git' not in entry.name and 'node_modules' not in entry.name and 'venv' not in entry.name:
                    total += self._get_dir_size(Path(entry.path))
        except Exception:
            pass
        return total

    def _check_compatibility(self, project: Dict) -> list:
        platforms = ['Linux']
        readme = project.get('readme_content', '').lower()
        language = project.get('primary_language', '').lower()
        frameworks = [f.lower() for f in project.get('frameworks', [])]
        
        if language in ['python', 'javascript', 'typescript', 'go', 'java', 'rust']:
            platforms.extend(['Windows', 'macOS'])
        
        if any(kw in readme for kw in ['windows', 'win32', 'macos', 'mac os', 'darwin', 'cross-platform']):
            if 'Windows' not in platforms:
                platforms.append('Windows')
            if 'macOS' not in platforms:
                platforms.append('macOS')
        
        if any(fw in frameworks for fw in ['electron', 'tauri']):
            if 'Windows' not in platforms:
                platforms.append('Windows')
            if 'macOS' not in platforms:
                platforms.append('macOS')
        
        if project.get('has_docker', False):
            platforms.append('Docker')
        
        return list(set(platforms))
