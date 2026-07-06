#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class ArchitectureGenerator:
    def __init__(self, config):
        self.config = config
        self.arch_dir = Path(config.get('paths', {}).get('architecture', './Architecture'))
        self.arch_dir.mkdir(parents=True, exist_ok=True)

    def generate(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        safe_name = name.replace('/', '_').replace('\\', '_')
        
        logger.info(f"生成架构图: {name}")
        
        project['architecture_generated'] = False
        project['architecture_path'] = None
        
        arch_dir = self.arch_dir / safe_name
        arch_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            mermaid = self._generate_mermaid(project)
            plantuml = self._generate_plantuml(project)
            svg = self._generate_svg(project)
            
            with open(arch_dir / 'architecture.mmd', 'w', encoding='utf-8') as f:
                f.write(mermaid)
            
            with open(arch_dir / 'architecture.puml', 'w', encoding='utf-8') as f:
                f.write(plantuml)
            
            with open(arch_dir / 'architecture.svg', 'w', encoding='utf-8') as f:
                f.write(svg)
            
            project['architecture_generated'] = True
            project['architecture_path'] = str(arch_dir)
            
        except Exception as e:
            logger.error(f"生成架构图失败 {name}: {e}")
            project['architecture_error'] = str(e)
        
        return project

    def _generate_mermaid(self, project: Dict) -> str:
        name = project.get('name', '')
        project_type = project.get('project_type', 'unknown')
        tags = project.get('tags', [])
        language = project.get('primary_language', '')
        frameworks = project.get('frameworks', [])
        dep_files = project.get('dependency_files', [])
        
        mermaid = f"""%%{{init: {{'theme': 'dark'}}}}%%
graph TB
    User[用户] --> Interface[接口层]
    
    subgraph Interface[接口层]
        direction LR
        WebUI[Web UI]
        CLI[CLI]
        API[API 接口]
        MCP[MCP Server]
    end
    
    subgraph Core[核心层]
        direction TB
        Business[业务逻辑]
        AgentEngine[Agent 引擎]
        LLM[LLM 集成]
    end
    
    subgraph Data[数据层]
        direction LR
        Database[(数据库)]
        VectorDB[(向量数据库)]
        Cache[(缓存)]
        Files[文件存储]
    end
    
    subgraph Infra[基础设施]
        direction TB
        Docker[Docker 部署]
        CI/CD[CI/CD]
        Monitoring[监控]
    end
    
    Interface --> Core
    Core --> Data
    Core --> Infra
"""
        
        if 'MCP' in tags:
            mermaid = mermaid.replace('MCP[MCP Server]', 'MCP[MCP Server]:::highlight')
        
        if 'Agent' in tags:
            mermaid = mermaid.replace('AgentEngine[Agent 引擎]', 'AgentEngine[Agent 引擎]:::highlight')
        
        mermaid += f"""
    classDef highlight fill:#3b82f6,stroke:#60a5fa,stroke-width:2px,color:white
    
    %% 技术栈信息
    subgraph TechStack[技术栈]
        direction LR
        Lang[{language}]
        FW[{', '.join(frameworks[:3]) if frameworks else 'N/A'}]
        Deps[{', '.join(dep_files[:3]) if dep_files else 'N/A'}]
    end
"""
        
        return mermaid

    def _generate_plantuml(self, project: Dict) -> str:
        name = project.get('name', '')
        language = project.get('primary_language', '')
        frameworks = project.get('frameworks', [])
        
        plantuml = f"""@startuml
!theme plain
skinparam backgroundColor #1e1e2e
skinparam classAttributeIconSize 0
skinparam defaultFontColor #cdd6f4
skinparam classBackgroundColor #313244
skinparam classBorderColor #45475a
skinparam titleFontColor #cdd6f4
skinparam ArrowColor #89b4fa

title {name} 架构图

package "接口层" #313244 {{
    interface WebUI
    interface CLI
    interface RESTAPI
    interface MCPServer
}}

package "核心层" #313244 {{
    class ServiceLayer
    class AgentEngine
    class LLMIntegration
    class BusinessLogic
}}

package "数据层" #313244 {{
    database Database
    database VectorDB
    file FileStorage
    cache Cache
}}

package "基础设施" #313244 {{
    class DockerContainer
    class CI_CD
    class Monitoring
}}

WebUI --> ServiceLayer
CLI --> ServiceLayer
RESTAPI --> ServiceLayer
MCPServer --> ServiceLayer

ServiceLayer --> BusinessLogic
ServiceLayer --> AgentEngine
AgentEngine --> LLMIntegration

BusinessLogic --> Database
BusinessLogic --> VectorDB
AgentEngine --> Cache
LLMIntegration --> FileStorage

note right of LLMIntegration
  主要语言: {language}
  框架: {', '.join(frameworks[:3]) if frameworks else 'N/A'}
end note

@enduml
"""
        
        return plantuml

    def _generate_svg(self, project: Dict) -> str:
        name = project.get('name', 'System Architecture')
        tags = project.get('tags', [])
        language = project.get('primary_language', 'N/A')
        frameworks = project.get('frameworks', [])
        
        highlight_color = '#3b82f6'
        bg_color = '#1e1e2e'
        text_color = '#cdd6f4'
        box_color = '#313244'
        border_color = '#45475a'
        
        is_agent = 'Agent' in tags
        is_mcp = 'MCP' in tags
        
        svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" width="800" height="600">
  <style>
    .title {{ font-size: 20px; font-weight: bold; fill: {text_color}; font-family: sans-serif; }}
    .subtitle {{ font-size: 12px; fill: #9399b2; font-family: sans-serif; }}
    .box-title {{ font-size: 14px; font-weight: bold; fill: {text_color}; font-family: sans-serif; }}
    .box-text {{ font-size: 11px; fill: #bac2de; font-family: sans-serif; }}
    .layer-title {{ font-size: 13px; font-weight: bold; fill: #89b4fa; font-family: sans-serif; }}
  </style>
  
  <rect width="800" height="600" fill="{bg_color}"/>
  
  <text x="400" y="35" text-anchor="middle" class="title">{name} - Architecture</text>
  <text x="400" y="55" text-anchor="middle" class="subtitle">Language: {language} | Frameworks: {', '.join(frameworks[:3]) if frameworks else 'N/A'}</text>
  
  <text x="400" y="90" text-anchor="middle" class="layer-title">用户层 / User Layer</text>
  <rect x="300" y="105" width="200" height="50" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="400" y="135" text-anchor="middle" class="box-title">👤 用户</text>
  
  <line x1="400" y1="155" x2="400" y2="180" stroke="{border_color}" stroke-width="2" marker-end="url(#arrowhead)"/>
  
  <text x="400" y="200" text-anchor="middle" class="layer-title">接口层 / Interface Layer</text>
  <rect x="50" y="215" width="150" height="60" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="125" y="240" text-anchor="middle" class="box-title">Web UI</text>
  <text x="125" y="258" text-anchor="middle" class="box-text">前端界面</text>
  
  <rect x="220" y="215" width="150" height="60" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="295" y="240" text-anchor="middle" class="box-title">CLI</text>
  <text x="295" y="258" text-anchor="middle" class="box-text">命令行工具</text>
  
  <rect x="390" y="215" width="150" height="60" rx="8" fill="{box_color}" stroke="{highlight_color if is_mcp else border_color}" stroke-width="{'3' if is_mcp else '2'}"/>
  <text x="465" y="240" text-anchor="middle" class="box-title">{'🔌 MCP Server' if is_mcp else 'API Server'}</text>
  <text x="465" y="258" text-anchor="middle" class="box-text">{'模型上下文协议' if is_mcp else 'RESTful API'}</text>
  
  <rect x="560" y="215" width="150" height="60" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="635" y="240" text-anchor="middle" class="box-title">SDK</text>
  <text x="635" y="258" text-anchor="middle" class="box-text">开发工具包</text>
  
  <line x1="400" y1="275" x2="400" y2="300" stroke="{border_color}" stroke-width="2" marker-end="url(#arrowhead)"/>
  
  <text x="400" y="320" text-anchor="middle" class="layer-title">核心层 / Core Layer</text>
  <rect x="100" y="335" width="180" height="70" rx="8" fill="{box_color}" stroke="{highlight_color if is_agent else border_color}" stroke-width="{'3' if is_agent else '2'}"/>
  <text x="190" y="360" text-anchor="middle" class="box-title">{'🤖 Agent 引擎' if is_agent else '业务逻辑'}</text>
  <text x="190" y="380" text-anchor="middle" class="box-text">{'多代理协作' if is_agent else '核心功能模块'}</text>
  <text x="190" y="395" text-anchor="middle" class="box-text">{'任务编排' if is_agent else '业务流程'}</text>
  
  <rect x="310" y="335" width="180" height="70" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="400" y="360" text-anchor="middle" class="box-title">LLM 集成</text>
  <text x="400" y="380" text-anchor="middle" class="box-text">大语言模型调用</text>
  <text x="400" y="395" text-anchor="middle" class="box-text">多模型支持</text>
  
  <rect x="520" y="335" width="180" height="70" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="610" y="360" text-anchor="middle" class="box-title">工具集成</text>
  <text x="610" y="380" text-anchor="middle" class="box-text">外部工具调用</text>
  <text x="610" y="395" text-anchor="middle" class="box-text">插件系统</text>
  
  <line x1="400" y1="405" x2="400" y2="430" stroke="{border_color}" stroke-width="2" marker-end="url(#arrowhead)"/>
  
  <text x="400" y="450" text-anchor="middle" class="layer-title">数据层 / Data Layer</text>
  <rect x="100" y="465" width="130" height="60" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="165" y="490" text-anchor="middle" class="box-title">💾 数据库</text>
  <text x="165" y="508" text-anchor="middle" class="box-text">结构化数据</text>
  
  <rect x="250" y="465" width="130" height="60" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="315" y="490" text-anchor="middle" class="box-title">🔍 向量库</text>
  <text x="315" y="508" text-anchor="middle" class="box-text">RAG 检索</text>
  
  <rect x="400" y="465" width="130" height="60" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="465" y="490" text-anchor="middle" class="box-title">📦 缓存</text>
  <text x="465" y="508" text-anchor="middle" class="box-text">性能优化</text>
  
  <rect x="550" y="465" width="130" height="60" rx="8" fill="{box_color}" stroke="{border_color}" stroke-width="2"/>
  <text x="615" y="490" text-anchor="middle" class="box-title">📁 文件存储</text>
  <text x="615" y="508" text-anchor="middle" class="box-text">文档/媒体</text>
  
  <line x1="400" y1="525" x2="400" y2="545" stroke="{border_color}" stroke-width="2" marker-end="url(#arrowhead)"/>
  
  <text x="400" y="565" text-anchor="middle" class="layer-title">基础设施 / Infrastructure</text>
  <text x="400" y="585" text-anchor="middle" class="box-text">Docker • CI/CD • Monitoring • Logging</text>
  
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="{border_color}"/>
    </marker>
  </defs>
</svg>
'''
        return svg
