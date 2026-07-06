#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import json
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class FailureHandler:
    def __init__(self, config):
        self.config = config
        self.logs_dir = Path(config.get('paths', {}).get('logs', './workspace/logs'))
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.failures = []

    def record_failure(self, project_name: str, step: str, error: Exception, 
                       context: Dict = None, suggestion: str = ''):
        failure = {
            'project': project_name,
            'step': step,
            'error': str(error),
            'error_type': type(error).__name__,
            'traceback': traceback.format_exc(),
            'context': context or {},
            'suggestion': suggestion,
            'timestamp': datetime.now().isoformat()
        }
        
        self.failures.append(failure)
        
        logger.error(f"[失败] {project_name} - {step}: {error}")
        if suggestion:
            logger.info(f"  建议: {suggestion}")
        
        self._save_failure_log(failure)
        
        return failure

    def _save_failure_log(self, failure: Dict):
        try:
            date_str = datetime.now().strftime('%Y%m%d')
            log_file = self.logs_dir / f'failures_{date_str}.json'
            
            all_failures = []
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        all_failures = json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
            
            all_failures.append(failure)
            
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(all_failures, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.debug(f"保存失败日志出错: {e}")

    def get_failures(self, step: str = None, project: str = None) -> List[Dict]:
        result = self.failures
        
        if step:
            result = [f for f in result if f['step'] == step]
        if project:
            result = [f for f in result if f['project'] == project]
        
        return result

    def get_failure_summary(self) -> Dict:
        summary = {
            'total': len(self.failures),
            'by_step': {},
            'by_type': {},
            'projects': []
        }
        
        for f in self.failures:
            step = f['step']
            summary['by_step'][step] = summary['by_step'].get(step, 0) + 1
            
            err_type = f['error_type']
            summary['by_type'][err_type] = summary['by_type'].get(err_type, 0) + 1
            
            if f['project'] not in summary['projects']:
                summary['projects'].append(f['project'])
        
        return summary

    def generate_failure_report(self) -> str:
        summary = self.get_failure_summary()
        
        report = f"""## 失败统计

- **总失败数**: {summary['total']}
- **涉及项目**: {len(summary['projects'])} 个

### 按步骤分布

| 步骤 | 失败数 |
|------|--------|
"""
        
        for step, count in sorted(summary['by_step'].items(), key=lambda x: x[1], reverse=True):
            report += f"| {step} | {count} |\n"
        
        report += "\n### 按错误类型分布\n\n| 错误类型 | 数量 |\n|----------|------|\n"
        
        for err_type, count in sorted(summary['by_type'].items(), key=lambda x: x[1], reverse=True):
            report += f"| {err_type} | {count} |\n"
        
        if self.failures:
            report += "\n### 失败详情\n\n"
            for i, f in enumerate(self.failures[:20], 1):
                report += f"**{i}. {f['project']}** - {f['step']}\n"
                report += f"- 错误: {f['error'][:200]}\n"
                if f.get('suggestion'):
                    report += f"- 建议: {f['suggestion']}\n"
                report += "\n"
        
        return report

    def reset(self):
        self.failures = []
