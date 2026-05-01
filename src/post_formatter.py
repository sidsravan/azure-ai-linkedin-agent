import json
from datetime import datetime
from pathlib import Path
from typing import Dict

class PostFormatter:
    """Formats and stores LinkedIn posts"""
    
    def __init__(self):
        self.history_file = Path('data/post_history.json')
        self.history_file.parent.mkdir(exist_ok=True)
        self.load_history()
    
    def load_history(self):
        """Load post history"""
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                content = f.read().strip()
                self.history = json.loads(content) if content else {'posts': [], 'total_posts': 0}
        else:
            self.history = {'posts': [], 'total_posts': 0}
    
    def save_post(self, content: str, metadata: Dict = None) -> Dict:
        """Save post to history"""
        post = {
            'id': self.history['total_posts'] + 1,
            'content': content,
            'posted_at': datetime.now().isoformat(),
            'character_count': len(content),
            'metadata': metadata or {}
        }
        
        self.history['posts'].append(post)
        self.history['total_posts'] += 1
        
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
        
        return post
    
    def get_last_post(self) -> Dict:
        """Get most recent post"""
        if self.history['posts']:
            return self.history['posts'][-1]
        return None
    
    def format_for_linkedin(self, content: str) -> str:
        """Format content with proper LinkedIn formatting"""
        # Ensure content isn't too long
        if len(content) > 3000:
            content = content[:2997] + "..."
        
        # Clean up any formatting issues
        content = content.replace('\r\n', '\n')
        content = content.replace('\r', '\n')
        
        return content