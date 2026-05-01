#!/usr/bin/env python3
"""
LinkedIn Post Publisher - Publish generated posts to LinkedIn
Run this locally to post content to your LinkedIn profile

Usage:
    python publish.py                 # Publish latest post
    python publish.py --post-id 5     # Publish specific post
    python publish.py --dry-run       # Test without actually posting
    python publish.py --login-only    # Only authenticate and save session
"""

import sys
import argparse
from pathlib import Path

from src.post_formatter import PostFormatter
from src.linkedin_publisher import LinkedInPublisher
from src.utils import logger, ConfigManager

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║     📤 LinkedIn Post Publisher                      ║
    ║     Posts generated content to your profile         ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)

def authenticate():
    """Authenticate with LinkedIn and save session"""
    print("\n🔐 AUTHENTICATION MODE")
    print("This will login to LinkedIn and save your session for future use.\n")
    
    try:
        publisher = LinkedInPublisher()
        success = publisher.authenticate(headless=False)
        
        if success:
            print("\n✅ Authentication successful!")
            print(f"   Session saved to: data/linkedin_session.json")
            print("   You can now publish posts without re-entering credentials.")
        else:
            print("\n❌ Authentication failed!")
            print("   Check data/screenshots/ for diagnostic screenshots.")
        
        return success
    
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        print("   Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
        return False

def publish_post(post_id: int = None, dry_run: bool = False):
    """
    Publish a post to LinkedIn
    
    Args:
        post_id: Specific post ID to publish (None for latest)
        dry_run: If True, stop before actually posting
    """
    print("\n📤 PUBLISH MODE")
    
    # Get post
    formatter = PostFormatter()
    
    if post_id:
        post = formatter.get_post(post_id)
        if not post:
            print(f"\n❌ Post #{post_id} not found!")
            print(f"   Available posts: {len(formatter.history['posts'])}")
            return False
        print(f"📄 Using post #{post_id}")
    else:
        pending = formatter.get_pending_posts()
        if not pending:
            print("\n❌ No pending posts found!")
            print("   Run 'python main.py' first to generate a post.")
            return False
        
        post = pending[-1]  # Get latest pending post
        print(f"📄 Using latest pending post (#{post['id']})")
    
    # Confirm
    print(f"\n📝 Post preview (first 200 chars):")
    print("-" * 60)
    print(post['content'][:200] + "...")
    print("-" * 60)
    char_count = post.get('char_count') or post.get('character_count', len(post['content']))
    print(f"Total: {char_count} characters")
    
    if dry_run:
        print("\n🔍 DRY RUN - Will not actually post")
    
    if not dry_run:
        response = input("\n🤔 Publish this to LinkedIn? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Publishing cancelled.")
            return False
    
    # Publish
    try:
        publisher = LinkedInPublisher()
        result = publisher.post_content(post['content'], dry_run=dry_run)
        
        if result['success']:
            if dry_run:
                print("\n✅ Dry run successful! Post is ready to publish.")
            else:
                print(f"\n✅ Post published successfully!")
                formatter.mark_as_published(post['id'])
                
                if result.get('warning'):
                    print(f"   ⚠️  {result['warning']}")
        else:
            print(f"\n❌ Publishing failed: {result.get('error', 'Unknown error')}")
            print("   Check data/screenshots/ for diagnostic screenshots.")
        
        return result['success']
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False

def list_posts():
    """List all posts in history"""
    print("\n📚 POST HISTORY")
    
    formatter = PostFormatter()
    posts = formatter.history['posts']
    
    if not posts:
        print("No posts found. Run 'python main.py' to generate your first post.")
        return
    
    for post in posts:
        status_emoji = {
            'pending': '⏳',
            'published': '✅',
            'failed': '❌'
        }.get(post.get('status'), '❓')
        
        char_count = post.get('char_count') or post.get('character_count', len(post.get('content', '')))
        print(f"  {status_emoji} #{post['id']}: {char_count} chars | "
              f"{post.get('created_at', 'Unknown date')[:10]} | {post.get('status', 'unknown')}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Publish LinkedIn posts from Azure AI Agent'
    )
    parser.add_argument(
        '--post-id',
        type=int,
        help='Publish specific post by ID'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test without actually posting'
    )
    parser.add_argument(
        '--login-only',
        action='store_true',
        help='Only authenticate and save session'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all posts in history'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check if running in GitHub Actions
    if ConfigManager.is_github_actions():
        print("\n❌ This script should NOT run in GitHub Actions!")
        print("   LinkedIn posting only works from your local machine.")
        print("   Please run this on your computer.")
        return 1
    
    try:
        if args.list:
            list_posts()
        elif args.login_only:
            success = authenticate()
            return 0 if success else 1
        else:
            success = publish_post(post_id=args.post_id, dry_run=args.dry_run)
            return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())