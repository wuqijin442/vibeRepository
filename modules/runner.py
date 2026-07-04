#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import subprocess
import time
import psutil
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ProjectRunner:
    def __init__(self, config):
        self.config = config
        self.processes = {}

    def run(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        clone_path = project.get('clone_path')
        install_method = project.get('install_method', '')
        
        logger.info(f"运行项目: {name}")
        
        project['run_success'] = False
        project['run_time'] = 0
        project['run_log'] = ''
        project['run_command'] = ''
        project['startup_time'] = 0
        project['cpu_usage'] = 0
        project['memory_usage'] = 0
        project['project_type'] = self._detect_project_type(project)
        
        if not clone_path or not Path(clone_path).exists():
            project['run_error'] = '项目路径不存在'
            return project
        
        start_time = time.time()
        
        try:
            run_cmd = self._get_run_command(project, install_method)
            project['run_command'] = run_cmd
            
            if not run_cmd:
                project['run_error'] = '无法确定运行命令'
                return project
            
            logger.info(f"运行命令: {run_cmd}")
            
            process = subprocess.Popen(
                run_cmd,
                cwd=str(clone_path),
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes[name] = process
            
            startup_success, startup_time = self._wait_for_startup(process, project)
            project['startup_time'] = round(startup_time, 2)
            
            if startup_success:
                project['run_success'] = True
                self._measure_performance(process, project)
            
            elapsed = time.time() - start_time
            project['run_time'] = round(elapsed, 2)
            
            if startup_success:
                logger.info(f"项目 {name} 启动成功 (耗时: {startup_time:.1f}s)")
            else:
                logger.warning(f"项目 {name} 启动失败或超时")
                
                try:
                    stdout, stderr = process.communicate(timeout=5)
                    project['run_log'] = f"STDOUT:\n{stdout[:2000]}\nSTDERR:\n{stderr[:2000]}"
                except Exception:
                    pass
                
                self._terminate_process(process)
            
        except Exception as e:
            logger.error(f"运行项目 {name} 异常: {e}")
            project['run_error'] = str(e)
        
        return project

    def _detect_project_type(self, project: Dict) -> str:
        readme = project.get('readme_content', '').lower()
        tags = project.get('tags', [])
        files = project.get('top_level_files', [])
        dirs = project.get('top_level_dirs', [])
        
        if 'MCP' in tags or 'mcp server' in readme:
            return 'mcp_server'
        elif any(d.lower() in ['src', 'app', 'client'] for d in dirs) and any(f.endswith('.tsx') or f.endswith('.jsx') for f in files):
            return 'web_app'
        elif 'agent' in readme or 'Agent' in tags:
            return 'agent'
        elif 'cli' in readme or 'command line' in readme:
            return 'cli'
        elif 'api' in readme:
            return 'api_server'
        elif any(f in files for f in ['server.py', 'main.py', 'app.py']):
            return 'python_server'
        else:
            return 'unknown'

    def _get_run_command(self, project: Dict, install_method: str) -> str:
        clone_path = Path(project.get('clone_path', '.'))
        readme = project.get('readme_content', '').lower()
        project_type = project.get('project_type', 'unknown')
        
        if install_method == 'poetry':
            if (clone_path / 'pyproject.toml').exists():
                try:
                    import re
                    with open(clone_path / 'pyproject.toml', 'r') as f:
                        content = f.read()
                    
                    match = re.search(r'\[tool\.poetry\.scripts\]\s*\n([^\[]+)', content)
                    if match:
                        scripts = match.group(1)
                        first_script = scripts.strip().split('\n')[0]
                        if '=' in first_script:
                            script_name = first_script.split('=')[0].strip()
                            return f'poetry run {script_name}'
                except Exception:
                    pass
            return 'poetry run python main.py' if (clone_path / 'main.py').exists() else 'poetry run python app.py'
        
        if install_method in ['pip_requirements', 'pip_setup', 'uv']:
            if (clone_path / 'main.py').exists():
                return 'python main.py'
            elif (clone_path / 'app.py').exists():
                return 'python app.py'
            elif (clone_path / 'server.py').exists():
                return 'python server.py'
            elif (clone_path / 'run.py').exists():
                return 'python run.py'
        
        if install_method in ['npm', 'pnpm', 'yarn', 'bun']:
            pkg_manager = install_method
            if (clone_path / 'package.json').exists():
                try:
                    import json
                    with open(clone_path / 'package.json', 'r') as f:
                        pkg = json.load(f)
                    
                    scripts = pkg.get('scripts', {})
                    if 'dev' in scripts:
                        return f'{pkg_manager} run dev'
                    elif 'start' in scripts:
                        return f'{pkg_manager} start'
                    elif 'serve' in scripts:
                        return f'{pkg_manager} run serve'
                except Exception:
                    pass
        
        if install_method == 'cargo':
            return 'cargo run --release'
        
        if install_method == 'go':
            if (clone_path / 'main.go').exists():
                return 'go run main.go'
            else:
                return 'go run ./cmd/main'
        
        if 'docker-compose' in install_method:
            return 'docker-compose up -d'
        
        if install_method == 'docker':
            return 'docker run -d project-test'
        
        return ''

    def _wait_for_startup(self, process: subprocess.Popen, project: Dict, max_wait: int = 30) -> tuple:
        start_time = time.time()
        project_type = project.get('project_type', 'unknown')
        
        while time.time() - start_time < max_wait:
            if process.poll() is not None:
                return (False, time.time() - start_time)
            
            try:
                cpu_percent = 0
                mem_mb = 0
                
                try:
                    proc = psutil.Process(process.pid)
                    cpu_percent = proc.cpu_percent(interval=0.5)
                    mem_info = proc.memory_info()
                    mem_mb = mem_info.rss / 1024 / 1024
                    
                    if mem_mb > 50 or cpu_percent > 0:
                        time.sleep(2)
                        if process.poll() is None:
                            return (True, time.time() - start_time)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
            except Exception:
                pass
            
            time.sleep(1)
        
        if process.poll() is None:
            return (True, time.time() - start_time)
        
        return (False, time.time() - start_time)

    def _measure_performance(self, process: subprocess.Popen, project: Dict):
        try:
            proc = psutil.Process(process.pid)
            
            cpu_samples = []
            mem_samples = []
            
            for _ in range(3):
                try:
                    cpu = proc.cpu_percent(interval=1)
                    mem_info = proc.memory_info()
                    mem_mb = mem_info.rss / 1024 / 1024
                    
                    cpu_samples.append(cpu)
                    mem_samples.append(mem_mb)
                    
                    children = proc.children(recursive=True)
                    for child in children:
                        try:
                            child_cpu = child.cpu_percent()
                            child_mem = child.memory_info().rss / 1024 / 1024
                            cpu_samples.append(child_cpu)
                            mem_samples.append(child_mem)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
            
            if cpu_samples:
                project['cpu_usage'] = round(sum(cpu_samples) / len(cpu_samples), 1)
            if mem_samples:
                project['memory_usage'] = round(sum(mem_samples), 1)
                
        except Exception as e:
            logger.debug(f"性能测量失败: {e}")

    def _terminate_process(self, process: subprocess.Popen):
        try:
            proc = psutil.Process(process.pid)
            children = proc.children(recursive=True)
            
            for child in children:
                try:
                    child.terminate()
                except Exception:
                    pass
            
            proc.terminate()
            
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def cleanup(self, name: str):
        if name in self.processes:
            self._terminate_process(self.processes[name])
            del self.processes[name]
