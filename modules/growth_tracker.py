#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GrowthTracker:
    def __init__(self, config):
        self.config = config
        self.metadata_dir = Path(config.get('paths', {}).get('metadata', './Metadata'))
        self.rankings_dir = Path(config.get('paths', {}).get('rankings', './Rankings'))
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.rankings_dir.mkdir(parents=True, exist_ok=True)

    def track_growth(self, project: dict) -> dict:
        name = project.get('name', 'unknown')
        stars = project.get('stars', 0)
        logger.info(f"追踪 Star 增长: {name}")

        growth = self._compute_growth(name, stars)
        today = growth['date']
        daily = growth['daily_growth']
        star_history = growth['star_history']

        star_history = [e for e in star_history if e.get('date') != today]
        star_history.append({'date': today, 'stars': stars, 'daily_growth': daily})
        self._save_history(name, {'name': name, 'star_history': star_history})

        return {
            'name': name,
            'date': today,
            'stars': stars,
            'daily_growth': daily,
            'weekly_growth': growth['weekly_growth'],
            'monthly_growth': growth['monthly_growth'],
        }

    def get_daily_ranking(self, projects: list, top_n: int = 10) -> list:
        logger.info(f"生成日增长排名 (top {top_n})")

        enriched = []
        for p in projects:
            name = p.get('name', 'unknown')
            stars = p.get('stars', 0)
            if 'daily_growth' in p:
                growth = {
                    'daily_growth': p.get('daily_growth', 0),
                    'weekly_growth': p.get('weekly_growth', 0),
                    'monthly_growth': p.get('monthly_growth', 0),
                }
            else:
                g = self._compute_growth(name, stars)
                growth = {
                    'daily_growth': g['daily_growth'],
                    'weekly_growth': g['weekly_growth'],
                    'monthly_growth': g['monthly_growth'],
                }
            item = dict(p)
            item.update(growth)
            enriched.append(item)

        enriched.sort(key=lambda x: x.get('daily_growth', 0), reverse=True)
        return enriched[:top_n]

    def get_growth_summary(self, project_name: str) -> dict:
        star_history = self._load_history(project_name).get('star_history', [])
        latest = star_history[-1] if star_history else {}

        logger.info(f"获取增长摘要: {project_name} (共 {len(star_history)} 条记录)")
        return {
            'name': project_name,
            'total_records': len(star_history),
            'latest_date': latest.get('date', ''),
            'latest_stars': latest.get('stars', 0),
            'latest_daily_growth': latest.get('daily_growth', 0),
            'star_history': star_history,
        }

    def save_ranking_snapshot(self, projects: list, date_str: str) -> str:
        logger.info(f"保存排名快照: {date_str}")

        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            dt = datetime.now()
            date_str = dt.strftime('%Y-%m-%d')

        snapshot_dir = self.rankings_dir / f"{dt.year:04d}" / f"{dt.month:02d}"
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        content = self._build_ranking_markdown(projects, date_str)
        file_path = snapshot_dir / f"{date_str}_ranking.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        logger.info(f"排名快照已保存: {file_path}")
        return str(file_path)

    def _compute_growth(self, name: str, stars: int) -> dict:
        today = datetime.now().strftime('%Y-%m-%d')
        star_history = self._load_history(name).get('star_history', [])
        return {
            'date': today,
            'daily_growth': self._calc_growth(stars, star_history, today, 1),
            'weekly_growth': self._calc_growth(stars, star_history, today, 7),
            'monthly_growth': self._calc_growth(stars, star_history, today, 30),
            'star_history': star_history,
        }

    def _calc_growth(self, stars: int, star_history: list, today: str, days: int) -> int:
        target = (datetime.strptime(today, '%Y-%m-%d') - timedelta(days=days)).strftime('%Y-%m-%d')
        prev = self._get_stars_on_date(star_history, target)
        if prev is None:
            return 0
        return stars - prev

    def _get_stars_on_date(self, star_history: list, target_date: str):
        try:
            target = datetime.strptime(target_date, '%Y-%m-%d')
        except (ValueError, TypeError):
            return None

        fallback_date = None
        fallback_stars = None
        for entry in star_history:
            try:
                entry_date = datetime.strptime(entry.get('date', ''), '%Y-%m-%d')
            except (ValueError, TypeError):
                continue
            if entry_date == target:
                return entry.get('stars', 0)
            if entry_date < target:
                if fallback_date is None or entry_date > fallback_date:
                    fallback_date = entry_date
                    fallback_stars = entry.get('stars', 0)
        return fallback_stars

    def _load_history(self, name: str) -> dict:
        file_path = self.metadata_dir / f"{self._safe_name(name)}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载历史数据失败 {name}: {e}")
        return {'name': name, 'star_history': []}

    def _save_history(self, name: str, history: dict):
        file_path = self.metadata_dir / f"{self._safe_name(name)}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存历史数据失败 {name}: {e}")

    def _build_ranking_markdown(self, projects: list, date_str: str) -> str:
        lines = [f"# 📈 GitHub 飙升榜 - {date_str}", ""]
        lines.append("| 排名 | 项目名 | Star⭐ | 日增长🔺 | 周增长🔺 | 月增长🔺 | 开源时间 | 语言 |")
        lines.append("|---|---|---|---|---|---|---|---|")

        for i, p in enumerate(projects, 1):
            name = p.get('name', 'unknown')
            stars = self._format_stars(p.get('stars', 0))
            daily = p.get('daily_growth', 0)
            weekly = p.get('weekly_growth', 0)
            monthly = p.get('monthly_growth', 0)
            created = p.get('created_at', p.get('open_source_date', 'N/A'))
            language = p.get('primary_language', p.get('language', 'Unknown'))
            lines.append(
                f"| {i} | {name} | {stars} | 🔺{daily} | 🔺{weekly} | 🔺{monthly} | {created} | {language} |"
            )

        lines.append("")
        return "\n".join(lines)

    def _format_stars(self, stars) -> str:
        try:
            stars = int(stars)
        except (ValueError, TypeError):
            stars = 0
        if stars >= 1000000:
            return f"{stars / 1000000:.1f}M"
        if stars >= 1000:
            return f"{stars / 1000:.1f}k"
        return str(stars)

    def _safe_name(self, name: str) -> str:
        return name.replace('/', '_').replace('\\', '_')
