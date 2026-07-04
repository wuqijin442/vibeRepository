#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class ProjectScorer:
    def __init__(self, config):
        self.config = config
        scoring_config = config.get('scoring', {})
        self.heat_weight = scoring_config.get('heat_weight', 0.20)
        self.innovation_weight = scoring_config.get('innovation_weight', 0.20)
        self.completeness_weight = scoring_config.get('completeness_weight', 0.20)
        self.runtime_success_weight = scoring_config.get('runtime_success_weight', 0.20)
        self.actual_value_weight = scoring_config.get('actual_value_weight', 0.20)

    def score(self, project: Dict) -> Dict:
        name = project.get('name', 'unknown')
        
        logger.info(f"AI 评分: {name}")
        
        heat_score = self._calc_heat_score(project)
        innovation_score = self._calc_innovation_score(project)
        completeness_score = self._calc_completeness_score(project)
        runtime_score = self._calc_runtime_score(project)
        actual_value_score = self._calc_actual_value_score(project)
        
        total_score = (
            heat_score * self.heat_weight +
            innovation_score * self.innovation_weight +
            completeness_score * self.completeness_weight +
            runtime_score * self.runtime_success_weight +
            actual_value_score * self.actual_value_weight
        )
        
        total_score = round(total_score, 1)
        stars = self._score_to_stars(total_score)
        
        project['score'] = total_score
        project['score_breakdown'] = {
            'heat': round(heat_score, 1),
            'innovation': round(innovation_score, 1),
            'completeness': round(completeness_score, 1),
            'runtime': round(runtime_score, 1),
            'actual_value': round(actual_value_score, 1)
        }
        project['stars_count'] = stars
        project['stars_display'] = '★' * stars + '☆' * (5 - stars)
        
        logger.info(f"项目 {name} 评分: {total_score} ({project['stars_display']})")
        
        return project

    def _calc_heat_score(self, project: Dict) -> float:
        score = 0.0
        
        stars = project.get('stars', 0)
        daily_stars = project.get('daily_stars', 0)
        forks = project.get('forks', 0)
        
        if stars >= 10000:
            score += 40
        elif stars >= 5000:
            score += 35
        elif stars >= 1000:
            score += 30
        elif stars >= 500:
            score += 20
        elif stars >= 100:
            score += 10
        else:
            score += 5
        
        if daily_stars >= 500:
            score += 30
        elif daily_stars >= 100:
            score += 25
        elif daily_stars >= 50:
            score += 20
        elif daily_stars >= 10:
            score += 15
        elif daily_stars >= 5:
            score += 10
        elif daily_stars >= 1:
            score += 5
        else:
            score += 2
        
        if forks >= 1000:
            score += 30
        elif forks >= 500:
            score += 25
        elif forks >= 100:
            score += 20
        elif forks >= 50:
            score += 15
        elif forks >= 10:
            score += 10
        else:
            score += 5
        
        return min(score, 100)

    def _calc_innovation_score(self, project: Dict) -> float:
        score = 50.0
        
        tags = project.get('tags', [])
        description = project.get('description', '').lower()
        
        innovative_tags = ['Agent', 'Multi Agent', 'MCP', 'Vibe Coding', 'Browser Use', 'Computer Use']
        for tag in innovative_tags:
            if tag in tags:
                score += 10
        
        if any(kw in description for kw in ['first', 'novel', 'state-of-the-art', 'sota', 'breakthrough']):
            score += 10
        
        if project.get('frameworks', []):
            score += 5
        
        return min(score, 100)

    def _calc_completeness_score(self, project: Dict) -> float:
        score = 40.0
        
        if project.get('has_readme', False):
            score += 10
        
        if project.get('readme_has_demo', False):
            score += 10
        
        if project.get('readme_has_install', False):
            score += 10
        
        if project.get('readme_has_docs', False):
            score += 10
        
        if project.get('readme_length', 0) > 5000:
            score += 10
        elif project.get('readme_length', 0) > 2000:
            score += 5
        
        if project.get('license', '').lower() not in ['unknown', '']:
            score += 5
        
        if project.get('has_docker', False):
            score += 5
        
        examples_dir = False
        clone_path = project.get('clone_path')
        if clone_path:
            from pathlib import Path
            examples_dir = (Path(clone_path) / 'examples').exists()
        if examples_dir:
            score += 5
        
        return min(score, 100)

    def _calc_runtime_score(self, project: Dict) -> float:
        score = 0.0
        
        if project.get('install_success', False):
            score += 30
        else:
            return 10.0
        
        if project.get('run_success', False):
            score += 35
        else:
            return 30.0
        
        if project.get('demo_success', False):
            score += 35
        else:
            return 60.0
        
        startup_time = project.get('startup_time', 999)
        if startup_time <= 5:
            score += 5
        elif startup_time <= 10:
            score += 3
        
        return min(score, 100)

    def _calc_actual_value_score(self, project: Dict) -> float:
        score = 50.0
        
        tags = project.get('tags', [])
        use_cases = project.get('use_cases', [])
        
        high_value_tags = ['Coding', 'Agent', 'Workflow', 'MCP', 'DevTools']
        for tag in high_value_tags:
            if tag in tags:
                score += 10
        
        if len(use_cases) >= 3:
            score += 10
        elif len(use_cases) >= 1:
            score += 5
        
        if len(project.get('target_audience', [])) >= 2:
            score += 5
        
        if project.get('has_docker', False):
            score += 5
        
        advantages = project.get('advantages', [])
        if len(advantages) >= 4:
            score += 10
        elif len(advantages) >= 2:
            score += 5
        
        return min(score, 100)

    def _score_to_stars(self, score: float) -> int:
        if score >= 90:
            return 5
        elif score >= 80:
            return 4
        elif score >= 70:
            return 3
        elif score >= 60:
            return 2
        else:
            return 1
