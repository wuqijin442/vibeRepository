#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import json
import shutil
from pathlib import Path
from typing import Dict
import subprocess

logger = logging.getLogger(__name__)


class ProjectAnalyzer:
    def __init__(self, config):
        self.config = config
        self.clones_dir = Path(config.get('paths', {}).get('clones', './workspace/clones'))
        self.clones_dir.mkdir(parents=True, exist_ok=True)

    def analyze(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        logger.info(f"分析项目: {name}")
        
        project['cloned'] = False
        project['clone_path'] = None
        
        url = project.get('url', '')
        if 'github.com' not in url:
            logger.warning(f"非 GitHub 项目，跳过 Clone: {url}")
            project['analysis_error'] = '非 GitHub 项目'
            return project
        
        clone_path = self._clone_repo(url, name)
        if not clone_path:
            project['analysis_error'] = 'Clone 失败'
            return project
        
        project['cloned'] = True
        project['clone_path'] = str(clone_path)
        
        self._analyze_structure(project, clone_path)
        self._analyze_readme(project, clone_path)
        self._detect_language(project, clone_path)
        self._detect_framework(project, clone_path)
        self._detect_license(project, clone_path)
        self._detect_dependencies(project, clone_path)
        self._detect_deployment(project, clone_path)
        self._generate_tags(project)
        
        logger.info(f"项目 {name} 分析完成")
        return project

    def _clone_repo(self, url: str, name: str) -> Path:
        safe_name = name.replace('/', '_').replace('\\', '_')
        clone_path = self.clones_dir / safe_name

        if clone_path.exists():
            if not (clone_path / '.git').exists():
                logger.warning(f"目录存在但非有效 git 仓库，删除后重新 Clone: {clone_path}")
                shutil.rmtree(clone_path)
            else:
                logger.info(f"项目已存在，尝试更新: {clone_path}")
                try:
                    result = subprocess.run(
                        ['git', 'pull'],
                        cwd=str(clone_path),
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    if result.returncode == 0:
                        return clone_path
                except Exception as e:
                    logger.warning(f"更新失败，尝试重新 Clone: {e}")
        
        try:
            logger.info(f"Cloning {url} -> {clone_path}")
            result = subprocess.run(
                ['git', 'clone', '--depth', '1', url, str(clone_path)],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0 and clone_path.exists():
                return clone_path
            else:
                logger.error(f"Clone 失败: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error(f"Clone 超时: {url}")
            return None
        except Exception as e:
            logger.error(f"Clone 异常: {e}")
            return None

    def _analyze_structure(self, project: Dict, clone_path: Path):
        try:
            items = list(clone_path.iterdir())
            project['top_level_files'] = [f.name for f in items if f.is_file()]
            project['top_level_dirs'] = [d.name for d in items if d.is_dir()]
            
            total_files = 0
            total_dirs = 0
            for root, dirs, files in os.walk(str(clone_path)):
                if '.git' in root:
                    continue
                total_files += len(files)
                total_dirs += len(dirs)
            
            project['total_files'] = total_files
            project['total_dirs'] = total_dirs
            
        except Exception as e:
            logger.error(f"分析目录结构失败: {e}")

    def _analyze_readme(self, project: Dict, clone_path: Path):
        readme_names = ['README.md', 'README.MD', 'readme.md', 'README', 'Readme.md']
        readme_path = None
        
        for name in readme_names:
            p = clone_path / name
            if p.exists():
                readme_path = p
                break
        
        if not readme_path:
            project['has_readme'] = False
            return
        
        project['has_readme'] = True
        
        try:
            with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            project['readme_content'] = content[:10000]
            project['readme_length'] = len(content)
            
            has_demo = any(kw in content.lower() for kw in ['demo', 'screenshot', 'gif', 'example', 'usage'])
            has_install = any(kw in content.lower() for kw in ['install', 'setup', 'getting started', 'quick start'])
            has_docs = any(kw in content.lower() for kw in ['documentation', 'docs', 'api', 'guide'])
            
            project['readme_has_demo'] = has_demo
            project['readme_has_install'] = has_install
            project['readme_has_docs'] = has_docs
            
        except Exception as e:
            logger.error(f"读取 README 失败: {e}")

    def _detect_language(self, project: Dict, clone_path: Path):
        languages = {}
        
        ext_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.tsx': 'TypeScript',
            '.jsx': 'JavaScript',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.sh': 'Shell',
            '.lua': 'Lua',
            '.swift': 'Swift',
            '.kt': 'Kotlin'
        }
        
        try:
            for root, dirs, files in os.walk(str(clone_path)):
                if '.git' in root or 'node_modules' in root or 'venv' in root:
                    continue
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext in ext_map:
                        lang = ext_map[ext]
                        languages[lang] = languages.get(lang, 0) + 1
        except Exception as e:
            logger.error(f"检测语言失败: {e}")
        
        if languages:
            sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
            project['detected_languages'] = dict(sorted_langs)
            project['primary_language'] = sorted_langs[0][0]
        else:
            project['detected_languages'] = {}
            project['primary_language'] = project.get('language', 'Unknown')

    def _detect_framework(self, project: Dict, clone_path: Path):
        frameworks = []
        
        package_json = clone_path / 'package.json'
        if package_json.exists():
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    pkg = json.load(f)
                deps = list(pkg.get('dependencies', {}).keys())
                dev_deps = list(pkg.get('devDependencies', {}).keys())
                all_deps = deps + dev_deps
                
                for dep in all_deps:
                    dep_lower = dep.lower()
                    if any(kw in dep_lower for kw in ['react', 'vue', 'angular', 'next', 'svelte', 'express', 'fastify', 'nest', 'electron']):
                        frameworks.append(dep)
            except Exception:
                pass
        
        pyproject = clone_path / 'pyproject.toml'
        requirements = clone_path / 'requirements.txt'
        setup_py = clone_path / 'setup.py'
        
        py_frameworks = []
        if pyproject.exists():
            try:
                with open(pyproject, 'r', encoding='utf-8') as f:
                    content = f.read()
                for fw in ['fastapi', 'flask', 'django', 'langchain', 'llama-index', 'pydantic', 'torch', 'transformers']:
                    if fw in content.lower():
                        py_frameworks.append(fw)
            except Exception:
                pass
        
        if requirements.exists():
            try:
                with open(requirements, 'r', encoding='utf-8') as f:
                    content = f.read()
                for fw in ['fastapi', 'flask', 'django', 'langchain', 'llama_index', 'torch', 'transformers', 'numpy']:
                    if fw in content.lower():
                        py_frameworks.append(fw)
            except Exception:
                pass
        
        frameworks.extend(py_frameworks)
        project['frameworks'] = list(set(frameworks))

    def _detect_license(self, project: Dict, clone_path: Path):
        license_names = ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING', 'License.md']
        
        for name in license_names:
            p = clone_path / name
            if p.exists():
                try:
                    with open(p, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()[:500]
                    
                    if 'MIT' in content:
                        project['license'] = 'MIT'
                    elif 'GPL' in content:
                        project['license'] = 'GPL'
                    elif 'Apache' in content:
                        project['license'] = 'Apache'
                    elif 'BSD' in content:
                        project['license'] = 'BSD'
                    else:
                        project['license'] = 'Other'
                    return
                except Exception:
                    pass
        
        project['license'] = project.get('license', 'Unknown')

    def _detect_dependencies(self, project: Dict, clone_path: Path):
        dep_files = []
        
        for f in ['package.json', 'requirements.txt', 'pyproject.toml', 'setup.py', 
                  'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle', 'Gemfile']:
            if (clone_path / f).exists():
                dep_files.append(f)
        
        project['dependency_files'] = dep_files
        
        has_docker = (clone_path / 'Dockerfile').exists() or (clone_path / 'docker-compose.yml').exists()
        project['has_docker'] = has_docker

    def _detect_deployment(self, project: Dict, clone_path: Path):
        deployment = []
        
        if (clone_path / 'Dockerfile').exists():
            deployment.append('Docker')
        if (clone_path / 'docker-compose.yml').exists() or (clone_path / 'docker-compose.yaml').exists():
            deployment.append('Docker Compose')
        if (clone_path / '.github' / 'workflows').exists():
            deployment.append('GitHub Actions')
        if (clone_path / 'Makefile').exists():
            deployment.append('Makefile')
        if (clone_path / 'docker-compose.yml').exists():
            deployment.append('Docker Compose')
        
        project['deployment_methods'] = deployment
        
        platforms = ['Linux']
        readme = project.get('readme_content', '').lower()
        if any(kw in readme for kw in ['windows', 'macos', 'mac os', 'cross-platform']):
            platforms.extend(['Windows', 'macOS'])
        project['supported_platforms'] = list(set(platforms))

    def _generate_tags(self, project: Dict):
        tags = []
        text = (project.get('name', '') + ' ' + 
                project.get('description', '') + ' ' + 
                project.get('readme_content', '')).lower()
        
        tag_keywords = {
            'Agent': ['agent', 'multi-agent', 'autonomous'],
            'LLM': ['llm', 'gpt', 'large language model'],
            'RAG': ['rag', 'retrieval augmented', 'vector store'],
            'MCP': ['mcp', 'model context protocol'],
            'Coding': ['coding', 'code generation', 'programmer'],
            'Workflow': ['workflow', 'automation', 'pipeline'],
            'Browser Use': ['browser', 'headless', 'playwright', 'puppeteer'],
            'Computer Use': ['computer use', 'desktop automation'],
            'Local AI': ['local', 'offline', 'self-hosted', 'selfhosted'],
            'OCR': ['ocr', 'text recognition'],
            'Voice': ['whisper', 'tts', 'voice', 'speech'],
            'Image Gen': ['image generation', 'stable diffusion', 'flux', 'comfyui'],
            'Video Gen': ['video generation', 'text to video'],
            'DevTools': ['devtool', 'developer tool', 'productivity'],
            'Open Source': ['open source', 'opensource']
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in text for kw in keywords):
                tags.append(tag)
        
        if not tags:
            tags.append('AI')
        
        project['tags'] = tags
