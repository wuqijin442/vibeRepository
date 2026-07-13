#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

import yaml

from modules.collector import DataCollector
from modules.filter import ProjectFilter
from modules.analyzer import ProjectAnalyzer
from modules.installer import ProjectInstaller
from modules.runner import ProjectRunner
from modules.tester import ProjectTester
from modules.screenshot import ScreenshotTaker
from modules.performance import PerformanceAnalyzer
from modules.competitor import CompetitorAnalyzer
from modules.documenter import DocumentGenerator
from modules.architect import ArchitectureGenerator
from modules.scoring import ProjectScorer
from modules.knowledge_base import KnowledgeBaseManager
from modules.reporter import ReportGenerator
from modules.github_sync import GitHubSyncer
from modules.failure_handler import FailureHandler
from modules.growth_tracker import GrowthTracker

Path('workspace/logs').mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'workspace/logs/main_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class AIDailyWorkflow:
    def __init__(self, config_path='config.yaml'):
        self.config = self._load_config(config_path)
        self._init_directories()
        self.today = datetime.now().strftime('%Y-%m-%d')
        self.weekday = datetime.now().weekday()
        self.is_sunday = (self.weekday == 6)
        self.is_month_end = self._check_month_end()
        
        self.collector = DataCollector(self.config)
        self.project_filter = ProjectFilter(self.config)
        self.analyzer = ProjectAnalyzer(self.config)
        self.installer = ProjectInstaller(self.config)
        self.runner = ProjectRunner(self.config)
        self.tester = ProjectTester(self.config)
        self.screenshot_taker = ScreenshotTaker(self.config)
        self.perf_analyzer = PerformanceAnalyzer(self.config)
        self.competitor_analyzer = CompetitorAnalyzer(self.config)
        self.documenter = DocumentGenerator(self.config)
        self.architect = ArchitectureGenerator(self.config)
        self.scorer = ProjectScorer(self.config)
        self.kb_manager = KnowledgeBaseManager(self.config)
        self.reporter = ReportGenerator(self.config)
        self.github_syncer = GitHubSyncer(self.config)
        self.failure_handler = FailureHandler(self.config)
        self.growth_tracker = GrowthTracker(self.config)

        self.stats = {
            'scanned': 0,
            'filtered': 0,
            'cloned': 0,
            'installed': 0,
            'ran': 0,
            'demo_passed': 0,
            'recommended': 0,
            'synced': 0,
            'failed_projects': []
        }

    def _load_config(self, config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _init_directories(self):
        dirs = [
            'workspace',
            'workspace/clones',
            'workspace/screenshots',
            'workspace/demos',
            'workspace/logs',
            'Knowledge-Base',
            'Daily-Reports',
            'Weekly-Reports',
            'Monthly-Reports',
            'Awesome-Projects',
            'Benchmarks',
            'Reviews',
            'Architecture',
            'Metadata',
            'Rankings'
        ]
        for d in dirs:
            Path(d).mkdir(parents=True, exist_ok=True)

    def _check_month_end(self):
        today = datetime.now()
        next_day = today.replace(day=28) + __import__('datetime').timedelta(days=4)
        return (next_day - __import__('datetime').timedelta(days=next_day.day)).day == today.day

    def run(self):
        logger.info("=" * 60)
        logger.info(f"AI 开源项目每日工作流启动 - {self.today}")
        logger.info("=" * 60)

        try:
            self._step_1_collect()
            self._step_2_filter()
            self._step_2_5_track_growth()
            self._step_3_analyze()
            self._step_4_install()
            self._step_5_run()
            self._step_6_test()
            self._step_7_screenshot()
            self._step_8_performance()
            self._step_9_competitor()
            self._step_10_document()
            self._step_11_architecture()
            self._step_12_score()
            self._step_13_knowledge_base()
            self._step_13_5_kb_daily_scan()
            self._step_14_report()
            self._step_14_5_save_ranking()
            self._step_15_github_sync()
            
            logger.info("=" * 60)
            logger.info("工作流执行完成！")
            logger.info(f"扫描: {self.stats['scanned']} | 筛选: {self.stats['filtered']} | "
                       f"Clone: {self.stats['cloned']} | 安装: {self.stats['installed']} | "
                       f"运行: {self.stats['ran']} | Demo: {self.stats['demo_passed']} | "
                       f"推荐: {self.stats['recommended']}")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"工作流执行出错: {e}", exc_info=True)
            self._generate_fallback_report()

    def _step_1_collect(self):
        logger.info("[步骤1] 数据采集...")
        projects = self.collector.collect_all()
        self.stats['scanned'] = len(projects)
        logger.info(f"共采集到 {len(projects)} 个项目")
        self.raw_projects = projects

    def _step_2_filter(self):
        logger.info("[步骤2] 项目筛选...")
        round1 = self.project_filter.first_round(self.raw_projects)
        logger.info(f"第一轮筛选后: {len(round1)} 个项目 (目标: 50)")
        
        round2 = self.project_filter.second_round(round1)
        logger.info(f"第二轮筛选后: {len(round2)} 个项目 (目标: 20)")
        
        round3 = self.project_filter.third_round(round2)
        
        if self.is_sunday:
            top_n = 10
            round3 = sorted(round3, key=lambda x: x.get('stars', 0), reverse=True)[:top_n]
        else:
            top_n = 5
            round3 = sorted(round3, key=lambda x: x.get('daily_stars', 0), reverse=True)[:top_n]
        
        self.stats['filtered'] = len(round3)
        logger.info(f"第三轮筛选后: {len(round3)} 个项目 (TOP {top_n})")
        self.filtered_projects = round3

    def _step_2_5_track_growth(self):
        logger.info("[步骤2.5] 增长趋势追踪...")
        # 对全部采集项目追踪增长趋势（用于飙升榜 TOP 10）
        self.all_growth_projects = []
        for project in self.raw_projects:
            try:
                growth_data = self.growth_tracker.track_growth(project)
                p = dict(project)
                p['daily_growth'] = growth_data.get('daily_growth', 0)
                p['weekly_growth'] = growth_data.get('weekly_growth', 0)
                p['monthly_growth'] = growth_data.get('monthly_growth', 0)
                # 回退使用 Trending 的 daily_stars
                if p['daily_growth'] == 0:
                    p['daily_growth'] = project.get('daily_stars', 0)
                if p['weekly_growth'] == 0:
                    p['weekly_growth'] = project.get('weekly_stars', 0)
                if p['monthly_growth'] == 0:
                    p['monthly_growth'] = project.get('monthly_stars', 0)
                self.all_growth_projects.append(p)
            except Exception as e:
                logger.error(f"增长追踪 {project.get('name', 'unknown')} 失败: {e}")
                p = dict(project)
                p['daily_growth'] = project.get('daily_stars', 0)
                p['weekly_growth'] = project.get('weekly_stars', 0)
                p['monthly_growth'] = project.get('monthly_stars', 0)
                self.all_growth_projects.append(p)

        # 同步给筛选项目
        growth_map = {p['name']: p for p in self.all_growth_projects if 'name' in p}
        for project in self.filtered_projects:
            g = growth_map.get(project.get('name'), {})
            project['daily_growth'] = g.get('daily_growth', project.get('daily_stars', 0))
            project['weekly_growth'] = g.get('weekly_growth', 0)
            project['monthly_growth'] = g.get('monthly_growth', 0)

        # 对飙升榜 TOP 10 补全 GitHub API 数据（开源时间、forks、license）
        try:
            top_for_enrich = self.growth_tracker.get_daily_ranking(self.all_growth_projects, top_n=10)
            if top_for_enrich:
                self.collector.enrich_with_github_data(top_for_enrich, top_n=10)
                # 回写补全的数据到 all_growth_projects
                enrich_map = {p.get('name'): p for p in top_for_enrich if p.get('name')}
                for p in self.all_growth_projects:
                    ep = enrich_map.get(p.get('name'))
                    if ep:
                        if ep.get('created_at'):
                            p['created_at'] = ep['created_at']
                        if ep.get('open_source_date'):
                            p['open_source_date'] = ep['open_source_date']
                        if ep.get('forks'):
                            p['forks'] = ep['forks']
                        if ep.get('license'):
                            p['license'] = ep['license']
                logger.info("飙升榜 TOP 10 GitHub 数据补全完成")
        except Exception as e:
            logger.warning(f"GitHub 数据补全失败（不影响主流程）: {e}")

        logger.info(f"增长趋势追踪完成（{len(self.all_growth_projects)} 个项目）")

    def _step_3_analyze(self):
        logger.info("[步骤3] 项目分析...")
        analyzed = []
        for project in self.filtered_projects:
            try:
                result = self.analyzer.analyze(project)
                if result.get('cloned', False):
                    self.stats['cloned'] += 1
                analyzed.append(result)
            except Exception as e:
                logger.error(f"分析项目 {project.get('name', 'unknown')} 失败: {e}")
                project['error'] = str(e)
                self.stats['failed_projects'].append(project)
        self.analyzed_projects = analyzed
        logger.info(f"成功分析 {len(analyzed)} 个项目")

    def _step_4_install(self):
        logger.info("[步骤4] 自动安装...")
        installed = []
        for project in self.analyzed_projects:
            try:
                result = self.installer.install(project)
                if result.get('install_success', False):
                    self.stats['installed'] += 1
                installed.append(result)
            except Exception as e:
                logger.error(f"安装项目 {project.get('name', 'unknown')} 失败: {e}")
                project['install_error'] = str(e)
                self.stats['failed_projects'].append(project)
        self.installed_projects = installed
        logger.info(f"成功安装 {self.stats['installed']} 个项目")

    def _step_5_run(self):
        logger.info("[步骤5] 真实运行...")
        ran = []
        for project in self.installed_projects:
            if not project.get('install_success', False):
                ran.append(project)
                continue
            try:
                result = self.runner.run(project)
                if result.get('run_success', False):
                    self.stats['ran'] += 1
                ran.append(result)
            except Exception as e:
                logger.error(f"运行项目 {project.get('name', 'unknown')} 失败: {e}")
                project['run_error'] = str(e)
                self.stats['failed_projects'].append(project)
        self.ran_projects = ran
        logger.info(f"成功运行 {self.stats['ran']} 个项目")

    def _step_6_test(self):
        logger.info("[步骤6] 真实测试...")
        tested = []
        for project in self.ran_projects:
            if not project.get('run_success', False):
                tested.append(project)
                continue
            try:
                result = self.tester.test(project)
                if result.get('demo_success', False):
                    self.stats['demo_passed'] += 1
                tested.append(result)
            except Exception as e:
                logger.error(f"测试项目 {project.get('name', 'unknown')} 失败: {e}")
                project['test_error'] = str(e)
                self.stats['failed_projects'].append(project)
        self.tested_projects = tested
        logger.info(f"Demo成功 {self.stats['demo_passed']} 个项目")

    def _step_7_screenshot(self):
        logger.info("[步骤7] 截图录屏...")
        screenshot_projects = []
        for project in self.tested_projects:
            try:
                result = self.screenshot_taker.take_screenshots(project)
                screenshot_projects.append(result)
            except Exception as e:
                logger.error(f"截图项目 {project.get('name', 'unknown')} 失败: {e}")
                screenshot_projects.append(project)
        self.tested_projects = screenshot_projects

    def _step_8_performance(self):
        logger.info("[步骤8] 性能分析...")
        perf_projects = []
        for project in self.tested_projects:
            try:
                result = self.perf_analyzer.analyze(project)
                perf_projects.append(result)
            except Exception as e:
                logger.error(f"性能分析 {project.get('name', 'unknown')} 失败: {e}")
                perf_projects.append(project)
        self.tested_projects = perf_projects

    def _step_9_competitor(self):
        logger.info("[步骤9] 竞品分析...")
        comp_projects = []
        for project in self.tested_projects:
            try:
                result = self.competitor_analyzer.analyze(project)
                comp_projects.append(result)
            except Exception as e:
                logger.error(f"竞品分析 {project.get('name', 'unknown')} 失败: {e}")
                comp_projects.append(project)
        self.tested_projects = comp_projects

    def _step_10_document(self):
        logger.info("[步骤10] 生成中文文档...")
        doc_projects = []
        for project in self.tested_projects:
            try:
                result = self.documenter.generate(project)
                doc_projects.append(result)
            except Exception as e:
                logger.error(f"生成文档 {project.get('name', 'unknown')} 失败: {e}")
                doc_projects.append(project)
        self.tested_projects = doc_projects

    def _step_11_architecture(self):
        logger.info("[步骤11] 生成架构图...")
        arch_projects = []
        for project in self.tested_projects:
            try:
                result = self.architect.generate(project)
                arch_projects.append(result)
            except Exception as e:
                logger.error(f"生成架构图 {project.get('name', 'unknown')} 失败: {e}")
                arch_projects.append(project)
        self.tested_projects = arch_projects

    def _step_12_score(self):
        logger.info("[步骤12] AI评分...")
        scored = []
        for project in self.tested_projects:
            try:
                result = self.scorer.score(project)
                scored.append(result)
                if result.get('score', 0) >= 90 and result.get('stars_count', 0) >= 4:
                    self.stats['recommended'] += 1
            except Exception as e:
                logger.error(f"评分 {project.get('name', 'unknown')} 失败: {e}")
                project['score_error'] = str(e)
                scored.append(project)
        self.scored_projects = scored
        logger.info(f"推荐项目 {self.stats['recommended']} 个")

    def _step_13_knowledge_base(self):
        logger.info("[步骤13] 知识库整理...")
        for project in self.scored_projects:
            try:
                self.kb_manager.add_project(project)
            except Exception as e:
                logger.error(f"知识库整理 {project.get('name', 'unknown')} 失败: {e}")
                self.failure_handler.record_failure(
                    project.get('name', 'unknown'),
                    'knowledge_base',
                    e,
                    suggestion='检查项目数据完整性'
                )

    def _step_13_5_kb_daily_scan(self):
        logger.info("[步骤13.5] 知识库每日扫描...")
        try:
            scan_results = self.kb_manager.daily_scan()
            logger.info(f"知识库扫描完成: {scan_results.get('total', 0)} 个项目, "
                       f"{scan_results.get('updated', 0)} 个更新, "
                       f"{scan_results.get('new_releases', 0)} 个新版本")
            self.stats['kb_scan_results'] = scan_results
        except Exception as e:
            logger.error(f"知识库每日扫描失败: {e}")

    def _step_14_report(self):
        logger.info("[步骤14] 生成报告...")
        self.reporter.generate_daily_report(
            self.scored_projects,
            self.stats,
            self.today,
            failure_handler=self.failure_handler,
            growth_data=self.all_growth_projects
        )
        
        if self.is_sunday:
            logger.info("生成周报...")
            self.reporter.generate_weekly_report(self.today)
        
        if self.is_month_end:
            logger.info("生成月报...")
            self.reporter.generate_monthly_report(self.today)

    def _step_14_5_save_ranking(self):
        logger.info("[步骤14.5] 保存飙升榜单...")
        try:
            # 使用全部采集项目按日增长排序，取 TOP 10
            ranking_projects = self.growth_tracker.get_daily_ranking(
                self.all_growth_projects, top_n=10
            )
            ranking_path = self.growth_tracker.save_ranking_snapshot(
                ranking_projects, self.today
            )
            logger.info(f"飙升榜单已保存: {ranking_path}")
        except Exception as e:
            logger.error(f"保存飙升榜单失败: {e}")

    def _step_15_github_sync(self):
        if not self.config.get('github_sync', {}).get('enabled', False):
            logger.info("[步骤15] GitHub同步已禁用，跳过")
            return
        
        logger.info("[步骤15] GitHub同步...")
        try:
            synced = self.github_syncer.sync(self.today)
            self.stats['synced'] = synced
            logger.info(f"同步成功 {synced} 个文件")
        except Exception as e:
            logger.error(f"GitHub同步失败: {e}")

    def _generate_fallback_report(self):
        report_path = f"Daily-Reports/{self.today}_Report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# Today's Report - {self.today}\n\n")
            f.write(f"**⚠️ 工作流执行出错**\n\n")
            f.write(f"扫描数量: {self.stats['scanned']}\n")
            f.write(f"失败项目数: {len(self.stats['failed_projects'])}\n")
        
        logger.info(f"已生成降级报告: {report_path}")


def main():
    workflow = AIDailyWorkflow()
    workflow.run()


if __name__ == '__main__':
    main()
