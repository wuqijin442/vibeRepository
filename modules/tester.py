#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import subprocess
import time
import re
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class ProjectTester:
    def __init__(self, config):
        self.config = config

    def test(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        project_type = project.get('project_type', 'unknown')
        
        logger.info(f"测试项目: {name} (类型: {project_type})")
        
        project['demo_success'] = False
        project['test_log'] = ''
        project['test_time'] = 0
        
        start_time = time.time()
        
        try:
            if project_type == 'web_app':
                success, log = self._test_web_project(project)
            elif project_type == 'cli':
                success, log = self._test_cli_project(project)
            elif project_type == 'api_server':
                success, log = self._test_api_project(project)
            elif project_type == 'python_server':
                success, log = self._test_api_project(project)
            elif project_type == 'mcp_server':
                success, log = self._test_mcp_project(project)
            elif project_type == 'agent':
                success, log = self._test_agent_project(project)
            else:
                success, log = self._test_generic(project)
            
            project['demo_success'] = success
            project['test_log'] = log[:3000]
            
        except Exception as e:
            logger.error(f"测试项目 {name} 异常: {e}")
            project['test_error'] = str(e)
        
        project['test_time'] = round(time.time() - start_time, 2)
        
        if project['demo_success']:
            logger.info(f"项目 {name} Demo 测试通过")
        else:
            logger.warning(f"项目 {name} Demo 测试失败")
        
        return project

    def _test_web_project(self, project: Dict) -> tuple:
        clone_path = Path(project.get('clone_path', '.'))
        readme = project.get('readme_content', '').lower()
        
        port = self._detect_port(project)
        url = f'http://localhost:{port}'
        
        try:
            import requests
            time.sleep(3)
            
            for i in range(5):
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        return (True, f"Web 服务可访问: {url} (状态码: {resp.status_code})")
                except requests.exceptions.ConnectionError:
                    time.sleep(2)
                    continue
            
            return (False, f"无法访问 Web 服务: {url}")
            
        except Exception as e:
            return (False, f"Web 测试异常: {str(e)}")

    def _test_cli_project(self, project: Dict) -> tuple:
        clone_path = Path(project.get('clone_path', '.'))
        install_method = project.get('install_method', '')
        
        help_cmd = ''
        if install_method == 'poetry':
            help_cmd = 'poetry run python main.py --help'
            if not (clone_path / 'main.py').exists():
                help_cmd = 'poetry run python app.py --help'
        elif install_method in ['pip_requirements', 'pip_setup', 'uv']:
            help_cmd = 'python main.py --help'
            if not (clone_path / 'main.py').exists():
                help_cmd = 'python app.py --help'
        elif install_method in ['npm', 'pnpm', 'yarn', 'bun']:
            help_cmd = f'{install_method} run --help'
        elif install_method == 'cargo':
            help_cmd = 'cargo run --release -- --help'
        elif install_method == 'go':
            help_cmd = 'go run main.go --help'
        
        if not help_cmd:
            return (False, '无法确定 CLI 测试命令')
        
        try:
            result = subprocess.run(
                help_cmd,
                cwd=str(clone_path),
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )
            
            log = f"STDOUT:\n{result.stdout[:1000]}\nSTDERR:\n{result.stderr[:1000]}"
            
            if result.returncode == 0 or result.stdout:
                return (True, f"CLI 帮助命令执行成功\n{log}")
            else:
                return (False, f"CLI 帮助命令失败\n{log}")
                
        except subprocess.TimeoutExpired:
            return (False, 'CLI 测试超时')
        except Exception as e:
            return (False, f"CLI 测试异常: {str(e)}")

    def _test_api_project(self, project: Dict) -> tuple:
        port = self._detect_port(project)
        base_url = f'http://localhost:{port}'
        
        try:
            import requests
            time.sleep(2)
            
            health_urls = [
                f'{base_url}/health',
                f'{base_url}/api/health',
                f'{base_url}/',
                f'{base_url}/docs',
                f'{base_url}/api/docs',
            ]
            
            for url in health_urls:
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code in [200, 404, 401]:
                        return (True, f"API 服务可访问: {url} (状态码: {resp.status_code})")
                except requests.exceptions.ConnectionError:
                    continue
            
            return (False, f"无法访问 API 服务: {base_url}")
            
        except Exception as e:
            return (False, f"API 测试异常: {str(e)}")

    def _test_mcp_project(self, project: Dict) -> tuple:
        clone_path = Path(project.get('clone_path', '.'))
        install_method = project.get('install_method', '')
        
        list_tools_cmd = ''
        if install_method == 'poetry':
            list_tools_cmd = 'poetry run python -m mcp server'
        elif install_method in ['pip_requirements', 'pip_setup', 'uv']:
            list_tools_cmd = 'python -m mcp server'
        elif install_method in ['npm', 'pnpm', 'yarn', 'bun']:
            list_tools_cmd = f'{install_method} exec mcp-server'
        
        if not list_tools_cmd:
            return (False, '无法确定 MCP 测试命令')
        
        try:
            result = subprocess.run(
                list_tools_cmd + ' --help',
                cwd=str(clone_path),
                capture_output=True,
                text=True,
                timeout=30,
                shell=True
            )
            
            log = f"STDOUT:\n{result.stdout[:1000]}\nSTDERR:\n{result.stderr[:1000]}"
            
            if result.returncode == 0 or 'mcp' in result.stdout.lower():
                return (True, f"MCP 服务命令可用\n{log}")
            else:
                return (False, f"MCP 服务命令不可用\n{log}")
                
        except Exception as e:
            return (False, f"MCP 测试异常: {str(e)}")

    def _test_agent_project(self, project: Dict) -> tuple:
        return self._test_cli_project(project)

    def _test_generic(self, project: Dict) -> tuple:
        clone_path = Path(project.get('clone_path', '.'))
        readme = project.get('readme_content', '').lower()
        
        examples_dir = clone_path / 'examples'
        if examples_dir.exists():
            return (True, '存在 examples 目录，包含示例代码')
        
        if project.get('has_readme', False) and project.get('readme_has_demo', False):
            return (True, 'README 包含 Demo/示例说明')
        
        return (False, '未找到明确的测试方式')

    def _detect_port(self, project: Dict) -> int:
        readme = project.get('readme_content', '').lower()
        clone_path = Path(project.get('clone_path', '.'))
        
        ports = []
        
        import re
        port_patterns = [
            r'port[\s:=]+(\d{2,5})',
            r'localhost:(\d{2,5})',
            r'127\.0\.0\.1:(\d{2,5})',
            r'0\.0\.0\.0:(\d{2,5})',
        ]
        
        for pattern in port_patterns:
            matches = re.findall(pattern, readme)
            for m in matches:
                port = int(m)
                if 1000 <= port <= 65535:
                    ports.append(port)
        
        env_file = clone_path / '.env.example'
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    env_content = f.read().lower()
                for pattern in port_patterns:
                    matches = re.findall(pattern, env_content)
                    for m in matches:
                        port = int(m)
                        if 1000 <= port <= 65535:
                            ports.append(port)
            except Exception:
                pass
        
        common_ports = [3000, 8000, 8080, 5173, 4000, 5000, 8501]
        ports.extend(common_ports)
        
        return ports[0] if ports else 8000
