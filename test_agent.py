#!/usr/bin/env python3
"""Test script for local development"""

from src.news_fetcher import AzureNewsFetcher
from src.content_generator import ContentGenerator
from src.post_formatter import PostFormatter
import logging

logging.basicConfig(level=logging.INFO)

def test_news_fetching():
    """Test news fetching"""
    print("\n📡 Testing News Fetcher...")
    fetcher = AzureNewsFetcher()
    news = fetcher.fetch_news(days_back=7)
    print(f"✅ Found {len(news)} articles")
    for item in news[:3]:
        print(f"  - {item['title'][:80]}...")
    return news

def test_content_generation(news):
    """Test content generation"""
    print("\n🧠 Testing Content Generator...")
    generator = ContentGenerator(model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    post = generator.generate_post(news)
    print(f"✅ Generated post ({len(post)} chars)")
    print("\n" + "="*50)
    print(post[:500] + "...\n")
    return post

def test_formatting(post):
    """Test formatting"""
    print("\n📝 Testing Post Formatter...")
    formatter = PostFormatter()
    formatted = formatter.format_for_linkedin(post)
    saved = formatter.save_post(post)
    print(f"✅ Saved as post #{saved['id']}")
    return saved

if __name__ == "__main__":
    print("🚀 Starting local tests...\n")
    
    # Test 1: Fetch news
    news = test_news_fetching()
    
    # Test 2: Generate content
    post = test_content_generation(news)
    
    # Test 3: Format and save
    saved = test_formatting(post)
    
    print("\n✅ All tests passed!")