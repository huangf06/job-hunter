#!/usr/bin/env python3
"""
Test automated application for Adyen Data Engineer position
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
JOB_URL = "https://nl.linkedin.com/jobs/view/data-engineer-at-adyen-4257029457"
RESUME_PATH = Path("C:/Users/huang/.openclaw/workspace/job-hunter/output/Fei_Huang_Adyen_Data_Engineer.pdf")

def test_apply_adyen():
    """Test applying to Adyen position"""
    print("=" * 60)
    print("Testing Automated Application - Adyen Data Engineer")
    print("=" * 60)
    
    with sync_playwright() as p:
        # Launch browser (visible for testing)
        browser = p.chromium.launch(headless=False, slow_mo=100)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()
        
        try:
            # Step 1: Open job page
            print("\n[1] Opening LinkedIn job page...")
            page.goto(JOB_URL, wait_until="networkidle", timeout=30000)
            print(f"    Page loaded: {page.title()}")
            
            # Wait for page to settle
            page.wait_for_timeout(3000)
            
            # Step 2: Look for Apply button
            print("\n[2] Looking for Apply button...")
            
            # Possible selectors for apply button
            apply_selectors = [
                'button[data-control-name="jobdetails_topcard_inapply"]',
                'button:has-text("Apply")',
                'button:has-text("Easy Apply")',
                '.jobs-apply-button',
                '[data-control-name="jobdetails_topcard_inapply"]',
            ]
            
            apply_button = None
            for selector in apply_selectors:
                try:
                    apply_button = page.locator(selector).first
                    if apply_button.is_visible(timeout=2000):
                        print(f"    Found apply button: {selector}")
                        break
                except:
                    continue
            
            if not apply_button or not apply_button.is_visible():
                print("    ❌ No apply button found - may require login or different layout")
                # Take screenshot for debugging
                screenshot_path = "adyen_apply_debug.png"
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"    Screenshot saved: {screenshot_path}")
                return False
            
            # Step 3: Click Apply
            print("\n[3] Clicking Apply button...")
            apply_button.click()
            page.wait_for_timeout(2000)
            
            # Step 4: Check what happens next
            print("\n[4] Checking application flow...")
            
            # Check if it's Easy Apply (form opens) or external redirect
            current_url = page.url
            print(f"    Current URL: {current_url}")
            
            if "linkedin.com" in current_url and "jobs" in current_url:
                # Likely Easy Apply modal opened
                print("    ✓ Easy Apply modal detected")
                
                # Look for form fields
                form_selectors = [
                    'input[type="email"]',
                    'input[type="tel"]',
                    'input[name="*email*"]',
                    'input[placeholder*="email" i]',
                ]
                
                for selector in form_selectors:
                    try:
                        field = page.locator(selector).first
                        if field.is_visible(timeout=1000):
                            print(f"    Found form field: {selector}")
                    except:
                        pass
                
                # Look for file upload
                upload_selectors = [
                    'input[type="file"]',
                    'button:has-text("Upload resume")',
                    'button:has-text("Choose file")',
                ]
                
                for selector in upload_selectors:
                    try:
                        upload = page.locator(selector).first
                        if upload.is_visible(timeout=1000):
                            print(f"    Found upload button: {selector}")
                            
                            # Try to upload resume
                            if RESUME_PATH.exists():
                                print(f"    Uploading resume: {RESUME_PATH}")
                                upload.set_input_files(str(RESUME_PATH))
                                print("    ✓ Resume uploaded")
                            break
                    except Exception as e:
                        print(f"    Upload error: {e}")
                
                # Look for Next/Submit buttons
                button_selectors = [
                    'button:has-text("Next")',
                    'button:has-text("Submit")',
                    'button:has-text("Apply")',
                    'button[type="submit"]',
                ]
                
                for selector in button_selectors:
                    try:
                        btn = page.locator(selector).first
                        if btn.is_visible(timeout=1000):
                            print(f"    Found button: {selector}")
                    except:
                        pass
                
                print("\n    ⚠️  Application form detected but NOT submitting")
                print("    (Waiting for manual review)")
                
                # Keep browser open for 30 seconds to review
                print("\n    Browser will stay open for 30 seconds...")
                page.wait_for_timeout(30000)
                
            else:
                # External redirect
                print(f"    ⚠️  Redirected to external site: {current_url}")
                print("    This requires company-specific automation")
                
                # Keep browser open for review
                page.wait_for_timeout(10000)
            
            return True
            
        except PlaywrightTimeout as e:
            print(f"\n    ❌ Timeout error: {e}")
            return False
        except Exception as e:
            print(f"\n    ❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    success = test_apply_adyen()
    sys.exit(0 if success else 1)
