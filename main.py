#!/usr/bin/env python3
"""
Azure AI LinkedIn Agent - Main Automation Script
Runs every Friday to generate and post Azure AI content
"""

import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from src.news_fetcher import AzureNewsFetcher
from src.content_generator import ContentGenerator
from src.post_formatter import PostFormatter
from src.linkedin_publisher import LinkedInPublisher

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Main automation workflow"""
    logger.info("=" * 50)
    logger.info("Starting Azure AI LinkedIn Agent")
    logger.info(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)
    
    try:
        # Step 1: Fetch latest Azure AI news
        logger.info("📡 Fetching latest Azure AI news...")
        fetcher = AzureNewsFetcher()
        news = fetcher.fetch_news(days_back=7)
        
        if news:
            logger.info(f"✅ Found {len(news)} relevant articles")
            fetcher.save_news(news)
        else:
            logger.warning("⚠️ No relevant news found, will use default content")
        
        # Step 2: Generate content using LLM
        logger.info("🧠 Generating LinkedIn post...")
        model_name = os.getenv('MODEL_NAME', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
        generator = ContentGenerator(model_name=model_name)
        post_content = generator.generate_post(news)
        
        # Step 3: Format and save post
        logger.info("📝 Formatting and saving post...")
        formatter = PostFormatter()
        formatted_post = formatter.format_for_linkedin(post_content)
        
        post_record = formatter.save_post(
            formatted_post,
            metadata={
                'news_count': len(news),
                'news_topics': [n['title'] for n in news[:3]] if news else [],
                'generated_by': model_name
            }
        )
        
        logger.info(f"✅ Post saved (ID: {post_record['id']})")
        
        # Step 4: Preview post
        logger.info("\n" + "=" * 50)
        logger.info("POST PREVIEW:")
        logger.info("=" * 50)
        logger.info(formatted_post)
        logger.info("=" * 50)
        logger.info(f"Character count: {len(formatted_post)}")
        
        # Step 5: Post to LinkedIn (optional, enable with flag)
        if os.getenv('AUTO_POST', 'false').lower() == 'true':
            logger.info("📤 Posting to LinkedIn...")
            publisher = LinkedInPublisher()
            success = publisher.post_content(formatted_post)
            
            if success:
                logger.info("✅ Successfully posted to LinkedIn!")
            else:
                logger.error("❌ Failed to post to LinkedIn")
        
        logger.info("\n🎉 Automation completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Automation failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()