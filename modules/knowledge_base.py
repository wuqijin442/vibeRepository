#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List
from datetime import datetime

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    def __init__(self, config):
        self.config = config
        self.kb_dir = Path(config.get('paths', {}).get('knowledge_base', './Knowledge-Base'))
        self.metadata_dir = Path(config.get('paths', {}).get('metadata', './Metadata'))
        self.logs_dir = Path(config.get('paths', {}).get('logs', './workspace/logs'))
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        self.category_map = {
            'Agent': 'Agents',
            'Coding': 'Coding',
            'MCP': 'MCP',
            'Workflow': 'Workflow',
            'LLM': 'LLM',
            'RAG': 'RAG',
            'OCR': 'OCR',
            'Browser Use': 'Automation',
            'Computer Use': 'Automation',
            'Voice': 'Voice',
            'Image Gen': 'Image',
            'Video Gen': 'Video',
            'DevTools': 'Utilities',
            'Local AI': 'LocalAI',
        }

    def add_project(self, project: Dict) -> bool:
        name = project.get('name', 'unknown')
        score = project.get('score', 0)
        stars = project.get('stars_count', 0)
        
        if score < 90 or stars < 4:
            logger.info(f"项目 {name} 评分不足 (score={score}, stars={stars})，不加入知识库")
            return False
        
        if not project.get('install_success', False) or not project.get('run_success', False):
            logger.info(f"项目 {name} 安装或运行失败，不加入知识库")
            return False
        
        logger.info(f"项目 {name} 加入知识库")
        
        try:
            category = self._get_primary_category(project)
            proj_dir = self.kb_dir / category / self._safe_name(name)
            proj_dir.mkdir(parents=True, exist_ok=True)
            
            self._copy_docs(project, proj_dir)
            self._copy_screenshots(project, proj_dir)
            self._generate_metadata(project, proj_dir, category)
            
            return True
            
        except Exception as e:
            logger.error(f"添加项目到知识库失败 {name}: {e}")
            return False

    def _get_primary_category(self, project: Dict) -> str:
        tags = project.get('tags', [])
        
        priority = ['Agent', 'Coding', 'MCP', 'Workflow', 'LLM', 'RAG', 
                   'Browser Use', 'Computer Use', 'OCR', 'Voice', 
                   'Image Gen', 'Video Gen', 'DevTools', 'Local AI']
        
        for tag in priority:
            if tag in tags:
                return self.category_map.get(tag, 'Others')
        
        return 'Others'

    def _safe_name(self, name: str) -> str:
        return name.replace('/', '_').replace('\\', '_')

    def _copy_docs(self, project: Dict, proj_dir: Path):
        docs_path = project.get('docs_path')
        if docs_path and Path(docs_path).exists():
            src = Path(docs_path)
            for f in src.glob('*.md'):
                shutil.copy2(f, proj_dir / f.name)

    def _copy_screenshots(self, project: Dict, proj_dir: Path):
        screenshots = project.get('screenshots', [])
        if screenshots:
            screen_dir = proj_dir / 'screenshots'
            screen_dir.mkdir(exist_ok=True)
            for s in screenshots:
                if Path(s).exists():
                    shutil.copy2(s, screen_dir / Path(s).name)

    def _generate_metadata(self, project: Dict, proj_dir: Path, category: str):
        metadata = {
            'name': project.get('name', ''),
            'category': category,
            'url': project.get('url', ''),
            'author': project.get('author', ''),
            'license': project.get('license', ''),
            'description': project.get('description', ''),
            'language': project.get('primary_language', ''),
            'frameworks': project.get('frameworks', []),
            'tags': project.get('tags', []),
            'stars': project.get('stars', 0),
            'daily_stars': project.get('daily_stars', 0),
            'forks': project.get('forks', 0),
            'score': project.get('score', 0),
            'stars_count': project.get('stars_count', 0),
            'install_success': project.get('install_success', False),
            'run_success': project.get('run_success', False),
            'demo_success': project.get('demo_success', False),
            'install_time': project.get('install_time', 0),
            'startup_time': project.get('startup_time', 0),
            'cpu_usage': project.get('cpu_usage', 0),
            'memory_usage': project.get('memory_usage', 0),
            'disk_usage': project.get('perf_disk_usage', 0),
            'advantages': project.get('advantages', []),
            'disadvantages': project.get('disadvantages', []),
            'target_audience': project.get('target_audience', []),
            'use_cases': project.get('use_cases', []),
            'competitors': project.get('competitors', []),
            'added_at': project.get('collected_at', ''),
            'updated_at': project.get('updated_at', ''),
        }
        
        with open(proj_dir / 'project.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        meta_file = self.metadata_dir / f"{self._safe_name(project.get('name', ''))}.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def list_projects(self, category: str = None) -> List[Dict]:
        projects = []
        
        if category:
            cat_dir = self.kb_dir / category
            if cat_dir.exists():
                for proj_dir in cat_dir.iterdir():
                    meta_file = proj_dir / 'project.json'
                    if meta_file.exists():
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            projects.append(json.load(f))
        else:
            for cat_dir in self.kb_dir.iterdir():
                if cat_dir.is_dir():
                    for proj_dir in cat_dir.iterdir():
                        meta_file = proj_dir / 'project.json'
                        if meta_file.exists():
                            with open(meta_file, 'r', encoding='utf-8') as f:
                                projects.append(json.load(f))
        
        return projects

    def update_project(self, name: str, updates: Dict) -> bool:
        projects = self.list_projects()
        for p in projects:
            if p.get('name') == name:
                p.update(updates)
                category = p.get('category', 'Others')
                proj_dir = self.kb_dir / category / self._safe_name(name)
                with open(proj_dir / 'project.json', 'w', encoding='utf-8') as f:
                    json.dump(p, f, indent=2, ensure_ascii=False)
                return True
        return False

    def daily_scan(self) -> Dict:
        logger.info("开始知识库每日扫描...")
        projects = self.list_projects()
        results = {
            'total': len(projects),
            'updated': 0,
            'new_releases': 0,
            'stop_maintaining': [],
            'issue_changes': [],
            'security_alerts': [],
            'star_growth': []
        }
        
        for project in projects:
            try:
                self._scan_single_project(project, results)
            except Exception as e:
                logger.error(f"扫描项目 {project.get('name', 'unknown')} 失败: {e}")
        
        logger.info(f"每日扫描完成: 共 {results['total']} 个项目, "
                   f"更新 {results['updated']} 个, "
                   f"新版本 {results['new_releases']} 个")
        
        self._save_scan_report(results)
        return results

    def _scan_single_project(self, project: Dict, results: Dict):
        name = project.get('name', '')
        url = project.get('url', '')
        
        if not url or 'github.com' not in url:
            return
        
        star_growth = self._check_star_growth(project)
        if star_growth:
            results['star_growth'].append({
                'name': name,
                'growth': star_growth
            })
            results['updated'] += 1
        
        new_release = self._check_new_release(project)
        if new_release:
            results['new_releases'] += 1
            results['updated'] += 1
        
        is_stopped = self._check_maintenance_status(project)
        if is_stopped:
            results['stop_maintaining'].append(name)
        
        issue_change = self._check_issue_changes(project)
        if issue_change:
            results['issue_changes'].append({
                'name': name,
                'change': issue_change
            })
        
        security_alert = self._check_security_alerts(project)
        if security_alert:
            results['security_alerts'].append({
                'name': name,
                'alert': security_alert
            })

    def _check_star_growth(self, project: Dict) -> int:
        try:
            old_stars = project.get('stars', 0)
            url = project.get('url', '')
            
            if not url or 'github.com' not in url:
                return 0
            
            repo_path = url.replace('https://github.com/', '').rstrip('/')
            api_url = f'https://api.github.com/repos/{repo_path}'
            
            import requests
            headers = {}
            token = self.config.get('github', {}).get('token', '')
            if token:
                headers['Authorization'] = f'token {token}'
            
            resp = requests.get(api_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                new_stars = data.get('stargazers_count', old_stars)
                growth = new_stars - old_stars
                
                if growth > 0:
                    project['stars'] = new_stars
                    project['daily_stars'] = growth
                    category = project.get('category', 'Others')
                    proj_dir = self.kb_dir / category / self._safe_name(project.get('name', ''))
                    if proj_dir.exists():
                        with open(proj_dir / 'project.json', 'w', encoding='utf-8') as f:
                            json.dump(project, f, indent=2, ensure_ascii=False)
                
                return growth
        except Exception as e:
            logger.debug(f"检查 Star 增长失败 {project.get('name', '')}: {e}")
        
        return 0

    def _check_new_release(self, project: Dict) -> bool:
        try:
            url = project.get('url', '')
            if not url or 'github.com' not in url:
                return False
            
            repo_path = url.replace('https://github.com/', '').rstrip('/')
            api_url = f'https://api.github.com/repos/{repo_path}/releases/latest'
            
            import requests
            headers = {}
            token = self.config.get('github', {}).get('token', '')
            if token:
                headers['Authorization'] = f'token {token}'
            
            resp = requests.get(api_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                latest_release = data.get('tag_name', '')
                last_checked = project.get('last_release', '')
                
                if latest_release and latest_release != last_checked:
                    project['last_release'] = latest_release
                    project['last_release_date'] = data.get('published_at', '')
                    return True
        except Exception as e:
            logger.debug(f"检查新版本失败 {project.get('name', '')}: {e}")
        
        return False

    def _check_maintenance_status(self, project: Dict) -> bool:
        try:
            updated_at = project.get('updated_at', '')
            if not updated_at:
                return False
            
            from datetime import datetime, timedelta
            try:
                updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                days_since_update = (datetime.now(updated.tzinfo) - updated).days
                
                if days_since_update > 180:
                    project['maintenance_status'] = '可能停止维护'
                    return True
            except (ValueError, TypeError):
                pass
        except Exception as e:
            logger.debug(f"检查维护状态失败 {project.get('name', '')}: {e}")
        
        return False

    def _check_issue_changes(self, project: Dict) -> str:
        try:
            url = project.get('url', '')
            if not url or 'github.com' not in url:
                return ''
            
            repo_path = url.replace('https://github.com/', '').rstrip('/')
            api_url = f'https://api.github.com/repos/{repo_path}'
            
            import requests
            headers = {}
            token = self.config.get('github', {}).get('token', '')
            if token:
                headers['Authorization'] = f'token {token}'
            
            resp = requests.get(api_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                new_issues = data.get('open_issues_count', 0)
                old_issues = project.get('open_issues', 0)
                
                if new_issues != old_issues:
                    project['open_issues'] = new_issues
                    change = new_issues - old_issues
                    return f"{'+' if change > 0 else ''}{change} issues"
        except Exception as e:
            logger.debug(f"检查 Issue 变化失败 {project.get('name', '')}: {e}")
        
        return ''

    def _check_security_alerts(self, project: Dict) -> str:
        clone_path = project.get('clone_path', '')
        if not clone_path or not Path(clone_path).exists():
            return ''
        
        alerts = []
        
        env_file = Path(clone_path) / '.env'
        if env_file.exists():
            alerts.append('存在 .env 文件，可能包含敏感信息')
        
        for pattern in ['*.key', '*.pem', '*secret*', '*password*']:
            found = list(Path(clone_path).rglob(pattern))
            if found:
                alerts.append(f'发现疑似敏感文件: {pattern}')
        
        return '; '.join(alerts) if alerts else ''

    def _save_scan_report(self, results: Dict):
        report_path = self.logs_dir / f'kb_scan_{datetime.now().strftime("%Y%m%d")}.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"知识库扫描报告已保存: {report_path}")
