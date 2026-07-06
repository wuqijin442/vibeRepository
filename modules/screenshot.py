#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import os
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)


class ScreenshotTaker:
    def __init__(self, config):
        self.config = config
        self.screenshots_dir = Path(config.get('paths', {}).get('screenshots', './workspace/screenshots'))
        self.demos_dir = Path(config.get('paths', {}).get('demos', './workspace/demos'))
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.demos_dir.mkdir(parents=True, exist_ok=True)
        self._check_dependencies()
    
    def _check_dependencies(self):
        self.has_ffmpeg = self._check_tool('ffmpeg')
        self.has_scrot = self._check_tool('scrot')
        logger.info(f"视频录制依赖: ffmpeg={'✓' if self.has_ffmpeg else '✗'}")
    
    def _check_tool(self, tool_name: str) -> bool:
        try:
            import subprocess
            result = subprocess.run(
                ['which', tool_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def take_screenshots(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        project_type = project.get('project_type', '')
        
        logger.info(f"截图录屏: {name}")
        
        project['screenshots'] = []
        project['demo_video'] = None
        project['demo_gif'] = None
        
        if project_type not in ['web_app', 'api_server', 'python_server']:
            logger.info(f"非 Web 项目，跳过截图: {project_type}")
            return project
        
        if not project.get('run_success', False):
            logger.info(f"项目未成功运行，跳过截图")
            return project
        
        safe_name = name.replace('/', '_').replace('\\', '_')
        project_screenshot_dir = self.screenshots_dir / safe_name
        project_screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            self._take_web_screenshots(project, project_screenshot_dir, safe_name)
            self._record_demo_video(project, project_screenshot_dir, safe_name)
        except Exception as e:
            logger.error(f"截图失败 {name}: {e}")
            project['screenshot_error'] = str(e)
        
        return project
    
    def _record_demo_video(self, project: Dict, save_dir: Path, safe_name: str):
        if not self.has_ffmpeg:
            logger.info("ffmpeg 未安装，跳过视频录制")
            return
        
        project_type = project.get('project_type', '')
        if project_type not in ['web_app', 'api_server', 'python_server']:
            return
        
        if not project.get('run_success', False):
            return
        
        port = self._detect_port(project)
        url = f'http://localhost:{port}'
        video_path = str(self.demos_dir / f'{safe_name}_demo.webm')
        gif_path = str(self.demos_dir / f'{safe_name}_demo.gif')
        
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1280, 'height': 720},
                    record_video_dir=str(self.demos_dir),
                    record_video_size={'width': 1280, 'height': 720}
                )
                page = context.new_page()
                
                try:
                    page.goto(url, timeout=30000, wait_until='networkidle')
                    time.sleep(2)
                    
                    for i in range(3):
                        try:
                            page.mouse.move(100 + i * 200, 200 + i * 100)
                            page.mouse.wheel(0, 500)
                            time.sleep(1)
                        except Exception:
                            continue
                    
                    context.close()
                    
                    video_files = list(self.demos_dir.glob(f'{safe_name}*.webm'))
                    if video_files:
                        latest_video = max(video_files, key=lambda x: x.stat().st_mtime)
                        final_video = self.demos_dir / f'{safe_name}_demo.webm'
                        if latest_video != final_video:
                            import shutil
                            shutil.move(str(latest_video), str(final_video))
                        project['demo_video'] = str(final_video)
                        logger.info(f"Demo 视频已保存: {final_video}")
                        
                        self._convert_to_gif(str(final_video), gif_path)
                        project['demo_gif'] = gif_path
                        logger.info(f"Demo GIF 已保存: {gif_path}")
                    
                except Exception as e:
                    logger.error(f"视频录制失败: {e}")
                
                browser.close()
                
        except ImportError:
            logger.warning("Playwright 未安装，跳过视频录制")
        except Exception as e:
            logger.error(f"视频录制异常: {e}")
    
    def _convert_to_gif(self, video_path: str, gif_path: str):
        if not self.has_ffmpeg or not os.path.exists(video_path):
            return
        
        try:
            import subprocess
            cmd = [
                'ffmpeg', '-y', '-i', video_path,
                '-vf', 'fps=10,scale=640:-1:flags=lanczos',
                '-c:v', 'gif', gif_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=60)
        except Exception as e:
            logger.debug(f"GIF 转换失败: {e}")

    def _take_web_screenshots(self, project: Dict, save_dir: Path, safe_name: str):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright 未安装，跳过截图")
            project['screenshot_error'] = 'playwright not installed'
            return
        
        port = self._detect_port(project)
        url = f'http://localhost:{port}'
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1920, 'height': 1080})
                
                try:
                    page.goto(url, timeout=30000, wait_until='networkidle')
                    time.sleep(2)
                    
                    home_screenshot = str(save_dir / 'homepage.png')
                    page.screenshot(path=home_screenshot, full_page=True)
                    project['screenshots'].append(home_screenshot)
                    logger.info(f"首页截图已保存: {home_screenshot}")
                    
                    nav_links = page.query_selector_all('nav a, header a, .nav a')
                    for i, link in enumerate(nav_links[:3]):
                        try:
                            href = link.get_attribute('href')
                            if href and not href.startswith('http'):
                                target_url = url + href if href.startswith('/') else url + '/' + href
                                page.goto(target_url, timeout=15000, wait_until='domcontentloaded')
                                time.sleep(1)
                                feature_screenshot = str(save_dir / f'feature_{i}.png')
                                page.screenshot(path=feature_screenshot, full_page=True)
                                project['screenshots'].append(feature_screenshot)
                        except Exception:
                            continue
                    
                except Exception as e:
                    logger.error(f"页面访问失败: {e}")
                
                browser.close()
                
        except Exception as e:
            logger.error(f"Playwright 截图异常: {e}")
            project['screenshot_error'] = str(e)

    def _detect_port(self, project: Dict) -> int:
        readme = project.get('readme_content', '').lower()
        clone_path = Path(project.get('clone_path', '.'))
        
        import re
        port_patterns = [
            r'port[\s:=]+(\d{2,5})',
            r'localhost:(\d{2,5})',
            r'127\.0\.0\.1:(\d{2,5})',
        ]
        
        for pattern in port_patterns:
            matches = re.findall(pattern, readme)
            for m in matches:
                port = int(m)
                if 1000 <= port <= 65535:
                    return port
        
        return 3000
