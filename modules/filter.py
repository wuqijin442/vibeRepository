#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)


class ProjectFilter:
    def __init__(self, config):
        self.config = config
        self.categories = [c.lower() for c in config.get('project', {}).get('categories', [])]
        self.filter_keywords = [kw.lower() for kw in config.get('project', {}).get('filter_keywords', [])]

    def first_round(self, projects: List[Dict], target: int = 50) -> List[Dict]:
        logger.info(f"第一轮筛选: 从 {len(projects)} 个项目中筛选")
        
        filtered = []
        for project in projects:
            if self._matches_categories(project) and not self._is_filtered(project):
                score = self._calc_heat_score(project)
                project['heat_score'] = score
                filtered.append(project)
        
        filtered.sort(key=lambda x: x.get('heat_score', 0), reverse=True)
        result = filtered[:max(target, 50)]
        
        logger.info(f"第一轮筛选完成: {len(result)} 个项目")
        return result

    def second_round(self, projects: List[Dict], target: int = 20) -> List[Dict]:
        logger.info(f"第二轮筛选: 从 {len(projects)} 个项目中筛选")
        
        scored = []
        for project in projects:
            score = self._calc_quality_score(project)
            project['quality_score'] = score
            scored.append(project)
        
        scored.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        result = scored[:max(target, 20)]
        
        logger.info(f"第二轮筛选完成: {len(result)} 个项目")
        return result

    def third_round(self, projects: List[Dict], target: int = 10) -> List[Dict]:
        logger.info(f"第三轮筛选: 从 {len(projects)} 个项目中筛选")
        return projects[:max(target, 10)]

    def _matches_categories(self, project: Dict) -> bool:
        text = (
            project.get('name', '') + ' ' +
            project.get('description', '')
        ).lower()
        
        for category in self.categories:
            if category in text:
                return True
        
        return False

    def _is_filtered(self, project: Dict) -> bool:
        name = project.get('name', '').lower()
        desc = project.get('description', '').lower()
        text = name + ' ' + desc
        
        for keyword in self.filter_keywords:
            if keyword in text:
                return True
        
        if name.endswith('.github.io') or name.endswith('.github.com'):
            return True
        
        return False

    def _calc_heat_score(self, project: Dict) -> float:
        stars = project.get('stars', 0)
        daily_stars = project.get('daily_stars', 0)
        
        score = 0.0
        score += min(stars / 1000.0, 50)
        score += min(daily_stars / 50.0, 30)
        
        if 'github_trending' in project.get('source', ''):
            score += 10
        if 'hackernews' in project.get('source', ''):
            score += 5
        if project.get('hn_score', 0) > 100:
            score += 5
        
        return score

    def _calc_quality_score(self, project: Dict) -> float:
        score = project.get('heat_score', 0)
        
        if project.get('description'):
            score += 5
        
        if project.get('language'):
            score += 3
        
        if project.get('forks', 0) > 0:
            score += min(project['forks'] / 100.0, 10)
        
        if project.get('author'):
            score += 2
        
        if project.get('license'):
            score += 3
        
        if project.get('updated_at'):
            from datetime import datetime, timedelta
            try:
                updated = datetime.fromisoformat(project['updated_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now(updated.tzinfo) - updated).days
                if days_ago < 7:
                    score += 10
                elif days_ago < 30:
                    score += 5
                elif days_ago < 90:
                    score += 2
            except (ValueError, TypeError):
                pass
        
        return score
