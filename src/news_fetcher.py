import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureNewsFetcher:
    """Fetches latest Azure and Microsoft AI news from RSS feeds"""
    
    def __init__(self):
        self.feeds = [
            # Azure Official Blog
            "https://azure.microsoft.com/en-us/blog/feed/",
            # Microsoft AI Blog
            "https://blogs.microsoft.com/ai/feed/",
            # Azure Updates
            "https://azure.microsoft.com/en-us/updates/feed/"
        ]
        
        self.relevance_keywords = [
            'azure', 'microsoft', 'cloud', 'ai', 'artificial intelligence',
            'machine learning', 'cognitive services', 'openai', 'copilot',
            'azure ai', 'azure openai', 'cognitive', 'ml', 'generative ai'
        ]
    
    def fetch_news(self, days_back: int = 7) -> List[Dict]:
        """Fetch and filter relevant Azure AI news"""
        all_entries = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for feed_url in self.feeds:
            try:
                feed = feedparser.parse(feed_url)
                logger.info(f"Fetched {len(feed.entries)} entries from {feed_url}")
                
                for entry in feed.entries:
                    # Check if entry is recent
                    entry_date = datetime(*entry.published_parsed[:6])
                    if entry_date < cutoff_date:
                        continue
                    
                    # Check relevance
                    if self._is_relevant(entry):
                        all_entries.append({
                            'title': entry.title,
                            'link': entry.link,
                            'summary': self._clean_summary(entry.summary),
                            'published': entry_date.isoformat(),
                            'source': feed_url
                        })
                        
            except Exception as e:
                logger.error(f"Error fetching {feed_url}: {e}")
                continue
        
        # Sort by date
        all_entries.sort(key=lambda x: x['published'], reverse=True)
        logger.info(f"Found {len(all_entries)} relevant entries")
        return all_entries[:10]  # Return top 10 most recent
    
    def _is_relevant(self, entry) -> bool:
        """Check if entry is relevant to Azure AI"""
        text = f"{entry.title} {entry.summary}".lower()
        return any(keyword in text for keyword in self.relevance_keywords)
    
    def _clean_summary(self, summary: str) -> str:
        """Clean HTML from summary"""
        import re
        clean = re.sub('<[^<]+?>', '', summary)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean[:500]  # Limit summary length
    
    def save_news(self, news: List[Dict], filename: str = 'latest_news.json'):
        """Save fetched news to JSON"""
        with open(f'data/{filename}', 'w') as f:
            json.dump({
                'fetched_at': datetime.now().isoformat(),
                'count': len(news),
                'entries': news
            }, f, indent=2)