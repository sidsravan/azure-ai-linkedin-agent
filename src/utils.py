"""Common utilities for the Azure AI LinkedIn Agent"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
def setup_logging(name: str = "AzureAI-Agent"):
    """Configure logging with both file and console handlers"""
    import sys
    
    log_dir = Path("data")
    log_dir.mkdir(exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # File handler
    fh = logging.FileHandler(log_dir / f"agent_{datetime.now():%Y%m%d}.log", encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # Fix Unicode encoding on Windows
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

logger = setup_logging()

class PostManager:
    """Manage post storage and retrieval"""
    
    def __init__(self, storage_file: str = "data/posts.json"):
        self.storage_file = Path(storage_file)
        self.storage_file.parent.mkdir(exist_ok=True)
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Initialize storage file if not exists"""
        if not self.storage_file.exists():
            self.save_posts([])
    
    def load_posts(self) -> list:
        """Load all posts from storage"""
        with open(self.storage_file, 'r') as f:
            return json.load(f)
    
    def save_posts(self, posts: list):
        """Save posts to storage"""
        with open(self.storage_file, 'w') as f:
            json.dump(posts, f, indent=2)
    
    def add_post(self, post_data: Dict) -> Dict:
        """Add a new post to storage"""
        posts = self.load_posts()
        post_data['id'] = len(posts) + 1
        post_data['created_at'] = datetime.now().isoformat()
        post_data['status'] = 'pending'  # pending, published, failed
        posts.append(post_data)
        self.save_posts(posts)
        logger.info(f"Post #{post_data['id']} saved to storage")
        return post_data
    
    def get_pending_posts(self) -> list:
        """Get all unpublished posts"""
        posts = self.load_posts()
        return [p for p in posts if p.get('status') == 'pending']
    
    def get_latest_post(self) -> Optional[Dict]:
        """Get the most recent post"""
        posts = self.load_posts()
        return posts[-1] if posts else None
    
    def mark_as_published(self, post_id: int):
        """Mark a post as published"""
        posts = self.load_posts()
        for post in posts:
            if post['id'] == post_id:
                post['status'] = 'published'
                post['published_at'] = datetime.now().isoformat()
                break
        self.save_posts(posts)
        logger.info(f"Post #{post_id} marked as published")

class ConfigManager:
    """Manage configuration"""
    
    @staticmethod
    def is_github_actions() -> bool:
        """Check if running in GitHub Actions"""
        return os.getenv('GITHUB_ACTIONS', 'false').lower() == 'true'
    
    @staticmethod
    def get_env_var(key: str, default: str = None) -> str:
        """Get environment variable with default"""
        return os.getenv(key, default)