"""Azure AI News Fetcher - Collects latest news from multiple sources"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from .utils import logger

@dataclass
class NewsItem:
    """Represents a single news item"""
    title: str
    link: str
    summary: str
    published: str
    source: str
    category: str = "General"

class AzureNewsFetcher:
    """Fetches and filters Azure AI related news"""
    
    def __init__(self):
        self.feeds = {
            'Azure Blog': 'https://azure.microsoft.com/en-us/blog/feed/',
            'Microsoft AI': 'https://blogs.microsoft.com/ai/feed/',
            'Azure Updates': 'https://azure.microsoft.com/en-us/updates/feed/'
        }
        
        # Keywords for relevance scoring
        self.high_priority = [
            'azure openai', 'copilot', 'gpt-4', 'generative ai',
            'azure ai studio', 'cognitive services', 'machine learning'
        ]
        self.medium_priority = [
            'azure', 'microsoft', 'cloud', 'ai', 'artificial intelligence',
            'ml', 'deep learning', 'neural network'
        ]
    
    def fetch_news(self, days_back: int = 7, max_items: int = 10) -> List[Dict]:
        """
        Fetch and score Azure AI news from configured feeds
        
        Args:
            days_back: How many days back to fetch news
            max_items: Maximum number of items to return
        
        Returns:
            List of news items sorted by relevance and date
        """
        all_news = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        logger.info(f"Fetching news from {len(self.feeds)} sources...")
        
        for source_name, feed_url in self.feeds.items():
            try:
                logger.debug(f"Fetching from {source_name}...")
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    logger.warning(f"Feed parsing warning for {source_name}: {feed.bozo_exception}")
                    continue
                
                for entry in feed.entries:
                    # Parse publication date
                    published_date = self._parse_date(entry)
                    
                    # Skip old entries
                    if published_date and published_date < cutoff_date:
                        continue
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance(entry)
                    
                    if relevance_score > 0:
                        all_news.append({
                            'title': self._clean_text(entry.title),
                            'link': entry.link,
                            'summary': self._clean_summary(entry.get('summary', '')),
                            'published': published_date.isoformat() if published_date else datetime.now().isoformat(),
                            'source': source_name,
                            'relevance': relevance_score
                        })
                        
            except Exception as e:
                logger.error(f"Error fetching from {source_name}: {e}")
                continue
        
        # Sort by relevance (descending) and then date (descending)
        all_news.sort(key=lambda x: (x['relevance'], x['published']), reverse=True)
        
        logger.info(f"Found {len(all_news)} relevant articles, returning top {min(max_items, len(all_news))}")
        
        return all_news[:max_items]
    
    def _parse_date(self, entry) -> Optional[datetime]:
        """Parse publication date from feed entry"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6])
        except:
            pass
        return None
    
    def _calculate_relevance(self, entry) -> int:
        """
        Calculate relevance score based on keyword matching
        
        Returns:
            0: Not relevant
            1-5: Low relevance
            6-10: Medium relevance
            11-15: High relevance
        """
        text = f"{entry.title} {entry.get('summary', '')}".lower()
        score = 0
        
        # High priority keywords
        for keyword in self.high_priority:
            if keyword in text:
                score += 5
        
        # Medium priority keywords
        for keyword in self.medium_priority:
            score += text.count(keyword)
        
        return min(score, 15)  # Cap at 15
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        import re
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', text)
        # Remove extra whitespace
        text = re.sub('\s+', ' ', text)
        return text.strip()
    
    def _clean_summary(self, summary: str, max_length: int = 300) -> str:
        """Clean and truncate summary for consistent length"""
        import re
        # Remove HTML tags
        summary = re.sub('<[^<]+?>', '', summary)
        # Remove extra whitespace
        summary = re.sub('\s+', ' ', summary)
        # Remove CDATA and other XML artifacts
        summary = re.sub('<!\[CDATA\[|\]\]>', '', summary)
        
        summary = summary.strip()
        
        # Truncate to max length, ending at a complete word
        if len(summary) > max_length:
            summary = summary[:max_length].rsplit(' ', 1)[0] + '...'
        
        return summary
    
    def format_news_for_prompt(self, news: List[Dict], max_items: int = 3) -> str:
        """
        Format news items into a string for LLM prompts
        
        Args:
            news: List of news items
            max_items: Maximum items to include
        
        Returns:
            Formatted string of news summaries
        """
        summary = "Recent Microsoft Azure and AI Updates:\n\n"
        
        for i, item in enumerate(news[:max_items], 1):
            summary += f"{i}. **{item['title']}**\n"
            summary += f"   Source: {item['source']}\n"
            summary += f"   Summary: {item['summary'][:200]}...\n"
            summary += f"   Read more: {item['link']}\n\n"
        
        return summary