#!/usr/bin/env python3
"""
End-to-End Testing Script for Azure AI LinkedIn Agent
Tests: News fetching → Content Generation → LinkedIn Login → Post Publishing
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.news_fetcher import AzureNewsFetcher
from src.content_generator import ContentGenerator
from src.post_formatter import PostFormatter
from src.linkedin_publisher import LinkedInPublisher

# Setup colorful logging
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }
    
    def format(self, record):
        levelname = record.levelname
        message = super().format(record)
        color = self.COLORS.get(levelname, '')
        return f"{color}{message}{self.COLORS['RESET']}"

# Setup logging
logger = logging.getLogger('E2E_Test')
logger.setLevel(logging.DEBUG)

# Console handler with colors
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter(
    '%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
))
logger.addHandler(console_handler)

# File handler
Path('data').mkdir(exist_ok=True)
file_handler = logging.FileHandler('data/e2e_test.log')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(file_handler)


class E2ETester:
    """Complete end-to-end testing orchestrator"""
    
    def __init__(self):
        self.results = {
            'test_start': datetime.now().isoformat(),
            'stages': {},
            'overall_success': False,
            'errors': []
        }
        
        # Check credentials
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        
        if not self.email or not self.password:
            logger.error("❌ LinkedIn credentials not configured!")
            logger.error("Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env file")
            sys.exit(1)
        
        logger.info(f"✅ Credentials found for: {self.email}")
    
    def print_header(self, text: str):
        """Print formatted header"""
        width = 80
        logger.info("\n" + "=" * width)
        logger.info(f"  {text}".center(width))
        logger.info("=" * width + "\n")
    
    def print_stage_result(self, stage: str, success: bool, details: str = ""):
        """Print stage result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{status} - {stage}")
        if details:
            logger.info(f"   {details}")
    
    def stage_1_news_fetching(self) -> Dict:
        """Test Stage 1: News Fetching"""
        self.print_header("STAGE 1: Testing News Fetching")
        
        try:
            logger.info("📡 Initializing news fetcher...")
            fetcher = AzureNewsFetcher()
            
            logger.info("🔍 Fetching Azure AI news (last 7 days)...")
            start_time = time.time()
            news = fetcher.fetch_news(days_back=7)
            fetch_time = time.time() - start_time
            
            # Validate results
            if news:
                logger.info(f"✅ Found {len(news)} relevant articles in {fetch_time:.2f}s")
                
                # Display top articles
                logger.info("\n📰 Top 3 Articles:")
                for i, article in enumerate(news[:3], 1):
                    logger.info(f"  {i}. {article['title'][:80]}...")
                    logger.info(f"     Published: {article['published'][:10]}")
                    logger.info(f"     Source: {article['source'].split('/')[2]}")
                
                # Save news
                fetcher.save_news(news, 'test_news.json')
                logger.info("\n💾 News saved to data/test_news.json")
                
                self.results['stages']['news_fetching'] = {
                    'success': True,
                    'articles_found': len(news),
                    'fetch_time': f"{fetch_time:.2f}s"
                }
                
                self.print_stage_result("News Fetching", True, f"Found {len(news)} articles")
                return {'success': True, 'data': news}
            else:
                logger.warning("⚠️ No articles found in the last 7 days")
                logger.info("Will use fallback content for testing")
                
                self.results['stages']['news_fetching'] = {
                    'success': True,
                    'articles_found': 0,
                    'note': 'No recent articles, using fallback'
                }
                
                self.print_stage_result("News Fetching", True, "No articles (will use fallback)")
                return {'success': True, 'data': []}
                
        except Exception as e:
            logger.error(f"❌ News fetching failed: {e}")
            self.results['stages']['news_fetching'] = {
                'success': False,
                'error': str(e)
            }
            self.print_stage_result("News Fetching", False, str(e))
            return {'success': False, 'error': str(e)}
    
    def stage_2_content_generation(self, news: List[Dict]) -> Dict:
        """Test Stage 2: Content Generation"""
        self.print_header("STAGE 2: Testing Content Generation")
        
        try:
            logger.info("🧠 Loading open-source LLM model...")
            
            # Try TinyLlama first (lightweight)
            model_name = os.getenv('MODEL_NAME', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
            logger.info(f"📚 Model: {model_name}")
            
            start_time = time.time()
            generator = ContentGenerator(model_name=model_name)
            load_time = time.time() - start_time
            
            logger.info(f"✅ Model loaded in {load_time:.2f}s")
            
            # Generate post
            logger.info("✍️ Generating LinkedIn post...")
            start_time = time.time()
            post_content = generator.generate_post(news)
            generation_time = time.time() - start_time
            
            logger.info(f"✅ Post generated in {generation_time:.2f}s")
            logger.info(f"📏 Character count: {len(post_content)}")
            
            # Display preview
            logger.info("\n" + "─" * 60)
            logger.info("📄 POST PREVIEW (first 300 chars):")
            logger.info("─" * 60)
            logger.info(post_content[:300] + "...")
            logger.info("─" * 60)
            
            # Validate content
            if len(post_content) < 100:
                logger.warning("⚠️ Post seems too short")
            elif len(post_content) > 3000:
                logger.warning("⚠️ Post exceeds LinkedIn limit")
            
            # Check for hashtags
            hashtags = [word for word in post_content.split() if word.startswith('#')]
            logger.info(f"🏷️ Hashtags found: {', '.join(hashtags)}")
            
            self.results['stages']['content_generation'] = {
                'success': True,
                'model': model_name,
                'load_time': f"{load_time:.2f}s",
                'generation_time': f"{generation_time:.2f}s",
                'char_count': len(post_content)
            }
            
            self.print_stage_result("Content Generation", True, f"{len(post_content)} chars generated")
            return {'success': True, 'data': post_content}
            
        except Exception as e:
            logger.error(f"❌ Content generation failed: {e}")
            
            # Try fallback without model
            logger.info("🔄 Trying fallback template-based generation...")
            try:
                generator = ContentGenerator(model_name="template")
                post_content = generator.generate_post(news)
                
                self.results['stages']['content_generation'] = {
                    'success': True,
                    'fallback': True,
                    'char_count': len(post_content)
                }
                
                self.print_stage_result("Content Generation", True, "Generated with fallback")
                return {'success': True, 'data': post_content}
                
            except Exception as fallback_error:
                self.results['stages']['content_generation'] = {
                    'success': False,
                    'error': str(e)
                }
                self.print_stage_result("Content Generation", False, str(e))
                return {'success': False, 'error': str(e)}
    
    def stage_3_post_formatting(self, content: str) -> Dict:
        """Test Stage 3: Post Formatting and Storage"""
        self.print_header("STAGE 3: Testing Post Formatting")
        
        try:
            logger.info("📝 Initializing post formatter...")
            formatter = PostFormatter()
            
            # Format the post
            logger.info("✨ Formatting post for LinkedIn...")
            formatted_post = formatter.format_for_linkedin(content)
            
            # Save to history
            logger.info("💾 Saving post to history...")
            post_record = formatter.save_post(
                formatted_post,
                metadata={
                    'test_run': True,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            logger.info(f"✅ Post saved as ID #{post_record['id']}")
            logger.info(f"📊 History now contains {formatter.history['total_posts']} posts")
            
            self.results['stages']['formatting'] = {
                'success': True,
                'post_id': post_record['id'],
                'total_posts': formatter.history['total_posts']
            }
            
            self.print_stage_result("Post Formatting", True, f"Saved as post #{post_record['id']}")
            return {'success': True, 'data': formatted_post}
            
        except Exception as e:
            logger.error(f"❌ Post formatting failed: {e}")
            self.results['stages']['formatting'] = {
                'success': False,
                'error': str(e)
            }
            self.print_stage_result("Post Formatting", False, str(e))
            return {'success': False, 'error': str(e)}
    
    def stage_4_linkedin_login(self) -> Dict:
        """Test Stage 4: LinkedIn Login (Headless)"""
        self.print_header("STAGE 4: Testing LinkedIn Login")
        
        publisher = None
        try:
            logger.info("🔐 Testing LinkedIn authentication...")
            publisher = LinkedInPublisher(self.email, self.password)
            
            # Test login
            logger.info("🌐 Launching browser (headless mode)...")
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Launch in headless mode for testing
                browser = p.chromium.launch(
                    headless=True,  # Set to False to see the browser
                    slow_mo=50
                )
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = context.new_page()
                
                # Navigate to LinkedIn login
                logger.info("📄 Navigating to LinkedIn login page...")
                page.goto('https://www.linkedin.com/login')
                page.wait_for_timeout(2000)
                
                # Take screenshot
                Path('data/screenshots').mkdir(exist_ok=True)
                page.screenshot(path='data/screenshots/01_login_page.png')
                logger.info("📸 Screenshot: Login page")
                
                # Fill credentials
                logger.info("⌨️ Entering credentials...")
                page.fill('input#username', self.email)
                page.fill('input#password', self.password)
                
                page.screenshot(path='data/screenshots/02_credentials_filled.png')
                logger.info("📸 Screenshot: Credentials filled")
                
                # Click sign in
                logger.info("🔘 Clicking Sign In button...")
                page.click('button[type="submit"]')
                
                # Wait for navigation
                logger.info("⏳ Waiting for login to complete...")
                try:
                    page.wait_for_url('**/feed/**', timeout=15000)
                    logger.info("✅ Login successful!")
                    
                    page.screenshot(path='data/screenshots/03_logged_in.png')
                    logger.info("📸 Screenshot: Logged in")
                    
                    # Verify login by checking for feed elements
                    if page.locator('div.feed-identity-module').is_visible():
                        logger.info("✅ Profile feed module visible")
                    
                    # Get profile name
                    try:
                        profile_name = page.locator('div.profile-card-profile-picture').get_attribute('alt')
                        logger.info(f"👤 Logged in as: {profile_name}")
                    except:
                        logger.info("👤 Profile name not captured (may be different layout)")
                    
                    # Save session state
                    context.storage_state(path='data/linkedin_state.json')
                    logger.info("💾 Session state saved for future use")
                    
                    self.results['stages']['login'] = {
                        'success': True,
                        'session_saved': True
                    }
                    
                    self.print_stage_result("LinkedIn Login", True, "Session saved")
                    
                except Exception as e:
                    logger.error(f"❌ Login may have failed: {e}")
                    
                    # Check for verification page
                    if 'checkpoint' in page.url or 'challenge' in page.url:
                        logger.warning("⚠️ LinkedIn requires additional verification")
                        logger.warning("Please complete verification manually")
                        
                        # Save screenshot of verification page
                        page.screenshot(path='data/screenshots/verification_required.png')
                        logger.info("📸 Screenshot: Verification page")
                    
                    self.results['stages']['login'] = {
                        'success': False,
                        'error': 'Verification required or login failed'
                    }
                    
                    self.print_stage_result("LinkedIn Login", False, "Verification may be needed")
                    return {'success': False, 'error': 'Login verification needed'}
                
                context.close()
                browser.close()
                
            return {'success': True, 'data': publisher}
            
        except Exception as e:
            logger.error(f"❌ Login test failed: {e}")
            self.results['stages']['login'] = {
                'success': False,
                'error': str(e)
            }
            self.print_stage_result("LinkedIn Login", False, str(e))
            return {'success': False, 'error': str(e)}
    
    def stage_5_post_publishing(self, content: str, publisher: LinkedInPublisher = None) -> Dict:
        """Test Stage 5: Actual Post Publishing"""
        self.print_header("STAGE 5: Testing Post Publishing")
        
        logger.warning("⚠️ About to publish a real post to LinkedIn!")
        logger.warning(f"📝 Post preview:\n{content[:200]}...\n")
        
        # Ask for confirmation
        if '--auto-publish' not in sys.argv:
            response = input("🤔 Publish this post to LinkedIn now? (yes/no): ").lower()
            if response != 'yes':
                logger.info("❌ Publishing cancelled by user")
                self.results['stages']['publishing'] = {
                    'success': False,
                    'cancelled': True
                }
                return {'success': False, 'cancelled': True}
        
        try:
            logger.info("📤 Starting LinkedIn publishing...")
            
            # Use existing publisher or create new one
            if publisher is None:
                publisher = LinkedInPublisher(self.email, self.password)
            
            # Publish with visual browser (not headless)
            logger.info("🌐 Launching browser with visible window...")
            
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                # Launch visible browser for reliability
                browser = p.chromium.launch(
                    headless=False,  # Show browser for debugging
                    slow_mo=100      # Slower for reliability
                )
                
                # Try to use saved session
                if Path('data/linkedin_state.json').exists():
                    logger.info("📂 Using saved session...")
                    context = browser.new_context(
                        storage_state='data/linkedin_state.json',
                        viewport={'width': 1920, 'height': 1080}
                    )
                else:
                    context = browser.new_context(
                        viewport={'width': 1920, 'height': 1080}
                    )
                
                page = context.new_page()
                
                # Go to feed
                logger.info("📄 Navigating to LinkedIn feed...")
                page.goto('https://www.linkedin.com/feed/')
                page.wait_for_timeout(3000)
                
                # Check if logged in
                if 'login' in page.url:
                    logger.info("🔐 Not logged in, performing login...")
                    page.goto('https://www.linkedin.com/login')
                    page.wait_for_timeout(2000)
                    
                    page.fill('input#username', self.email)
                    page.fill('input#password', self.password)
                    page.click('button[type="submit"]')
                    
                    try:
                        page.wait_for_url('**/feed/**', timeout=15000)
                        logger.info("✅ Login successful")
                        
                        # Save session
                        context.storage_state(path='data/linkedin_state.json')
                        
                    except:
                        logger.error("❌ Login failed during publishing")
                        page.screenshot(path='data/screenshots/publish_login_error.png')
                        return {'success': False, 'error': 'Login failed'}
                
                page.screenshot(path='data/screenshots/05_on_feed.png')
                logger.info("📸 Screenshot: On feed page")
                
                # Click "Start a post"
                logger.info("🔍 Looking for post creation button...")
                try:
                    # Try multiple selectors
                    selectors = [
                        'button.share-box-feed-entry__trigger',
                        'button[aria-label="Start a post"]',
                        'div.share-box-feed-entry__closed-share',
                        'button:has-text("Start a post")'
                    ]
                    
                    clicked = False
                    for selector in selectors:
                        try:
                            if page.locator(selector).is_visible(timeout=2000):
                                page.click(selector)
                                clicked = True
                                break
                        except:
                            continue
                    
                    if not clicked:
                        raise Exception("Could not find post button")
                    
                except Exception as e:
                    logger.error(f"❌ Could not find post button: {e}")
                    page.screenshot(path='data/screenshots/publish_no_button.png')
                    return {'success': False, 'error': 'Post button not found'}
                
                logger.info("✅ Post creation dialog opened")
                page.wait_for_timeout(2000)
                page.screenshot(path='data/screenshots/06_post_dialog.png')
                logger.info("📸 Screenshot: Post dialog")
                
                # Type the content
                logger.info("⌨️ Typing post content...")
                editor = page.locator('div.ql-editor').first
                editor.click()
                editor.fill('')
                page.wait_for_timeout(1000)
                
                # Type with natural delays
                editor.type(content, delay=10)  # Typing speed
                page.wait_for_timeout(2000)
                
                page.screenshot(path='data/screenshots/07_content_typed.png')
                logger.info("📸 Screenshot: Content typed")
                
                # Pause for review
                logger.info("⏸️ Pausing for 5 seconds to review post...")
                time.sleep(5)
                
                # Click Post button
                logger.info("🔘 Looking for Post button...")
                post_selectors = [
                    'button.share-actions__primary-action',
                    'button:has-text("Post")',
                    'button[aria-label="Post"]'
                ]
                
                posted = False
                for selector in post_selectors:
                    try:
                        post_button = page.locator(selector)
                        if post_button.is_visible(timeout=2000):
                            logger.info(f"✅ Clicking Post button: {selector}")
                            post_button.click()
                            posted = True
                            break
                    except:
                        continue
                
                if not posted:
                    raise Exception("Could not find Post button")
                
                # Wait for publishing
                logger.info("⏳ Waiting for post to publish...")
                page.wait_for_timeout(5000)
                
                page.screenshot(path='data/screenshots/08_post_published.png')
                logger.info("📸 Screenshot: After publishing")
                
                # Verify post appeared
                # Look for the post content on the page
                try:
                    first_sentence = content.split('\n')[0][:50]
                    if page.locator(f'text="{first_sentence}"').is_visible(timeout=5000):
                        logger.info("✅ Post confirmed on page!")
                    else:
                        logger.warning("⚠️ Could not verify post on page")
                except:
                    logger.warning("⚠️ Post verification skipped")
                
                # Save updated session
                context.storage_state(path='data/linkedin_state.json')
                logger.info("💾 Session updated")
                
                # Keep browser open for few seconds
                logger.info("⏳ Keeping browser open for 10 seconds...")
                time.sleep(10)
                
                context.close()
                browser.close()
            
            logger.info("✅ Post published successfully!")
            
            self.results['stages']['publishing'] = {
                'success': True,
                'published_at': datetime.now().isoformat()
            }
            
            self.print_stage_result("Post Publishing", True, "Posted to LinkedIn")
            return {'success': True}
            
        except Exception as e:
            logger.error(f"❌ Publishing failed: {e}")
            self.results['stages']['publishing'] = {
                'success': False,
                'error': str(e)
            }
            self.print_stage_result("Post Publishing", False, str(e))
            return {'success': False, 'error': str(e)}
    
    def run_full_test(self, skip_publish: bool = False):
        """Run all test stages in sequence"""
        self.print_header("🚀 AZURE AI LINKEDIN AGENT - FULL E2E TEST")
        
        logger.info(f"📅 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📧 Using account: {self.email}")
        logger.info(f"🤖 Model: {os.getenv('MODEL_NAME', 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')}")
        
        # Stage 1: News Fetching
        news_result = self.stage_1_news_fetching()
        if not news_result['success']:
            logger.error("❌ Cannot continue without news fetching")
            return False
        
        news_data = news_result.get('data', [])
        
        # Stage 2: Content Generation
        content_result = self.stage_2_content_generation(news_data)
        if not content_result['success']:
            logger.error("❌ Cannot continue without content")
            return False
        
        post_content = content_result['data']
        
        # Stage 3: Post Formatting
        format_result = self.stage_3_post_formatting(post_content)
        if not format_result['success']:
            logger.error("❌ Cannot continue without formatting")
            return False
        
        formatted_post = format_result['data']
        
        # Stage 4: LinkedIn Login
        login_result = self.stage_4_linkedin_login()
        
        # Stage 5: Post Publishing (optional)
        if not skip_publish:
            publish_result = self.stage_5_post_publishing(formatted_post)
        else:
            logger.info("⏭️ Skipping publishing stage")
            self.results['stages']['publishing'] = {'skipped': True}
        
        # Generate final report
        self.generate_report()
        
        return True
    
    def generate_report(self):
        """Generate final test report"""
        self.print_header("📊 E2E TEST RESULTS SUMMARY")
        
        passed = 0
        failed = 0
        skipped = 0
        
        for stage, result in self.results['stages'].items():
            if result.get('skipped'):
                skipped += 1
                logger.info(f"⏭️ {stage}: SKIPPED")
            elif result.get('success'):
                passed += 1
                logger.info(f"✅ {stage}: PASSED")
            else:
                failed += 1
                logger.info(f"❌ {stage}: FAILED")
        
        logger.info(f"\n📈 Total: {passed} passed, {failed} failed, {skipped} skipped")
        
        # Save report
        self.results['test_end'] = datetime.now().isoformat()
        self.results['summary'] = {
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'total': passed + failed + skipped
        }
        
        report_path = 'data/e2e_report.json'
        with open(report_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"\n📄 Full report saved to: {report_path}")
        
        # Print post location
        history_file = Path('data/post_history.json')
        if history_file.exists():
            logger.info(f"📝 Post saved in: {history_file}")
        
        # Print screenshots location
        screenshots_dir = Path('data/screenshots')
        if screenshots_dir.exists():
            screenshots = list(screenshots_dir.glob('*.png'))
            logger.info(f"📸 {len(screenshots)} screenshots saved in: {screenshots_dir}")
        
        if passed == len(self.results['stages']):
            logger.info("\n🎉 All tests passed successfully!")
        else:
            logger.warning("\n⚠️ Some tests failed. Check the logs.")


def main():
    """Main entry point for E2E testing"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Run E2E tests for Azure AI LinkedIn Agent')
    parser.add_argument(
        '--skip-publish',
        action='store_true',
        help='Skip actual LinkedIn publishing'
    )
    parser.add_argument(
        '--auto-publish',
        action='store_true',
        help='Auto-publish without confirmation'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run browser in headless mode'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║    AZURE AI LINKEDIN AGENT - END TO END TEST SUITE      ║
    ║         Testing: News → Content → LinkedIn Post         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Check environment
    if not os.getenv('LINKEDIN_EMAIL') or not os.getenv('LINKEDIN_PASSWORD'):
        print("❌ ERROR: LinkedIn credentials not configured!")
        print("\nPlease create a .env file with:")
        print("LINKEDIN_EMAIL=your.email@example.com")
        print("LINKEDIN_PASSWORD=your_password_here")
        return
    
    # Create necessary directories
    Path('data/screenshots').mkdir(parents=True, exist_ok=True)
    
    # Run tests
    tester = E2ETester()
    
    if args.skip_publish:
        print("\n⚠️ SKIP PUBLISH MODE: Will not post to LinkedIn")
    
    if args.auto_publish:
        print("\n⚠️ AUTO PUBLISH MODE: Will post without confirmation")
    
    try:
        tester.run_full_test(skip_publish=args.skip_publish)
    except KeyboardInterrupt:
        print("\n\n❌ Test interrupted by user")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        if tester:
            tester.results['overall_success'] = False
            tester.results['errors'].append(str(e))
            tester.generate_report()


if __name__ == "__main__":
    main()