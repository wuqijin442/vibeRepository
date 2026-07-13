#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class DataCollector:
    def __init__(self, config):
        self.config = config
        self.github_token = config.get('github', {}).get('token', '')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        if self.github_token:
            self.session.headers['Authorization'] = f'token {self.github_token}'

    def collect_all(self) -> List[Dict]:
        all_projects = []
        
        collectors = [
            self._collect_github_trending,
            self._collect_github_search,
            self._collect_huggingface,
            self._collect_hackernews,
            self._collect_reddit,
            self._collect_producthunt,
            self._collect_papers_with_code,
            self._collect_twitter,
        ]
        
        for collector in collectors:
            try:
                projects = collector()
                logger.info(f"从 {collector.__name__} 采集到 {len(projects)} 个项目")
                all_projects.extend(projects)
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                logger.error(f"采集 {collector.__name__} 失败: {e}")
        
        deduped = self._deduplicate(all_projects)
        logger.info(f"去重后共 {len(deduped)} 个项目")
        return deduped

    def _deduplicate(self, projects: List[Dict]) -> List[Dict]:
        seen = set()
        result = []
        for p in projects:
            key = p.get('url') or p.get('name', '')
            if key and key not in seen:
                seen.add(key)
                result.append(p)
        return result

    def _fetch_trending_page(self, since: str) -> List[Dict]:
        projects = []
        url = f"https://github.com/trending?since={since}"

        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')

            articles = soup.select('article.Box-row')
            for article in articles[:100]:
                try:
                    h2 = article.select_one('h2 a')
                    if not h2:
                        continue

                    repo_name = h2.get_text(strip=True).replace('\n', '').replace(' ', '')
                    repo_url = 'https://github.com' + h2.get('href', '')

                    desc_tag = article.select_one('p')
                    description = desc_tag.get_text(strip=True) if desc_tag else ''

                    stars_tag = article.select_one('a[href$="/stargazers"]')
                    stars = 0
                    if stars_tag:
                        stars_text = stars_tag.get_text(strip=True).replace(',', '')
                        try:
                            stars = int(stars_text)
                        except ValueError:
                            pass

                    period_stars = 0
                    period_stars_tag = article.select_one('span.d-inline-block.float-sm-right')
                    if period_stars_tag:
                        period_text = period_stars_tag.get_text(strip=True)
                        import re
                        match = re.search(r'([\d,]+)', period_text)
                        if match:
                            try:
                                period_stars = int(match.group(1).replace(',', ''))
                            except ValueError:
                                pass

                    lang_tag = article.select_one('[itemprop="programmingLanguage"]')
                    language = lang_tag.get_text(strip=True) if lang_tag else ''

                    projects.append({
                        'name': repo_name,
                        'url': repo_url,
                        'description': description,
                        'stars': stars,
                        'period_stars': period_stars,
                        'language': language,
                    })
                except Exception as e:
                    logger.debug(f"解析 trending({since}) 项目失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"GitHub Trending({since}) 采集失败: {e}")

        return projects

    def _collect_github_trending(self) -> List[Dict]:
        daily_projects = self._fetch_trending_page('daily')
        time.sleep(random.uniform(1, 2))
        weekly_projects = self._fetch_trending_page('weekly')
        time.sleep(random.uniform(1, 2))
        monthly_projects = self._fetch_trending_page('monthly')

        weekly_map = {p['name']: p['period_stars'] for p in weekly_projects}
        monthly_map = {p['name']: p['period_stars'] for p in monthly_projects}

        projects = []
        for p in daily_projects:
            repo_name = p['name']
            projects.append({
                'name': repo_name,
                'url': p['url'],
                'description': p['description'],
                'stars': p['stars'],
                'daily_stars': p['period_stars'],
                'weekly_stars': weekly_map.get(repo_name, 0),
                'monthly_stars': monthly_map.get(repo_name, 0),
                'language': p['language'],
                'source': 'github_trending',
                'collected_at': datetime.now().isoformat()
            })

        return projects

    def _collect_github_search(self) -> List[Dict]:
        projects = []
        keywords = [
            'AI agent', 'LLM agent', 'multi agent', 'coding agent',
            'MCP server', 'Claude Code', 'vibe coding', 'RAG',
            'local LLM', 'browser use', 'computer use', 'workflow automation',
            'OpenAI', 'Anthropic', 'DeepSeek', 'Gemini',
            'ComfyUI', 'Flux', 'Stable Diffusion',
            'Whisper', 'TTS', 'OCR', 'voice AI'
        ]
        
        for keyword in keywords[:10]:
            try:
                url = "https://api.github.com/search/repositories"
                params = {
                    'q': f'{keyword} stars:>100',
                    'sort': 'stars',
                    'order': 'desc',
                    'per_page': 30
                }
                
                resp = self.session.get(url, params=params, timeout=30)
                if resp.status_code == 403:
                    logger.warning("GitHub API rate limit reached")
                    break
                    
                data = resp.json()
                for item in data.get('items', [])[:20]:
                    created_at = item.get('created_at', '')
                    open_source_date = created_at[:10] if created_at else ''
                    projects.append({
                        'name': item.get('full_name', ''),
                        'url': item.get('html_url', ''),
                        'description': item.get('description', '') or '',
                        'stars': item.get('stargazers_count', 0),
                        'daily_stars': 0,
                        'language': item.get('language', '') or '',
                        'forks': item.get('forks_count', 0),
                        'author': item.get('owner', {}).get('login', ''),
                        'license': (item.get('license') or {}).get('name', ''),
                        'created_at': created_at,
                        'open_source_date': open_source_date,
                        'updated_at': item.get('updated_at', ''),
                        'source': 'github_search',
                        'collected_at': datetime.now().isoformat()
                    })
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"GitHub Search 关键词 '{keyword}' 失败: {e}")
                continue
        
        return projects

    def _collect_github_stargazers_timeline(self, owner: str, repo: str) -> dict:
        url = f"https://api.github.com/repos/{owner}/{repo}"

        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code == 403:
                logger.warning("GitHub API rate limit reached (stargazers timeline)")
                return {}
            resp.raise_for_status()

            data = resp.json()
            time.sleep(random.uniform(1, 2))

            return {
                'stargazers_count': data.get('stargazers_count', 0),
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', ''),
                'pushed_at': data.get('pushed_at', ''),
            }
        except Exception as e:
            logger.error(f"获取 stargazers timeline 失败 {owner}/{repo}: {e}")
            return {}

    def enrich_with_github_data(self, projects: List[Dict], top_n: int = 20) -> List[Dict]:
        api_rate_limited = False
        for project in projects[:top_n]:
            # 已有 open_source_date 则跳过
            if project.get('open_source_date') or project.get('created_at'):
                continue

            url = project.get('url', '')
            if 'github.com' not in url:
                continue

            try:
                parts = url.split('github.com/')[-1].split('/')
                if len(parts) < 2:
                    continue

                owner = parts[0]
                repo = parts[1].split('?')[0].split('#')[0].strip('/')
                if not owner or not repo:
                    continue

                # 优先使用 API（未被限速时）
                if not api_rate_limited:
                    api_url = f"https://api.github.com/repos/{owner}/{repo}"
                    resp = self.session.get(api_url, timeout=30)

                    if resp.status_code == 403:
                        logger.warning("GitHub API rate limit reached (enrich), 切换到网页抓取")
                        api_rate_limited = True
                    else:
                        resp.raise_for_status()
                        data = resp.json()
                        created_at = data.get('created_at', '')
                        if created_at:
                            project['created_at'] = created_at
                            project['open_source_date'] = created_at[:10]

                        project['forks'] = data.get('forks_count', project.get('forks', 0))

                        license_info = data.get('license')
                        license_name = (license_info or {}).get('name', '')
                        if license_name:
                            project['license'] = license_name

                        time.sleep(random.uniform(1, 2))
                        continue

                # API 限速时回退到网页抓取
                if api_rate_limited:
                    created_at = self._scrape_repo_created_at(owner, repo)
                    if created_at:
                        project['created_at'] = created_at
                        project['open_source_date'] = created_at[:10]
                        logger.info(f"网页抓取开源时间: {owner}/{repo} -> {created_at[:10]}")
                    time.sleep(random.uniform(0.5, 1))

            except Exception as e:
                logger.debug(f"enrich {project.get('name', '')} 失败: {e}")
                continue

        return projects

    def _scrape_repo_created_at(self, owner: str, repo: str) -> str:
        """通过抓取 GitHub 仓库页面 HTML 获取开源时间，绕过 API 速率限制"""
        url = f"https://github.com/{owner}/{repo}"
        try:
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                return ''

            html = resp.text

            # 方法1: 解析页面中的 embedded JSON (react-app.embeddedData)
            import re
            # 查找 createdAt 字段
            match = re.search(r'"createdAt"\s*:\s*"([^"]+)"', html)
            if match:
                return match.group(1)

            # 方法2: 查找 created_at 字段
            match = re.search(r'"created_at"\s*:\s*"([^"]+)"', html)
            if match:
                return match.group(1)

            # 方法3: 查找最早的 relative-time datetime 属性
            dates = re.findall(r'datetime="(\d{4}-\d{2}-\d{2})', html)
            if dates:
                return min(dates)

            return ''
        except Exception as e:
            logger.debug(f"网页抓取 {owner}/{repo} 失败: {e}")
            return ''

    def _collect_huggingface(self) -> List[Dict]:
        projects = []
        url = "https://huggingface.co/models?sort=trending"
        
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'lxml')
            
            cards = soup.select('article')
            for card in cards[:50]:
                try:
                    title_tag = card.select_one('h4 a, h3 a')
                    if not title_tag:
                        continue
                    
                    name = title_tag.get_text(strip=True)
                    href = title_tag.get('href', '')
                    url = 'https://huggingface.co' + href if href.startswith('/') else href
                    
                    desc_tag = card.select_one('p')
                    description = desc_tag.get_text(strip=True) if desc_tag else ''
                    
                    downloads = 0
                    dl_tag = card.find(string=lambda t: t and 'downloads' in t.lower())
                    if dl_tag:
                        import re
                        match = re.search(r'([\d,.kKmM]+)', dl_tag)
                        if match:
                            num_str = match.group(1).lower()
                            try:
                                if 'k' in num_str:
                                    downloads = int(float(num_str.replace('k', '')) * 1000)
                                elif 'm' in num_str:
                                    downloads = int(float(num_str.replace('m', '')) * 1000000)
                                else:
                                    downloads = int(num_str.replace(',', ''))
                            except ValueError:
                                pass
                    
                    projects.append({
                        'name': name,
                        'url': url,
                        'description': description,
                        'stars': downloads,
                        'daily_stars': 0,
                        'language': 'Python',
                        'source': 'huggingface',
                        'platform': 'huggingface',
                        'collected_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"HuggingFace 采集失败: {e}")
        
        return projects

    def _collect_hackernews(self) -> List[Dict]:
        projects = []
        
        try:
            url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            story_ids = resp.json()[:100]
            
            ai_keywords = ['ai', 'llm', 'gpt', 'agent', 'openai', 'anthropic', 
                          'claude', 'mcp', 'coding', 'github', 'model', 'ml',
                          'machine learning', 'deep learning']
            
            for story_id in story_ids:
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    resp = self.session.get(story_url, timeout=10)
                    item = resp.json()
                    
                    if not item or item.get('type') != 'story':
                        continue
                    
                    title = item.get('title', '').lower()
                    url = item.get('url', '')
                    
                    if not any(kw in title for kw in ai_keywords):
                        continue
                    
                    if 'github.com' in url:
                        projects.append({
                            'name': item.get('title', ''),
                            'url': url,
                            'description': item.get('title', ''),
                            'stars': item.get('score', 0),
                            'daily_stars': item.get('score', 0),
                            'language': '',
                            'source': 'hackernews',
                            'hn_score': item.get('score', 0),
                            'collected_at': datetime.now().isoformat()
                        })
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"HackerNews 采集失败: {e}")
        
        return projects

    def _collect_reddit(self) -> List[Dict]:
        projects = []
        subreddits = self.config.get('reddit', {}).get('subreddits', [])
        
        for subreddit in subreddits[:3]:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                headers = {'User-Agent': 'AIProjectResearcher/1.0'}
                resp = self.session.get(url, headers=headers, timeout=30)
                
                if resp.status_code != 200:
                    continue
                
                data = resp.json()
                posts = data.get('data', {}).get('children', [])
                
                for post in posts[:20]:
                    pdata = post.get('data', {})
                    url = pdata.get('url', '')
                    
                    if 'github.com' in url:
                        projects.append({
                            'name': pdata.get('title', ''),
                            'url': url,
                            'description': pdata.get('selftext', '')[:200],
                            'stars': pdata.get('score', 0),
                            'daily_stars': pdata.get('score', 0),
                            'language': '',
                            'source': f'reddit/r/{subreddit}',
                            'reddit_score': pdata.get('score', 0),
                            'collected_at': datetime.now().isoformat()
                        })
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"Reddit r/{subreddit} 采集失败: {e}")
                continue
        
        return projects

    def _collect_producthunt(self) -> List[Dict]:
        projects = []
        url = "https://www.producthunt.com"
        
        try:
            resp = self.session.get(f"{url}/topics/ai", timeout=30)
            if resp.status_code != 200:
                logger.warning(f"Product Hunt 请求失败: {resp.status_code}")
                return projects
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            cards = soup.select('[data-test^="post-item"]')
            for card in cards[:30]:
                try:
                    name_tag = card.select_one('[data-test^="post-name"]')
                    if not name_tag:
                        continue
                    
                    name = name_tag.get_text(strip=True)
                    
                    desc_tag = card.select_one('[data-test^="post-tagline"]')
                    description = desc_tag.get_text(strip=True) if desc_tag else ''
                    
                    vote_tag = card.select_one('[data-test^="vote-count"]')
                    votes = 0
                    if vote_tag:
                        vote_text = vote_tag.get_text(strip=True).replace(',', '')
                        try:
                            votes = int(vote_text)
                        except ValueError:
                            pass
                    
                    link_tag = card.select_one('a[href^="/posts/"]')
                    post_url = url + link_tag['href'] if link_tag and link_tag.get('href') else ''
                    
                    projects.append({
                        'name': name,
                        'url': post_url,
                        'description': description,
                        'stars': votes,
                        'daily_stars': votes,
                        'language': '',
                        'source': 'producthunt',
                        'ph_votes': votes,
                        'collected_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Product Hunt 采集失败: {e}")
        
        logger.info(f"Product Hunt 采集到 {len(projects)} 个项目")
        return projects

    def _collect_papers_with_code(self) -> List[Dict]:
        projects = []
        base_url = "https://paperswithcode.com"
        
        try:
            url = f"{base_url}/latest"
            resp = self.session.get(url, timeout=30)
            if resp.status_code != 200:
                logger.warning(f"Papers With Code 请求失败: {resp.status_code}")
                return projects
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            cards = soup.select('.paper-card, .row.infinite-item')
            for card in cards[:30]:
                try:
                    title_tag = card.select_one('h1 a, h2 a, .paper-title a')
                    if not title_tag:
                        continue
                    
                    name = title_tag.get_text(strip=True)
                    href = title_tag.get('href', '')
                    paper_url = base_url + href if href.startswith('/') else href
                    
                    desc_tag = card.select_one('.paper-abstract p, .entity-strip')
                    description = desc_tag.get_text(strip=True)[:200] if desc_tag else ''
                    
                    stars_tag = card.select_one('.stars-count, .badge-secondary')
                    stars = 0
                    if stars_tag:
                        stars_text = stars_tag.get_text(strip=True).replace(',', '')
                        try:
                            stars = int(stars_text)
                        except ValueError:
                            pass
                    
                    github_link = card.select_one('a[href*="github.com"]')
                    github_url = github_link['href'] if github_link else ''
                    
                    projects.append({
                        'name': name,
                        'url': github_url if github_url else paper_url,
                        'description': description,
                        'stars': stars,
                        'daily_stars': 0,
                        'language': 'Python',
                        'source': 'papers_with_code',
                        'paper_url': paper_url,
                        'collected_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Papers With Code 采集失败: {e}")
        
        logger.info(f"Papers With Code 采集到 {len(projects)} 个项目")
        return projects

    def _collect_twitter(self) -> List[Dict]:
        projects = []
        
        twitter_accounts = [
            'OpenAI', 'AnthropicAI', 'GoogleDeepMind', 'cursor_ai',
            'ClaudeAI', 'codex', 'ModelContextP', 'vibe_coding'
        ]
        
        try:
            for account in twitter_accounts[:5]:
                try:
                    url = f"https://twitter.com/{account}"
                    resp = self.session.get(url, timeout=15)
                    
                    if resp.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(resp.text, 'lxml')
                    
                    links = soup.select('a[href*="github.com"]')
                    for link in links[:5]:
                        href = link.get('href', '')
                        if 'github.com' in href and href.count('/') >= 3:
                            try:
                                parts = href.split('github.com/')[-1].split('/')
                                if len(parts) >= 2:
                                    repo_name = f"{parts[0]}/{parts[1].split('?')[0].split('#')[0]}"
                                    
                                    projects.append({
                                        'name': repo_name,
                                        'url': f"https://github.com/{repo_name}",
                                        'description': f"Mentioned by @{account} on X(Twitter)",
                                        'stars': 0,
                                        'daily_stars': 0,
                                        'language': '',
                                        'source': 'twitter',
                                        'twitter_account': account,
                                        'collected_at': datetime.now().isoformat()
                                    })
                            except Exception:
                                continue
                    
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.debug(f"Twitter 账号 {account} 采集失败: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Twitter 采集失败: {e}")
        
        logger.info(f"Twitter/X 采集到 {len(projects)} 个项目引用")
        return projects
