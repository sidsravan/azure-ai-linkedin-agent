"""LinkedIn Publisher - Posts content to LinkedIn using Playwright"""

from playwright.sync_api import sync_playwright, TimeoutError, Error as PlaywrightError
import logging
import os
import random
import time
from pathlib import Path
import json
from datetime import datetime
from typing import Optional, Dict
from .utils import logger, ConfigManager

class LinkedInPublisher:
    """Handles LinkedIn authentication and posting"""
    
    LINKEDIN_URLS = {
        'login': 'https://www.linkedin.com/login',
        'feed': 'https://www.linkedin.com/feed/',
        'post': 'https://www.linkedin.com/feed/'
    }
    
    def __init__(self):
        """Initialize LinkedIn publisher"""
        self.email = ConfigManager.get_env_var('LINKEDIN_EMAIL')
        self.password = ConfigManager.get_env_var('LINKEDIN_PASSWORD')
        self.state_file = Path('data/linkedin_session.json')
        self.screenshot_dir = Path('data/screenshots')
        self.screenshot_dir.mkdir(exist_ok=True)
        
        if not self.email or not self.password:
            raise ValueError(
                "LinkedIn credentials not found! Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env"
            )
    
    def _random_delay(self, min_sec: float = 0.3, max_sec: float = 1.5):
        """Add random delay to simulate human behavior"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _type_naturally(self, element, text: str):
        """Type text with natural timing"""
        for char in text:
            element.type(char, delay=random.randint(30, 100))
            # Occasionally pause (like a human thinking)
            if char in '.!?' and random.random() < 0.3:
                time.sleep(random.uniform(0.1, 0.3))
    
    def _setup_stealth(self, page):
        """Add stealth scripts to avoid detection"""
        page.add_init_script("""
            // Hide automation indicators
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Fake plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Fake languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Override chrome runtime
            window.chrome = {
                runtime: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                Promise.resolve({state: Notification.permission}) :
                originalQuery(parameters)
            );
        """)
    
    def authenticate(self, headless: bool = False) -> bool:
        """
        Authenticate with LinkedIn and save session
        
        Args:
            headless: Run browser in headless mode
        
        Returns:
            True if authentication successful
        """
        logger.info(f"🔐 Authenticating with LinkedIn as {self.email}")
        
        with sync_playwright() as p:
            # Launch browser with stealth settings
            browser = p.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=IsolateOrigins,site-per-process',
                    '--no-sandbox'
                ]
            )
            
            # Create context with realistic fingerprint
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/Chicago',
                screen={'width': 1920, 'height': 1080},
                color_scheme='light'
            )
            
            page = context.new_page()
            self._setup_stealth(page)
            
            try:
                # Check if we have a saved session
                if self.state_file.exists():
                    logger.info("📂 Trying saved session...")
                    context.storage_state(path=str(self.state_file))
                    page.goto(self.LINKEDIN_URLS['feed'])
                    self._random_delay(2, 4)
                    
                    # Verify session is still valid
                    if 'login' not in page.url and 'feed' in page.url:
                        logger.info("✅ Session still valid")
                        return True
                    else:
                        logger.info("Session expired, performing fresh login")
                
                # Perform fresh login
                logger.info("🌐 Navigating to LinkedIn login...")
                page.goto(self.LINKEDIN_URLS['login'])
                page.wait_for_load_state('networkidle')
                self._random_delay(2, 3)
                
                # Take screenshot to debug form
                page.screenshot(path=str(self.screenshot_dir / 'login_page.png'))
                logger.info("📸 Login page screenshot saved")
                
                # Fill credentials with multiple selector attempts
                logger.info("⌨️  Entering credentials...")
                
                # Try multiple selector strategies for username
                username_selectors = ['input[name="session_key"]', '#username', 'input[type="email"]', 'input[data-id="username"]']
                username_filled = False
                
                for selector in username_selectors:
                    try:
                        username_input = page.locator(selector)
                        if username_input.is_visible(timeout=2000):
                            username_input.fill(self.email)
                            self._random_delay(0.5, 1)
                            username_filled = True
                            logger.info(f"✓ Username entered")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue
                
                if not username_filled:
                    logger.error("❌ Could not find username field - tried all selectors")
                    page.screenshot(path=str(self.screenshot_dir / 'no_username_field.png'))
                    return False
                
                # Try multiple selector strategies for password
                password_selectors = ['input[name="session_password"]', '#password', 'input[type="password"]', 'input[data-id="password"]']
                password_filled = False
                
                for selector in password_selectors:
                    try:
                        password_input = page.locator(selector)
                        if password_input.is_visible(timeout=2000):
                            password_input.fill(self.password)
                            self._random_delay(0.5, 1)
                            password_filled = True
                            logger.info(f"✓ Password entered")
                            break
                    except Exception as e:
                        logger.debug(f"Selector {selector} failed: {e}")
                        continue
                
                if not password_filled:
                    logger.error("❌ Could not find password field - tried all selectors")
                    page.screenshot(path=str(self.screenshot_dir / 'no_password_field.png'))
                    return False
                
                self._random_delay(0.5, 1)
                
                # Take screenshot before clicking login
                page.screenshot(path=str(self.screenshot_dir / 'before_login.png'))
                
                # Click login button - try multiple selectors
                logger.info("🔘 Clicking Sign In...")
                signin_selectors = ['button[type="submit"]', 'button:has-text("Sign in")', 'button:has-text("Log in")', 'button[aria-label="Sign in"]']
                clicked = False
                
                for selector in signin_selectors:
                    try:
                        signin_button = page.locator(selector).first
                        if signin_button.is_visible(timeout=2000):
                            signin_button.click()
                            clicked = True
                            logger.info("✓ Sign in button clicked")
                            break
                    except Exception as e:
                        logger.debug(f"Signin selector {selector} failed: {e}")
                        continue
                
                if not clicked:
                    logger.error("❌ Could not find or click sign in button")
                    page.screenshot(path=str(self.screenshot_dir / 'no_signin_button.png'))
                    return False
                
                # Wait for navigation or error
                try:
                    page.wait_for_url('**/feed/**', timeout=15000)
                    logger.info("✅ Login successful!")
                    
                    # Check for security notification
                    self._random_delay(2, 3)
                    
                    # Save session for future use
                    context.storage_state(path=str(self.state_file))
                    logger.info(f"💾 Session saved to {self.state_file}")
                    
                    return True
                    
                except TimeoutError:
                    # Check what went wrong
                    current_url = page.url
                    logger.error(f"Login failed. Current URL: {current_url}")
                    
                    # Take error screenshot
                    page.screenshot(path=str(self.screenshot_dir / 'login_failed.png'))
                    
                    if 'checkpoint' in current_url:
                        logger.error("🔒 Account requires verification")
                        logger.error("💡 Please login manually in a regular browser first")
                    elif 'login' in current_url:
                        logger.error("❌ Invalid credentials or login blocked")
                    
                    return False
            
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                page.screenshot(path=str(self.screenshot_dir / 'auth_error.png'))
                return False
            
            finally:
                context.close()
                browser.close()
    
    def post_content(self, content: str, dry_run: bool = False) -> Dict:
        """
        Post content to LinkedIn
        
        Args:
            content: The post content to publish
            dry_run: If True, stop before clicking Post button
        
        Returns:
            Dict with post status information        """
        result = {
            'success': False,
            'posted': False,
            'error': None,
            'timestamp': datetime.now().isoformat()
        }
        
        if len(content) > 3000:
            result['error'] = 'Content too long for LinkedIn (max 3000 chars)'
            return result
        
        logger.info("📤 Publish to LinkedIn")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,  # Show browser for transparency
                slow_mo=50       # Slow down for reliability
            )
            
            # Try to use saved state
            context = None
            if self.state_file.exists():
                context = browser.new_context(
                    storage_state=str(self.state_file),
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
            else:
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
            
            page = context.new_page()
            self._setup_stealth(page)
            
            try:
                # Navigate to feed
                page.goto(self.LINKEDIN_URLS['feed'])
                self._random_delay(3, 5)
                
                # Check if we need to login
                if 'login' in page.url:
                    logger.info("Not logged in, authenticating first...")
                    auth_success = self.authenticate(headless=False)
                    
                    if not auth_success:
                        result['error'] = 'Authentication failed'
                        return result
                    
                    # Reload with authenticated context
                    page.goto(self.LINKEDIN_URLS['feed'])
                    self._random_delay(3, 5)
                
                # Find and click "Start a post" button
                logger.info("🔍 Looking for post creation button...")
                
                posted = False
                # Try different selectors
                selectors = [
                    'button.share-box-feed-entry__trigger',
                    'button:has-text("Start a post")',
                    'div.share-box-feed-entry__closed-share',
                    '[aria-label="Start a post"]'
                ]
                
                for selector in selectors:
                    try:
                        element = page.locator(selector).first
                        if element.is_visible(timeout=3000):
                            element.click()
                            posted = True
                            break
                    except:
                        continue
                
                if not posted:
                    result['error'] = 'Could not find post creation button'
                    page.screenshot(path=str(self.screenshot_dir / 'no_post_button.png'))
                    return result
                
                logger.info("✅ Post dialog opened")
                self._random_delay(1, 2)
                
                # Type the content
                logger.info("⌨️  Typing post content...")
                editor = page.locator('div.ql-editor').first
                editor.click()
                self._random_delay(0.5, 1)
                
                # Clear any existing text
                editor.fill('')
                self._random_delay(0.5, 1)
                
                # Type the content
                self._type_naturally(editor, content)
                
                logger.info(f"✅ Content typed ({len(content)} characters)")
                self._random_delay(2, 3)
                
                # Take screenshot before posting
                page.screenshot(path=str(self.screenshot_dir / 'ready_to_post.png'))
                
                if dry_run:
                    logger.info("🏁 Dry run - stopping before posting")
                    result['success'] = True
                    result['dry_run'] = True
                    
                    # Close dialog
                    try:
                        page.click('button:has-text("Cancel")')
                    except:
                        page.keyboard.press('Escape')
                    
                    return result
                
                # Click Post button
                logger.info("🔘 Clicking Post button...")
                
                posted = False
                post_selectors = [
                    'button.share-actions__primary-action',
                    'button:has-text("Post"):not([aria-label])',
                    'button.ml4[data-control-name="share.post"]'
                ]
                
                for selector in post_selectors:
                    try:
                        element = page.locator(selector).last
                        if element.is_visible(timeout=3000):
                            element.click()
                            posted = True
                            break
                    except:
                        continue
                
                if not posted:
                    result['error'] = 'Could not find Post button'
                    page.screenshot(path=str(self.screenshot_dir / 'no_post_button_found.png'))
                    return result
                
                # Wait for post to be published
                logger.info("⏳ Waiting for post to publish...")
                self._random_delay(5, 8)
                
                # Verify post appeared
                try:
                    # Wait for the post dialog to close
                    page.wait_for_selector('div.share-box-feed-entry__closed-share', timeout=10000)
                    logger.info("✅ Post appears to be published!")
                    
                    result['success'] = True
                    result['posted'] = True
                    
                    # Save updated session
                    context.storage_state(path=str(self.state_file))
                    
                except:
                    logger.warning("⚠️  Could not verify post, but it may have succeeded")
                    result['success'] = True
                    result['posted'] = True
                    result['warning'] = 'Post verification failed but action completed'
                
                # Keep browser open for a few seconds to see result
                if not self._is_github_actions():
                    logger.info("Keeping browser open for 10 seconds - take a look!")
                    time.sleep(10)
                
                return result
                
            except Exception as e:
                logger.error(f"Posting error: {e}")
                result['error'] = str(e)
                page.screenshot(path=str(self.screenshot_dir / 'posting_error.png'))
                return result
            
            finally:
                context.close()
                browser.close()
    
    def _is_github_actions(self) -> bool:
        """Check if running in GitHub Actions"""
        return ConfigManager.is_github_actions()