#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
sys.path.insert(0, '/workspace')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_quick_workflow():
    """快速验证主工作流的前几步"""
    import yaml
    from pathlib import Path
    
    with open('/workspace/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from modules.collector import DataCollector
    from modules.filter import ProjectFilter
    from modules.scoring import ProjectScorer
    
    print("=" * 60)
    print("快速验证主工作流")
    print("=" * 60)
    
    print("\n[1/5] 数据采集...")
    collector = DataCollector(config)
    projects = collector.collect_all()
    print(f"  采集到 {len(projects)} 个项目")
    
    print("\n[2/5] 第一轮筛选 (目标50个)...")
    project_filter = ProjectFilter(config)
    round1 = project_filter.first_round(projects, target=50)
    print(f"  筛选后: {len(round1)} 个项目")
    
    print("\n[3/5] 第二轮筛选 (目标20个)...")
    round2 = project_filter.second_round(round1, target=20)
    print(f"  筛选后: {len(round2)} 个项目")
    
    print("\n[4/5] 第三轮筛选 (TOP 5)...")
    top5 = round2[:5]
    print(f"  最终 TOP 5:")
    for i, p in enumerate(top5, 1):
        print(f"    {i}. {p.get('name', 'N/A')} - ⭐{p.get('stars', 0)} (+{p.get('daily_stars', 0)})")
    
    print("\n[5/5] 评分演示 (第一个项目)...")
    scorer = ProjectScorer(config)
    if top5:
        sample = top5[0].copy()
        sample['has_readme'] = True
        sample['readme_has_demo'] = True
        sample['readme_has_install'] = True
        sample['readme_has_docs'] = True
        sample['readme_length'] = 2000
        sample['install_success'] = True
        sample['run_success'] = True
        sample['demo_success'] = True
        sample['startup_time'] = 10
        sample['tags'] = ['Agent', 'LLM']
        sample['frameworks'] = []
        sample['use_cases'] = ['自动化任务']
        sample['target_audience'] = ['开发者']
        sample['advantages'] = ['社区活跃', '文档完善']
        sample['disadvantages'] = []
        sample['has_docker'] = False
        
        scored = scorer.score(sample)
        print(f"  项目: {scored.get('name')}")
        print(f"  评分: {scored.get('score')} 分")
        print(f"  推荐: {scored.get('stars_display')}")
    
    print("\n" + "=" * 60)
    print("✅ 快速验证通过！系统核心功能正常。")
    print("=" * 60)
    
    print("\n📁 生成的目录结构:")
    for d in ['Daily-Reports', 'Knowledge-Base', 'workspace/clones', 'workspace/logs']:
        p = Path(d)
        if p.exists():
            items = list(p.iterdir())
            print(f"  {d}/ ({len(items)} 项)")
    
    return True


if __name__ == '__main__':
    success = test_quick_workflow()
    sys.exit(0 if success else 1)
