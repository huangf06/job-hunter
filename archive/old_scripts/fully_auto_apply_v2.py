#!/usr/bin/env python3
"""
Fully automated LinkedIn job application - v2 with better error handling
"""

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Load credentials
CONFIG_PATH = Path(__file__).parent / "config" / "credentials.json"
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)

LINKEDIN_EMAIL = config['linkedin']['email']
LINKEDIN_PASSWORD = config['linkedin']['password']

# Job and resume info
JOB_URL = "https://nl.linkedin.com/jobs/view/data-engineer-at-adyen-4257029457"
RESUME_PATH = Path("C:/Users/huang/.openclaw/workspace/job-hunter/output/Fei_Huang_Adyen_Data_Engineer.pdf")

def fully_auto_apply():
    """Fully automated application with retry logic"""
    print("=" * 60)
    print("Fully Automated LinkedIn Application v2 - Adyen Data Engineer")
    print("=" * 60)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900}
        )
        page = context.new_page()
        
        try:
            # Step 1: Login to LinkedIn
            print("\n[1] Logging in to LinkedIn...")
            page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=15000)
            
            page.locator('input#username').fill(LINKEDIN_EMAIL)
            page.locator('input#password').fill(LINKEDIN_PASSWORD)
            page.locator('button[type="submit"]').click()
            
            page.wait_for_timeout(5000)
            
            if "login" in page.url:
                print("    ❌ Login failed - check credentials or security challenge")
                return False
            
            print("    ✓ Login successful!")
            
            # Step 2: Navigate to job page (with shorter timeout)
            print("\n[2] Navigating to job page...")
            try:
                page.goto(JOB_URL, wait_until="domcontentloaded", timeout=20000)
            except PlaywrightTimeout:
                print("    ⚠️  Page load timeout, retrying with load...")
                page.goto(JOB_URL, wait_until="load", timeout=20000)
            
            page.wait_for_timeout(5000)
            print(f"    ✓ Page loaded: {page.title()[:40]}")
            
            # Step 3: Look for Apply button
            print("\n[3] Looking for Apply button...")
            
            # Wait for job details to load
            page.wait_for_selector('.jobs-unified-top-card', timeout=10000)
            
            apply_btn = None
            selectors = [
                'button[data-control-name="jobdetails_topcard_inapply"]',
                '.jobs-apply-button',
                'button:has-text("Easy Apply")',
            ]
            
            for selector in selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        apply_btn = btn
                        print(f"    ✓ Found apply button")
                        break
                except:
                    continue
            
            if not apply_btn:
                print("    ❌ No Easy Apply button - external application required")
                return False
            
            # Click Apply
            print("\n[4] Starting application...")
            apply_btn.click()
            page.wait_for_timeout(3000)
            
            # Step 5: Process application form
            print("\n[5] Filling application...")
            
            max_pages = 5
            for page_num in range(max_pages):
                print(f"\n    Page {page_num + 1}:")
                page.wait_for_timeout(2000)
                
                # Fill contact info on first page
                if page_num == 0:
                    try:
                        email_field = page.locator('input[type="email"]').first
                        if email_field.is_visible(timeout=1000):
                            email_field.fill(LINKEDIN_EMAIL)
                            print("      ✓ Email")
                    except:
                        pass
                    
                    try:
                        phone_field = page.locator('input[type="tel"]').first
                        if phone_field.is_visible(timeout=1000):
                            phone_field.fill("+31645038614")
                            print("      ✓ Phone")
                    except:
                        pass
                    
                    # Upload resume
                    try:
                        file_input = page.locator('input[type="file"]').first
                        if file_input.is_visible(timeout=1000):
                            file_input.set_input_files(str(RESUME_PATH))
                            print(f"      ✓ Resume uploaded")
                            page.wait_for_timeout(2000)
                    except:
                        pass
                
                # Fill any visible text inputs
                try:
                    text_inputs = page.locator('input[type="text"]:visible').all()
                    for inp in text_inputs:
                        val = inp.input_value()
                        if not val:
                            placeholder = inp.get_attribute('placeholder') or ''
                            if 'city' in placeholder.lower():
                                inp.fill("Amsterdam")
                                print("      ✓ City")
                            elif 'country' in placeholder.lower():
                                inp.fill("Netherlands")
                                print("      ✓ Country")
                except:
                    pass
                
                # Check for buttons
                submit_btn = page.locator('button:has-text("Submit application"):visible, button:has-text("Submit"):visible').first
                next_btn = page.locator('button:has-text("Next"):visible').first
                
                if submit_btn.is_visible(timeout=1000):
                    print("\n    ✓✓✓ SUBMIT BUTTON FOUND!")
                    page.wait_for_timeout(2000)
                    submit_btn.click()
                    print("    ✓ Application submitted!")
                    
                    page.wait_for_timeout(5000)
                    update_tracker()
                    return True
                
                elif next_btn.is_visible(timeout=1000):
                    next_btn.click()
                    print("      → Next page")
                else:
                    print("      ⚠️  No button found")
                    break
            
            print("\n⚠️  Could not complete - manual review needed")
            page.wait_for_timeout(10000)
            return False
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            return False
        finally:
            browser.close()

def update_tracker():
    """Update tracker"""
    try:
        tracker_path = Path("C:/Users/huang/.openclaw/workspace/job-hunter/data/applications.json")
        with open(tracker_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update Adyen entry to 'applied'
        for app in data.get('applications', []):
            if app.get('company') == 'Adyen':
                app['status'] = 'applied'
                app['timeline']['applied_at'] = datetime.now().isoformat()
                break
        
        with open(tracker_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("\n[6] ✓ Tracker updated: Adyen -> 'applied'")
    except Exception as e:
        print(f"\n[6] ⚠️  Tracker update failed: {e}")

if __name__ == "__main__":
    success = fully_auto_apply()
    sys.exit(0 if success else 1)
