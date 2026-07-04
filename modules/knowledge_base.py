#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import shutil
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class KnowledgeBaseManager:
    def __init__(self, config):
        self.config = config
        self.kb_dir = Path(config.get('paths', {}).get('knowledge_base', './Knowledge-Base'))
        self.metadata_dir = Path(config.get('paths', {}).get('metadata', './Metadata'))
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
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
