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
            
            with open(arch_dir / 'architecture.mmd', 'w', encoding='utf-8') as f:
                f.write(mermaid)
            
            with open(arch_dir / 'architecture.puml', 'w', encoding='utf-8') as f:
                f.write(plantuml)
            
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
