#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class ProjectInstaller:
    def __init__(self, config):
        self.config = config
        self.install_logs_dir = Path(config.get('paths', {}).get('logs', './workspace/logs'))
        self.install_logs_dir.mkdir(parents=True, exist_ok=True)
        self.env_info = self._detect_environments()

    def _detect_environments(self) -> Dict:
        logger.info("检测运行环境...")
        envs = {}
        
        env_checks = {
            'python': ['python3 --version', 'python --version'],
            'pip': ['pip3 --version', 'pip --version'],
            'node': ['node --version'],
            'npm': ['npm --version'],
            'pnpm': ['pnpm --version'],
            'yarn': ['yarn --version'],
            'bun': ['bun --version'],
            'docker': ['docker --version'],
            'docker_compose': ['docker-compose --version', 'docker compose version'],
            'git': ['git --version'],
            'go': ['go version'],
            'rust': ['rustc --version'],
            'cargo': ['cargo --version'],
            'java': ['java -version'],
            'poetry': ['poetry --version'],
            'uv': ['uv --version'],
        }
        
        for env_name, commands in env_checks.items():
            available = False
            version = None
            for cmd in commands:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        shell=True
                    )
                    if result.returncode == 0:
                        available = True
                        output = result.stdout.strip() or result.stderr.strip()
                        import re
                        ver_match = re.search(r'(\d+\.\d+[\d\.]*)', output)
                        if ver_match:
                            version = ver_match.group(1)
                        break
                except Exception:
                    continue
            
            envs[env_name] = {
                'available': available,
                'version': version
            }
            status = '✓' if available else '✗'
            logger.info(f"  {status} {env_name}: {version or '未安装'}")
        
        return envs

    def install(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        clone_path = project.get('clone_path')
        
        logger.info(f"安装项目: {name}")
        
        project['install_success'] = False
        project['install_time'] = 0
        project['install_log'] = ''
        project['install_method'] = ''
        project['env_info'] = self.env_info
        
        if not clone_path or not Path(clone_path).exists():
            project['install_error'] = '项目未 Clone'
            project['fail_reason'] = 'not_cloned'
            return project
        
        if not self._check_required_env(project):
            project['install_error'] = '缺少必要的运行环境'
            project['fail_reason'] = 'missing_env'
            return project
        
        start_time = time.time()
        
        method, result = self._try_install(Path(clone_path), project)
        
        elapsed = time.time() - start_time
        project['install_time'] = round(elapsed, 2)
        project['install_method'] = method
        project['install_success'] = result[0]
        project['install_log'] = result[1]
        
        if not result[0]:
            project['fail_reason'] = 'install_failed'
        
        if result[0]:
            logger.info(f"项目 {name} 安装成功 (方法: {method}, 耗时: {elapsed:.1f}s)")
        else:
            logger.warning(f"项目 {name} 安装失败 (方法: {method})")
        
        return project
    
    def _check_required_env(self, project: Dict) -> bool:
        primary_lang = project.get('primary_language', '').lower()
        lang_env_map = {
            'python': 'python',
            'javascript': 'node',
            'typescript': 'node',
            'go': 'go',
            'rust': 'rust',
            'java': 'java',
        }
        
        required_env = lang_env_map.get(primary_lang)
        if required_env and not self.env_info.get(required_env, {}).get('available', False):
            logger.warning(f"项目需要 {primary_lang} 环境，但未检测到")
            return False
        
        return True

    def _try_install(self, clone_path: Path, project: Dict) -> Tuple[str, Tuple[bool, str]]:
        installers = [
            ('docker_compose', self._install_docker_compose),
            ('docker', self._install_docker),
            ('poetry', self._install_poetry),
            ('uv', self._install_uv),
            ('pip_requirements', self._install_pip_requirements),
            ('pip_setup', self._install_pip_setup),
            ('npm', self._install_npm),
            ('pnpm', self._install_pnpm),
            ('yarn', self._install_yarn),
            ('bun', self._install_bun),
            ('cargo', self._install_cargo),
            ('go', self._install_go),
        ]
        
        for method_name, method_func in installers:
            try:
                success, log = method_func(clone_path, project)
                if success:
                    return (method_name, (True, log))
            except Exception as e:
                logger.debug(f"安装方法 {method_name} 失败: {e}")
                continue
        
        return ('unknown', (False, '未找到可用的安装方法'))

    def _run_command(self, cmd, cwd, timeout=300) -> Tuple[bool, str]:
        try:
            result = subprocess.run(
                cmd,
                cwd=str(cwd),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=isinstance(cmd, str)
            )
            log = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            return (result.returncode == 0, log)
        except subprocess.TimeoutExpired:
            return (False, f"命令超时: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        except Exception as e:
            return (False, f"执行异常: {str(e)}")

    def _install_docker_compose(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'docker-compose.yml').exists() and not (path / 'docker-compose.yaml').exists():
            return (False, 'no docker-compose file')
        
        logger.info(f"尝试 Docker Compose 安装: {path}")
        return self._run_command('docker-compose pull', path, timeout=300)

    def _install_docker(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'Dockerfile').exists():
            return (False, 'no Dockerfile')
        
        logger.info(f"尝试 Docker 构建: {path}")
        return self._run_command('docker build -t project-test .', path, timeout=600)

    def _install_poetry(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'pyproject.toml').exists():
            return (False, 'no pyproject.toml')
        
        try:
            result = subprocess.run(['which', 'poetry'], capture_output=True, text=True)
            if result.returncode != 0:
                return (False, 'poetry not installed')
        except Exception:
            return (False, 'poetry check failed')
        
        logger.info(f"尝试 Poetry 安装: {path}")
        return self._run_command('poetry install', path, timeout=600)

    def _install_uv(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not ((path / 'pyproject.toml').exists() or (path / 'requirements.txt').exists()):
            return (False, 'no python project files')
        
        try:
            result = subprocess.run(['which', 'uv'], capture_output=True, text=True)
            if result.returncode != 0:
                return (False, 'uv not installed')
        except Exception:
            return (False, 'uv check failed')
        
        logger.info(f"尝试 uv 安装: {path}")
        
        if (path / 'pyproject.toml').exists():
            return self._run_command('uv sync', path, timeout=600)
        else:
            venv_path = path / '.venv'
            if not venv_path.exists():
                self._run_command('uv venv', path, timeout=60)
            return self._run_command('uv pip install -r requirements.txt', path, timeout=600)

    def _install_pip_requirements(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'requirements.txt').exists():
            return (False, 'no requirements.txt')
        
        logger.info(f"尝试 pip 安装 (requirements.txt): {path}")
        
        venv_path = path / 'venv'
        if not venv_path.exists():
            venv_path = path / '.venv'
        
        if not venv_path.exists():
            self._run_command('python3 -m venv venv', path, timeout=60)
            venv_path = path / 'venv'
        
        pip_path = venv_path / 'bin' / 'pip'
        if not pip_path.exists():
            pip_path = venv_path / 'Scripts' / 'pip.exe'
        
        if pip_path.exists():
            return self._run_command(f'{pip_path} install -r requirements.txt', path, timeout=600)
        else:
            return self._run_command('pip install -r requirements.txt', path, timeout=600)

    def _install_pip_setup(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'setup.py').exists() and not (path / 'setup.cfg').exists():
            return (False, 'no setup files')
        
        logger.info(f"尝试 pip 安装 (setup.py): {path}")
        return self._run_command('pip install -e .', path, timeout=600)

    def _install_npm(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'package.json').exists():
            return (False, 'no package.json')
        
        try:
            result = subprocess.run(['which', 'npm'], capture_output=True, text=True)
            if result.returncode != 0:
                return (False, 'npm not installed')
        except Exception:
            return (False, 'npm check failed')
        
        logger.info(f"尝试 npm 安装: {path}")
        return self._run_command('npm install', path, timeout=600)

    def _install_pnpm(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'package.json').exists():
            return (False, 'no package.json')
        
        try:
            result = subprocess.run(['which', 'pnpm'], capture_output=True, text=True)
            if result.returncode != 0:
                return (False, 'pnpm not installed')
        except Exception:
            return (False, 'pnpm check failed')
        
        logger.info(f"尝试 pnpm 安装: {path}")
        return self._run_command('pnpm install', path, timeout=600)

    def _install_yarn(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'package.json').exists():
            return (False, 'no package.json')
        
        try:
            result = subprocess.run(['which', 'yarn'], capture_output=True, text=True)
            if result.returncode != 0:
                return (False, 'yarn not installed')
        except Exception:
            return (False, 'yarn check failed')
        
        logger.info(f"尝试 yarn 安装: {path}")
        return self._run_command('yarn install', path, timeout=600)

    def _install_bun(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'package.json').exists():
            return (False, 'no package.json')
        
        try:
            result = subprocess.run(['which', 'bun'], capture_output=True, text=True)
            if result.returncode != 0:
                return (False, 'bun not installed')
        except Exception:
            return (False, 'bun check failed')
        
        logger.info(f"尝试 bun 安装: {path}")
        return self._run_command('bun install', path, timeout=600)

    def _install_cargo(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'Cargo.toml').exists():
            return (False, 'no Cargo.toml')
        
        try:
            result = subprocess.run(['which', 'cargo'], capture_output=True, text=True)
            if result.returncode != 0:
                return (False, 'cargo not installed')
        except Exception:
            return (False, 'cargo check failed')
        
        logger.info(f"尝试 cargo 构建: {path}")
        return self._run_command('cargo build --release', path, timeout=600)

    def _install_go(self, path: Path, project: Dict) -> Tuple[bool, str]:
        if not (path / 'go.mod').exists():
            return (False, 'no go.mod')
        
        try:
            result = subprocess.run(['which', 'go'], capture_output=True, text=True)
            if result.returncode != 0:
                return (False, 'go not installed')
        except Exception:
            return (False, 'go check failed')
        
        logger.info(f"尝试 go 构建: {path}")
        return self._run_command('go build ./...', path, timeout=600)
