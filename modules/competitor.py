#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class CompetitorAnalyzer:
    def __init__(self, config):
        self.config = config

    def analyze(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        tags = project.get('tags', [])
        description = project.get('description', '')
        
        logger.info(f"竞品分析: {name}")
        
        project['competitors'] = []
        project['advantages'] = []
        project['disadvantages'] = []
        project['target_audience'] = []
        project['use_cases'] = []
        
        project['competitors'] = self._find_competitors(project)
        project['advantages'] = self._analyze_advantages(project)
        project['disadvantages'] = self._analyze_disadvantages(project)
        project['target_audience'] = self._identify_audience(project)
        project['use_cases'] = self._identify_use_cases(project)
        
        return project

    def _find_competitors(self, project: Dict) -> List[str]:
        tags = project.get('tags', [])
        competitors = []
        
        competitor_map = {
            'Agent': ['AutoGPT', 'LangChain', 'CrewAI', 'AutoGen'],
            'LLM': ['Ollama', 'llama.cpp', 'vLLM', 'Text Generation WebUI'],
            'RAG': ['LlamaIndex', 'LangChain RAG', 'Haystack', 'Qdrant'],
            'MCP': ['MCP Servers Collection', 'modelcontextprotocol/servers'],
            'Coding': ['Continue', 'Cursor', 'Claude Code', 'aider'],
            'Workflow': ['n8n', 'LangFlow', 'Dify', 'Flowise'],
            'Browser Use': ['Playwright', 'Puppeteer', 'Browserbase'],
            'Image Gen': ['ComfyUI', 'Stable Diffusion WebUI', 'Fooocus'],
            'Voice': ['Whisper', 'Coqui TTS', 'Bark', 'XTTS'],
        }
        
        for tag in tags:
            if tag in competitor_map:
                competitors.extend(competitor_map[tag])
        
        return list(set(competitors))[:5]

    def _analyze_advantages(self, project: Dict) -> List[str]:
        advantages = []
        readme = project.get('readme_content', '').lower()
        tags = project.get('tags', [])
        
        if project.get('stars', 0) > 1000:
            advantages.append('社区热度高，Star 数量多')
        
        if project.get('readme_has_docs', False):
            advantages.append('文档完善')
        
        if project.get('has_docker', False):
            advantages.append('支持 Docker 部署')
        
        if project.get('install_success', False):
            advantages.append('安装简单，依赖易解决')
        
        if project.get('run_success', False):
            advantages.append('运行稳定，启动快')
        
        if 'open source' in readme or 'opensource' in readme:
            advantages.append('完全开源')
        
        if 'no api key' in readme or 'local' in readme:
            advantages.append('支持本地运行，保护隐私')
        
        if not advantages:
            advantages.append('项目处于早期阶段，有增长潜力')
        
        return advantages[:5]

    def _analyze_disadvantages(self, project: Dict) -> List[str]:
        disadvantages = []
        readme = project.get('readme_content', '').lower()
        
        if not project.get('install_success', False):
            disadvantages.append('安装可能存在依赖问题')
        
        if not project.get('run_success', False):
            disadvantages.append('运行稳定性待验证')
        
        if project.get('stars', 0) < 100:
            disadvantages.append('社区较小，生态待完善')
        
        if not project.get('readme_has_docs', False):
            disadvantages.append('文档不够完善')
        
        if project.get('readme_length', 0) < 500:
            disadvantages.append('README 信息较少')
        
        if not disadvantages:
            disadvantages.append('需要更多实际使用验证')
        
        return disadvantages[:5]

    def _identify_audience(self, project: Dict) -> List[str]:
        audience = []
        tags = project.get('tags', [])
        
        if 'Coding' in tags or 'DevTools' in tags:
            audience.extend(['开发者', '程序员'])
        if 'Agent' in tags:
            audience.extend(['AI 研究者', '自动化爱好者'])
        if 'RAG' in tags or 'LLM' in tags:
            audience.extend(['AI 工程师', '数据科学家'])
        if 'Workflow' in tags or 'Automation' in tags:
            audience.extend(['运维工程师', '产品经理'])
        if 'Image Gen' in tags:
            audience.extend(['设计师', '内容创作者'])
        if 'Voice' in tags:
            audience.extend(['语音开发者', '播客创作者'])
        if 'Local AI' in tags:
            audience.extend(['隐私关注者', '企业用户'])
        
        if not audience:
            audience = ['AI 爱好者', '技术研究者']
        
        return list(set(audience))

    def _identify_use_cases(self, project: Dict) -> List[str]:
        use_cases = []
        tags = project.get('tags', [])
        description = project.get('description', '').lower()
        
        if 'Agent' in tags:
            use_cases.extend(['自动化任务执行', '多代理协作', '智能客服'])
        if 'Coding' in tags:
            use_cases.extend(['代码生成', '代码审查', '重构辅助'])
        if 'RAG' in tags:
            use_cases.extend(['知识库问答', '文档智能检索', '企业内部搜索'])
        if 'Workflow' in tags:
            use_cases.extend(['工作流自动化', '业务流程编排', '任务调度'])
        if 'Image Gen' in tags:
            use_cases.extend(['图像生成', '设计辅助', '内容创作'])
        if 'Voice' in tags:
            use_cases.extend(['语音转文字', '文字转语音', '语音助手'])
        if 'MCP' in tags:
            use_cases.extend(['AI 工具集成', '模型上下文协议', '多工具协同'])
        if 'Browser Use' in tags:
            use_cases.extend(['网页自动化', '数据采集', 'UI 测试'])
        
        if not use_cases:
            use_cases = ['AI 应用开发', '技术研究探索']
        
        return list(set(use_cases))[:5]
