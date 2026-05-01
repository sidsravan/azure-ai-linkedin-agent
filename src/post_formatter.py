"""Post Formatter - Manages post formatting, history, and storage"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import re
from .utils import logger

class PostFormatter:
    """Format and manage LinkedIn posts"""
    
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.history_file = self.storage_dir / "post_history.json"
        self.ready_file = self.storage_dir / "ready_to_post.txt"
        self._load_history()
    
    def _load_history(self):
        """Load post history from file"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
            
            # Normalize old posts to use 'char_count' instead of 'character_count'
            for post in self.history.get('posts', []):
                if 'character_count' in post and 'char_count' not in post:
                    post['char_count'] = post.pop('character_count')
            
            logger.info(f"Loaded {len(self.history.get('posts', []))} historical posts")
        else:
            self.history = {
                'posts': [],
                'total_posts': 0,
                'last_updated': None
            }
            self._save_history()
    
    def _save_history(self):
        """Save post history to file"""
        self.history['last_updated'] = datetime.now().isoformat()
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def save_post(self, content: str, metadata: Dict = None) -> Dict:
        """
        Save a post to history
        
        Args:
            content: Post content
            metadata: Additional metadata
        
        Returns:
            Saved post record
        """
        post = {
            'id': self.history['total_posts'] + 1,
            'content': content,
            'char_count': len(content),
            'created_at': datetime.now().isoformat(),
            'metadata': metadata or {},
            'status': 'pending'
        }
        
        self.history['posts'].append(post)
        self.history['total_posts'] += 1
        self._save_history()
        
        # Also save as ready-to-post file
        self._save_ready_file(content)
        
        logger.info(f"Post #{post['id']} saved ({len(content)} chars)")
        return post
    
    def _save_ready_file(self, content: str):
        """Save post as ready-to-post text file"""
        with open(self.ready_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Post saved to {self.ready_file}")
    
    def get_post(self, post_id: int) -> Optional[Dict]:
        """Get a specific post by ID"""
        for post in self.history['posts']:
            if post['id'] == post_id:
                return post
        return None
    
    def get_latest_post(self) -> Optional[Dict]:
        """Get the most recent post"""
        if self.history['posts']:
            return self.history['posts'][-1]
        return None
    
    def get_pending_posts(self) -> List[Dict]:
        """Get all pending (unpublished) posts"""
        return [p for p in self.history['posts'] if p.get('status') == 'pending']
    
    def mark_as_published(self, post_id: int):
        """Mark a post as published"""
        for post in self.history['posts']:
            if post['id'] == post_id:
                post['status'] = 'published'
                post['published_at'] = datetime.now().isoformat()
                self._save_history()
                logger.info(f"Post #{post_id} marked as published")
                return True
        return False
    
    def format_for_linkedin(self, content: str, max_length: int = 1300) -> str:
        """
        Format content for optimal LinkedIn display
        
        Args:
            content: Raw post content
            max_length: Maximum character length
        
        Returns:
            Formatted post
        """
        # Replace escaped newlines with actual newlines
        content = content.replace('\\n', '\n')
        
        # Ensure consistent line spacing
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Add zero-width spaces to hashtags for better visibility
        # (This is optional and can be removed if undesired)
        # content = re.sub(r'(#\w+)', r'\1\u200B', content)  # Uncomment if needed
        
        # Truncate if too long (ending at complete word/sentence)
        if len(content) > max_length:
            # Find last complete sentence within limit
            truncated = content[:max_length]
            last_period = truncated.rfind('.')
            last_newline = truncated.rfind('\n')
            cut_point = max(last_period, last_newline)
            
            if cut_point > max_length * 0.8:  # Only cut if within reasonable range
                content = content[:cut_point + 1]
            else:
                content = truncated.rsplit(' ', 1)[0]
            
            content += "\n\n... [continued in comments]"
        
        return content.strip()
    
    def get_statistics(self) -> Dict:
        """Get statistics about posts"""
        posts = self.history['posts']
        if not posts:
            return {'total': 0}
        
        published = [p for p in posts if p.get('status') == 'published']
        
        return {
            'total': len(posts),
            'published': len(published),
            'pending': len(posts) - len(published),
            'avg_length': sum(p.get('char_count') or p.get('character_count', 0) for p in posts) / len(posts),
            'first_post': posts[0]['created_at'],
            'last_post': posts[-1]['created_at']
        }