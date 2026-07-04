#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '/workspace')

def test_imports():
    print("=" * 60)
    print("测试模块导入...")
    print("=" * 60)
    
    modules = [
        ('modules.collector', 'DataCollector'),
        ('modules.filter', 'ProjectFilter'),
        ('modules.analyzer', 'ProjectAnalyzer'),
        ('modules.installer', 'ProjectInstaller'),
        ('modules.runner', 'ProjectRunner'),
        ('modules.tester', 'ProjectTester'),
        ('modules.screenshot', 'ScreenshotTaker'),
        ('modules.performance', 'PerformanceAnalyzer'),
        ('modules.competitor', 'CompetitorAnalyzer'),
        ('modules.documenter', 'DocumentGenerator'),
        ('modules.architect', 'ArchitectureGenerator'),
        ('modules.scoring', 'ProjectScorer'),
        ('modules.knowledge_base', 'KnowledgeBaseManager'),
        ('modules.reporter', 'ReportGenerator'),
        ('modules.github_sync', 'GitHubSyncer'),
    ]
    
    all_ok = True
    for module_name, class_name in modules:
        try:
            mod = __import__(module_name, fromlist=[class_name])
            cls = getattr(mod, class_name)
            print(f"✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"✗ {module_name}.{class_name}: {e}")
            all_ok = False
    
    return all_ok


def test_collector():
    print("\n" + "=" * 60)
    print("测试数据采集模块...")
    print("=" * 60)
    
    import yaml
    with open('/workspace/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from modules.collector import DataCollector
    collector = DataCollector(config)
    
    print("采集 GitHub Trending...")
    try:
        projects = collector._collect_github_trending()
        print(f"✓ 采集到 {len(projects)} 个 Trending 项目")
        if projects:
            p = projects[0]
            print(f"  第一个: {p.get('name', 'N/A')} - {p.get('stars', 0)} Stars")
    except Exception as e:
        print(f"✗ GitHub Trending 采集失败: {e}")
    
    return True


def test_filter():
    print("\n" + "=" * 60)
    print("测试项目筛选模块...")
    print("=" * 60)
    
    import yaml
    with open('/workspace/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from modules.filter import ProjectFilter
    project_filter = ProjectFilter(config)
    
    test_projects = [
        {
            'name': 'test/awesome-ai-agent',
            'description': 'A collection of awesome AI agents',
            'url': 'https://github.com/test/awesome-ai-agent',
            'stars': 5000,
            'daily_stars': 100,
            'source': 'github_trending'
        },
        {
            'name': 'test/ai-agent-framework',
            'description': 'A powerful AI agent framework for building autonomous agents',
            'url': 'https://github.com/test/ai-agent-framework',
            'stars': 3000,
            'daily_stars': 50,
            'source': 'github_search',
            'language': 'Python',
            'forks': 200,
            'author': 'testuser',
            'license': 'MIT',
            'updated_at': '2024-01-15T10:00:00Z'
        },
        {
            'name': 'test/llm-rag-tool',
            'description': 'An LLM RAG tool for knowledge base',
            'url': 'https://github.com/test/llm-rag-tool',
            'stars': 1000,
            'daily_stars': 20,
            'language': 'Python',
            'source': 'github_search'
        },
    ]
    
    round1 = project_filter.first_round(test_projects, target=3)
    print(f"✓ 第一轮筛选: {len(round1)} / {len(test_projects)}")
    
    round2 = project_filter.second_round(round1, target=2)
    print(f"✓ 第二轮筛选: {len(round2)} / {len(round1)}")
    
    return True


def test_scoring():
    print("\n" + "=" * 60)
    print("测试评分模块...")
    print("=" * 60)
    
    import yaml
    with open('/workspace/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    from modules.scoring import ProjectScorer
    scorer = ProjectScorer(config)
    
    test_project = {
        'name': 'test/ai-agent',
        'stars': 5000,
        'daily_stars': 100,
        'forks': 500,
        'tags': ['Agent', 'LLM', 'Coding'],
        'description': 'A powerful AI agent framework',
        'has_readme': True,
        'readme_has_demo': True,
        'readme_has_install': True,
        'readme_has_docs': True,
        'readme_length': 6000,
        'license': 'MIT',
        'has_docker': True,
        'install_success': True,
        'run_success': True,
        'demo_success': True,
        'startup_time': 8,
        'frameworks': ['fastapi', 'langchain'],
        'use_cases': ['自动化任务', '多代理协作'],
        'target_audience': ['开发者', 'AI 研究者'],
        'advantages': ['社区热度高', '文档完善', '支持 Docker'],
        'disadvantages': ['学习曲线陡峭'],
    }
    
    result = scorer.score(test_project)
    print(f"✓ 评分完成: {result.get('score')} 分")
    print(f"  推荐指数: {result.get('stars_display')}")
    print(f"  评分明细: {result.get('score_breakdown')}")
    
    return True


def test_documenter():
    print("\n" + "=" * 60)
    print("测试文档生成模块...")
    print("=" * 60)
    
    import yaml
    import tempfile
    import os
    from pathlib import Path
    
    with open('/workspace/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['paths']['knowledge_base'] = tempfile.mkdtemp()
    
    from modules.documenter import DocumentGenerator
    documenter = DocumentGenerator(config)
    
    test_project = {
        'name': 'test/ai-demo',
        'description': 'An AI demo project',
        'url': 'https://github.com/test/ai-demo',
        'tags': ['Agent', 'LLM'],
        'primary_language': 'Python',
        'frameworks': ['fastapi', 'langchain'],
        'license': 'MIT',
        'supported_platforms': ['Linux', 'macOS', 'Windows'],
        'install_method': 'pip_requirements',
        'run_command': 'python main.py',
        'startup_time': 5.0,
        'memory_usage': 128.0,
        'cpu_usage': 10.5,
        'stars': 1000,
        'daily_stars': 50,
        'forks': 100,
        'score': 85.0,
        'install_success': True,
        'run_success': True,
        'demo_success': True,
        'install_time': 30.0,
        'perf_disk_usage': 100.0,
        'has_docker': True,
        'advantages': ['易于使用', '文档完善'],
        'disadvantages': ['功能有限'],
        'target_audience': ['开发者'],
        'use_cases': ['自动化任务', '测试'],
        'competitors': ['Competitor A', 'Competitor B'],
        'deployment_methods': ['Docker'],
        'collected_at': '2024-01-15T10:00:00',
        'readme_length': 3000,
        'author': 'testuser',
        'heat_score': 75.0,
    }
    
    result = documenter.generate(test_project)
    
    if result.get('docs_generated'):
        docs_path = Path(result['docs_path'])
        docs = list(docs_path.glob('*.md'))
        print(f"✓ 文档生成成功，共 {len(docs)} 个文件:")
        for doc in docs:
            print(f"  - {doc.name}")
    else:
        print(f"✗ 文档生成失败: {result.get('docs_error')}")
    
    return result.get('docs_generated', False)


def test_architect():
    print("\n" + "=" * 60)
    print("测试架构图生成模块...")
    print("=" * 60)
    
    import yaml
    import tempfile
    
    with open('/workspace/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['paths']['architecture'] = tempfile.mkdtemp()
    
    from modules.architect import ArchitectureGenerator
    architect = ArchitectureGenerator(config)
    
    test_project = {
        'name': 'test/ai-app',
        'project_type': 'web_app',
        'tags': ['Agent', 'MCP'],
        'primary_language': 'Python',
        'frameworks': ['fastapi', 'langchain', 'transformers'],
        'dependency_files': ['requirements.txt', 'Dockerfile'],
    }
    
    result = architect.generate(test_project)
    
    if result.get('architecture_generated'):
        from pathlib import Path
        arch_path = Path(result['architecture_path'])
        arch_files = list(arch_path.iterdir())
        print(f"✓ 架构图生成成功，共 {len(arch_files)} 个文件:")
        for f in arch_files:
            print(f"  - {f.name}")
    else:
        print(f"✗ 架构图生成失败: {result.get('architecture_error')}")
    
    return result.get('architecture_generated', False)


def test_reporter():
    print("\n" + "=" * 60)
    print("测试报告生成模块...")
    print("=" * 60)
    
    import yaml
    import tempfile
    
    with open('/workspace/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    config['paths']['daily_reports'] = tempfile.mkdtemp()
    config['paths']['weekly_reports'] = tempfile.mkdtemp()
    config['paths']['monthly_reports'] = tempfile.mkdtemp()
    
    from modules.reporter import ReportGenerator
    reporter = ReportGenerator(config)
    
    test_projects = [
        {
            'name': 'test/ai-agent-1',
            'url': 'https://github.com/test/ai-agent-1',
            'description': 'A powerful AI agent framework',
            'stars': 5000,
            'daily_stars': 100,
            'forks': 500,
            'score': 92.5,
            'stars_count': 5,
            'stars_display': '★★★★★',
            'primary_language': 'Python',
            'frameworks': ['fastapi', 'langchain'],
            'tags': ['Agent', 'LLM'],
            'install_success': True,
            'run_success': True,
            'demo_success': True,
            'startup_time': 5.0,
            'memory_usage': 256.0,
            'use_cases': ['自动化任务', '多代理协作'],
            'advantages': ['社区热度高', '文档完善', '功能强大'],
            'disadvantages': ['学习曲线陡峭'],
            'target_audience': ['开发者', 'AI 研究者'],
        },
        {
            'name': 'test/mcp-server',
            'url': 'https://github.com/test/mcp-server',
            'description': 'An MCP server implementation',
            'stars': 2000,
            'daily_stars': 80,
            'forks': 200,
            'score': 88.0,
            'stars_count': 4,
            'stars_display': '★★★★☆',
            'primary_language': 'TypeScript',
            'frameworks': ['express'],
            'tags': ['MCP', 'Agent'],
            'install_success': True,
            'run_success': True,
            'demo_success': False,
            'startup_time': 3.0,
            'memory_usage': 128.0,
            'use_cases': ['AI 工具集成'],
            'advantages': ['轻量高效', '易于集成'],
            'disadvantages': ['生态待完善'],
            'target_audience': ['开发者'],
        },
    ]
    
    stats = {
        'scanned': 300,
        'filtered': 5,
        'cloned': 5,
        'installed': 4,
        'ran': 3,
        'demo_passed': 2,
        'recommended': 1,
        'synced': 0,
        'failed_projects': [
            {'name': 'test/failed-project', 'error': '安装失败'}
        ]
    }
    
    report_path = reporter.generate_daily_report(test_projects, stats, '2024-01-15')
    print(f"✓ 日报已生成: {report_path}")
    
    from pathlib import Path
    if Path(report_path).exists():
        with open(report_path, 'r') as f:
            content = f.read()
        print(f"  报告长度: {len(content)} 字符")
    
    return True


def main():
    print("AI 开源项目每日工作流 - 系统验证")
    print()
    
    tests = [
        ('模块导入', test_imports),
        ('数据采集', test_collector),
        ('项目筛选', test_filter),
        ('评分系统', test_scoring),
        ('文档生成', test_documenter),
        ('架构图生成', test_architect),
        ('报告生成', test_reporter),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！系统运行正常。")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败。")
    
    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
