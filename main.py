#!/usr/bin/env python3
"""
Azure AI LinkedIn Post Generator
Run in GitHub Actions to auto-generate posts every Friday
Or run locally with: python main.py
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path
import json

from src.news_fetcher import AzureNewsFetcher
from src.content_generator import ContentGenerator
from src.post_formatter import PostFormatter
from src.utils import logger, ConfigManager

def print_banner():
    """Print application banner"""
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║     🤖 Azure AI LinkedIn Content Generator          ║
    ║     Automates Azure AI news → LinkedIn post         ║
    ╚══════════════════════════════════════════════════════╝
    """
    print(banner)

def generate_post(model_name: str = None):
    """
    Generate a LinkedIn post from Azure AI news
    
    Args:
        model_name: Optional model name override
    
    Returns:
        Dict with post information
    """
    logger.info("=" * 60)
    logger.info("Starting post generation")
    logger.info(f"Environment: {'GitHub Actions' if ConfigManager.is_github_actions() else 'Local'}")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Step 1: Fetch news
    logger.info("\n📡 STEP 1: Fetching Azure AI News...")
    fetcher = AzureNewsFetcher()
    news_items = fetcher.fetch_news(days_back=7, max_items=10)
    
    if news_items:
        logger.info(f"✅ Found {len(news_items)} relevant articles")
        
        # Display top articles
        for i, item in enumerate(news_items[:3], 1):
            logger.info(f"  {i}. {item['title'][:80]}...")
    else:
        logger.warning("⚠️  No relevant news found. Using default content.")
    
    # Save news for reference
    news_file = Path('data/latest_news.json')
    with open(news_file, 'w') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'count': len(news_items),
            'articles': news_items
        }, f, indent=2)
    logger.info(f"📁 News saved to {news_file}")
    
    # Step 2: Generate content
    logger.info("\n🧠 STEP 2: Generating LinkedIn Post...")
    
    if model_name:
        logger.info(f"Using model: {model_name}")
    else:
        logger.info(f"Using model: {ConfigManager.get_env_var('MODEL_NAME', 'template')}")
    
    generator = ContentGenerator(model_name=model_name)
    post_result = generator.generate_post(news_items)
    
    post_content = post_result['content']
    logger.info(f"✅ Post generated ({len(post_content)} characters)")
    
    # Step 3: Format and save
    logger.info("\n📝 STEP 3: Formatting and Saving...")
    formatter = PostFormatter()
    formatted_post = formatter.format_for_linkedin(post_content)
    
    saved_post = formatter.save_post(
        formatted_post,
        metadata={
            'source': 'automated',
            'environment': 'github_actions' if ConfigManager.is_github_actions() else 'local',
            'model': post_result['metadata']['model_used'],
            'news_count': len(news_items),
            'news_hash': post_result['metadata']['content_hash']
        }
    )
    
    logger.info(f"✅ Post saved as ID #{saved_post['id']}")
    
    # Step 4: Display post
    print("\n" + "=" * 60)
    print("📄 YOUR LINKEDIN POST:")
    print("=" * 60)
    print(formatted_post)
    print("=" * 60)
    print(f"Characters: {len(formatted_post)}")
    print(f"Post ID: {saved_post['id']}")
    print("=" * 60)
    
    # Step 5: Instructions based on environment
    if ConfigManager.is_github_actions():
        print("\n" + "ℹ️"  * 30)
        print("📋 Running in GitHub Actions - Post NOT published automatically")
        print("💡 To publish this post, run locally:")
        print("   python publish.py")
        print("   or")
        print("   make publish")
        print("\n📥 Download artifact 'linkedin-post-*' to see the post")
        print("ℹ️"  * 30)
    else:
        print("\n💡 To publish this post to LinkedIn:")
        print("   python publish.py")
        print("   or")
        print("   make publish")
    
    return {
        'post_id': saved_post['id'],
        'content': formatted_post,
        'char_count': len(formatted_post),
        'news_count': len(news_items)
    }

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Generate Azure AI LinkedIn posts'
    )
    parser.add_argument(
        '--model',
        type=str,
        help='Override model name (e.g., "template" for template mode)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/ready_to_post.txt',
        help='Output file for generated post'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    try:
        result = generate_post(model_name=args.model)
        
        # Save to output file
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result['content'])
        
        logger.info(f"\n✅ Post written to {args.output}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())