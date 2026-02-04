#!/usr/bin/env python3
"""
Fully automated LinkedIn job application
Auto-login + auto-fill + auto-submit
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
    """Fully automated application"""
    print("=" * 60)
    print("Fully Automated LinkedIn Application - Adyen Data Engineer")
    print("=" * 60)
    
    with sync_playwright() as p:
        # Launch browser (visible for monitoring)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900}
        )
        page = context.new_page()
        
        try:
            # Step 1: Login to LinkedIn
            print("\n[1] Logging in to LinkedIn...")
            page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            
            # Fill email
            page.locator('input#username').fill(LINKEDIN_EMAIL)
            print(f"    ✓ Email filled: {LINKEDIN_EMAIL}")
            
            # Fill password
            page.locator('input#password').fill(LINKEDIN_PASSWORD)
            print("    ✓ Password filled")
            
            # Click login
            page.locator('button[type="submit"]').click()
            print("    ✓ Login submitted")
            
            # Wait for login to complete
            page.wait_for_timeout(5000)
            
            # Check if login successful
            if "feed" in page.url or "linkedin.com/in/" in page.url:
                print("    ✓ Login successful!")
            else:
                print(f"    ⚠️  Current URL: {page.url}")
                print("    Checking for security challenges...")
                
                # Check for CAPTCHA or verification
                if page.locator('text=/verify|challenge|captcha/i').first.is_visible(timeout=3000):
                    print("    ❌ Security verification detected - cannot proceed automatically")
                    print("    Please complete verification manually in the browser")
                    page.wait_for_timeout(30000)
                    return False
            
            # Step 2: Navigate to job page
            print("\n[2] Navigating to job page...")
            page.goto(JOB_URL, wait_until="networkidle")
            page.wait_for_timeout(3000)
            print(f"    ✓ Page loaded: {page.title()[:50]}")
            
            # Step 3: Look for Easy Apply button
            print("\n[3] Looking for Easy Apply button...")
            
            apply_selectors = [
                'button[data-control-name="jobdetails_topcard_inapply"]',
                'button:has-text("Easy Apply")',
                'button:has-text("Apply")',
                '.jobs-apply-button',
            ]
            
            apply_btn = None
            for selector in apply_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=3000):
                        apply_btn = btn
                        print(f"    ✓ Found apply button")
                        break
                except:
                    continue
            
            if not apply_btn:
                print("    ❌ No Easy Apply button found")
                print("    This job may require external application")
                return False
            
            # Click Apply
            print("\n[4] Clicking Apply...")
            apply_btn.click()
            page.wait_for_timeout(3000)
            
            # Step 5: Fill application form
            print("\n[5] Filling application form...")
            
            # Check for contact info form
            try:
                # Email
                email_field = page.locator('input[type="email"]').first
                if email_field.is_visible(timeout=2000):
                    current_email = email_field.input_value()
                    if not current_email:
                        email_field.fill(LINKEDIN_EMAIL)
                        print(f"    ✓ Email filled")
                    else:
                        print(f"    ✓ Email already set: {current_email}")
            except:
                pass
            
            # Phone
            try:
                phone_field = page.locator('input[type="tel"]').first
                if phone_field.is_visible(timeout=2000):
                    current_phone = phone_field.input_value()
                    if not current_phone:
                        phone_field.fill("+31645038614")
                        print(f"    ✓ Phone filled")
                    else:
                        print(f"    ✓ Phone already set")
            except:
                pass
            
            # Step 6: Upload resume
            print("\n[6] Uploading resume...")
            try:
                file_input = page.locator('input[type="file"]').first
                if file_input.is_visible(timeout=3000):
                    file_input.set_input_files(str(RESUME_PATH))
                    print(f"    ✓ Resume uploaded: {RESUME_PATH.name}")
                    page.wait_for_timeout(3000)
                else:
                    print("    ⚠️  No upload field (may be on next page)")
            except Exception as e:
                print(f"    ⚠️  Upload: {e}")
            
            # Step 7: Handle multi-page application
            print("\n[7] Processing application steps...")
            max_steps = 5
            for step in range(max_steps):
                print(f"\n    Step {step + 1}:")
                page.wait_for_timeout(2000)
                
                # Check for additional questions
                try:
                    # Look for text inputs that need filling
                    text_inputs = page.locator('input[type="text"]:visible').all()
                    for inp in text_inputs:
                        placeholder = inp.get_attribute('placeholder') or ''
                        label = inp.locator('xpath=../label').text_content() or ''
                        
                        # Fill common fields
                        if 'city' in label.lower() or 'city' in placeholder.lower():
                            inp.fill("Amsterdam")
                            print(f"      ✓ City filled")
                        elif 'country' in label.lower():
                            inp.fill("Netherlands")
                            print(f"      ✓ Country filled")
                except:
                    pass
                
                # Check for select dropdowns
                try:
                    selects = page.locator('select:visible').all()
                    for sel in selects:
                        # Try to select first non-empty option
                        options = sel.locator('option').all()
                        for opt in options:
                            val = opt.get_attribute('value')
                            if val and val.strip():
                                sel.select_option(value=val)
                                print(f"      ✓ Dropdown selected")
                                break
                except:
                    pass
                
                # Look for Next or Submit button
                next_btn = page.locator('button:has-text("Next"):visible').first
                submit_btn = page.locator('button:has-text("Submit"):visible, button:has-text("Submit application"):visible').first
                
                if submit_btn.is_visible(timeout=1000):
                    print("    ✓ Submit button found!")
                    
                    # Final confirmation before submit
                    print("\n" + "=" * 60)
                    print("🎯 READY TO SUBMIT")
                    print("=" * 60)
                    print(f"Job: Adyen Data Engineer")
                    print(f"Resume: {RESUME_PATH.name}")
                    print("\nSubmitting in 3 seconds...")
                    page.wait_for_timeout(3000)
                    
                    submit_btn.click()
                    print("\n    ✓ Application submitted!")
                    
                    # Wait for confirmation
                    page.wait_for_timeout(5000)
                    
                    # Check for success message
                    success_indicators = [
                        'text=/application.*submitted/i',
                        'text=/success/i',
                        'text=/thank you/i',
                    ]
                    
                    for indicator in success_indicators:
                        try:
                            if page.locator(indicator).first.is_visible(timeout=2000):
                                print("    ✓ Confirmation received!")
                                break
                        except:
                            pass
                    
                    # Update tracker
                    print("\n[8] Updating application tracker...")
                    update_tracker()
                    
                    return True
                    
                elif next_btn.is_visible(timeout=1000):
                    print("    → Clicking Next...")
                    next_btn.click()
                else:
                    print("    ⚠️  No action button found")
                    break
            
            print("\n⚠️  Application flow incomplete - manual review needed")
            page.wait_for_timeout(10000)
            return False
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()

def update_tracker():
    """Update the application tracker"""
    try:
        tracker_path = Path("C:/Users/huang/.openclaw/workspace/job-hunter/data/applications.json")
        
        # Read current content
        with open(tracker_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update Adyen entry to 'applied'
        for app in data.get('applications', []):
            if app.get('company') == 'Adyen':
                app['status'] = 'applied'
                app['timeline']['applied_at'] = datetime.now().isoformat()
                break
        
        # Write back
        with open(tracker_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("    ✓ Tracker updated: Adyen status -> 'applied'")
    except Exception as e:
        print(f"    ⚠️  Tracker update failed: {e}")

if __name__ == "__main__":
    success = fully_auto_apply()
    sys.exit(0 if success else 1)
