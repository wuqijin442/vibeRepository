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

    def _collect_github_trending(self) -> List[Dict]:
        projects = []
        url = "https://github.com/trending?since=daily"
        
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
                    
                    daily_stars_tag = article.select_one('span.d-inline-block.float-sm-right')
                    daily_stars = 0
                    if daily_stars_tag:
                        daily_text = daily_stars_tag.get_text(strip=True)
                        import re
                        match = re.search(r'([\d,]+)', daily_text)
                        if match:
                            try:
                                daily_stars = int(match.group(1).replace(',', ''))
                            except ValueError:
                                pass
                    
                    lang_tag = article.select_one('[itemprop="programmingLanguage"]')
                    language = lang_tag.get_text(strip=True) if lang_tag else ''
                    
                    projects.append({
                        'name': repo_name,
                        'url': repo_url,
                        'description': description,
                        'stars': stars,
                        'daily_stars': daily_stars,
                        'language': language,
                        'source': 'github_trending',
                        'collected_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.debug(f"解析 trending 项目失败: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"GitHub Trending 采集失败: {e}")
        
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
                        'created_at': item.get('created_at', ''),
                        'updated_at': item.get('updated_at', ''),
                        'source': 'github_search',
                        'collected_at': datetime.now().isoformat()
                    })
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"GitHub Search 关键词 '{keyword}' 失败: {e}")
                continue
        
        return projects

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
        logger.info("Product Hunt 采集需要 API key，暂跳过")
        return projects

    def _collect_papers_with_code(self) -> List[Dict]:
        projects = []
        logger.info("Papers With Code 采集暂跳过")
        return projects
