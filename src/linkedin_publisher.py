from playwright.sync_api import sync_playwright, TimeoutError
import logging
import os
from pathlib import Path
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LinkedInPublisher:
    """Automates LinkedIn posting using Playwright"""
    
    def __init__(self, email: str = None, password: str = None):
        self.email = email or os.getenv('LINKEDIN_EMAIL')
        self.password = password or os.getenv('LINKEDIN_PASSWORD')
        self.state_file = 'data/linkedin_state.json'
    
    def is_logged_in(self) -> bool:
        """Check if saved session exists"""
        return Path(self.state_file).exists()
    
    def post_content(self, content: str) -> bool:
        """Post content to LinkedIn"""
        if not self.email or not self.password:
            logger.error("LinkedIn credentials not configured")
            return False
        
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(
                headless=False,  # Set to True in production
                slow_mo=100  # Slow down for reliability
            )
            
            context = None
            
            try:
                # Try to use saved state
                if self.is_logged_in():
                    logger.info("Using saved LinkedIn session")
                    context = browser.new_context(storage_state=self.state_file)
                    page = context.new_page()
                    
                    # Verify we're still logged in
                    page.goto('https://www.linkedin.com/feed/')
                    page.wait_for_timeout(3000)
                    
                    if 'login' in page.url:
                        logger.info("Session expired, re-logging in")
                        context.close()
                        context = None
                
                if not context:
                    # Create new context with realistic viewport
                    context = browser.new_context(
                        viewport={'width': 1920, 'height': 1080},
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    )
                    page = context.new_page()
                    
                    # Login
                    logger.info("Logging into LinkedIn...")
                    page.goto('https://www.linkedin.com/login')
                    page.wait_for_timeout(2000)
                    
                    # Fill credentials
                    page.fill('input#username', self.email)
                    page.fill('input#password', self.password)
                    page.click('button[type="submit"]')
                    
                    # Wait for login
                    page.wait_for_url('**/feed/**', timeout=15000)
                    logger.info("Login successful!")
                    
                    # Save state
                    context.storage_state(path=self.state_file)
                    logger.info("Saved login state")
                
                # Navigate to create post
                logger.info("Creating post...")
                page.goto('https://www.linkedin.com/feed/')
                page.wait_for_timeout(3000)
                
                # Click "Start a post"
                try:
                    page.click('button.share-box-feed-entry__trigger, button[aria-label="Start a post"]')
                except:
                    # Alternative selector
                    page.click('div.share-box-feed-entry__closed-share')
                
                page.wait_for_timeout(2000)
                
                # Type the post content
                editor = page.locator('div.ql-editor').first
                editor.click()
                
                # Clear default text if any
                editor.fill('')
                page.wait_for_timeout(500)
                
                # Type content with proper formatting
                editor.type(content, delay=50)
                page.wait_for_timeout(2000)
                
                # Click Post button
                post_button = page.locator('button.share-actions__primary-action')
                post_button.wait_for(state='visible', timeout=5000)
                post_button.click()
                
                # Wait for post to complete
                page.wait_for_timeout(5000)
                
                logger.info("Post published successfully!")
                return True
                
            except TimeoutError as e:
                logger.error(f"Timeout during LinkedIn automation: {e}")
                return False
            except Exception as e:
                logger.error(f"Error posting to LinkedIn: {e}")
                page.screenshot(path='data/error_screenshot.png')
                return False
            finally:
                if context:
                    context.close()
                browser.close()