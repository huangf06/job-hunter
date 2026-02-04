#!/usr/bin/env python3
"""
Semi-automated job application - LinkedIn Easy Apply
Fills form automatically, waits for user confirmation before submitting
"""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# Configuration
JOB_URL = "https://nl.linkedin.com/jobs/view/data-engineer-at-adyen-4257029457"
RESUME_PATH = Path("C:/Users/huang/.openclaw/workspace/job-hunter/output/Fei_Huang_Adyen_Data_Engineer.pdf")

# User info (should be moved to config)
USER_INFO = {
    "first_name": "Fei",
    "last_name": "Huang",
    "email": "huangf06@gmail.com",
    "phone": "+31645038614",
    "location": "Amsterdam, Netherlands",
    "linkedin": "linkedin.com/in/huangf06"
}

def semi_auto_apply():
    """Semi-automated application with user confirmation"""
    print("=" * 60)
    print("Semi-Automated LinkedIn Application - Adyen Data Engineer")
    print("=" * 60)
    print("\n[WARN] Please log in to LinkedIn when the browser opens")
    print("After login, the script will automatically fill the form.")
    print("\nPress Enter to start...")
    input()
    
    with sync_playwright() as p:
        # Launch browser (visible)
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900}
        )
        page = context.new_page()
        
        try:
            # Step 1: Open LinkedIn login
            print("\n[1] Opening LinkedIn...")
            page.goto("https://www.linkedin.com/login", wait_until="networkidle")
            print("    Please log in manually...")
            print("    (Waiting for login - navigate to the job page after login)")
            
            # Wait for user to navigate to job page
            print("\n[2] Navigate to the job page:")
            print(f"    {JOB_URL}")
            print("\nPress Enter when you're on the job page...")
            input()
            
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
                        print(f"    ✓ Found: {selector}")
                        break
                except:
                    continue
            
            if not apply_btn:
                print("    ❌ No Easy Apply button found")
                print("    This job may require external application")
                return False
            
            # Click Apply
            print("\n[4] Clicking Apply button...")
            apply_btn.click()
            page.wait_for_timeout(2000)
            
            # Step 5: Fill form fields
            print("\n[5] Filling application form...")
            
            # Try to fill contact info
            fields_filled = []
            
            # Email
            try:
                email_field = page.locator('input[type="email"]').first
                if email_field.is_visible(timeout=1000):
                    email_field.fill(USER_INFO["email"])
                    fields_filled.append("email")
            except:
                pass
            
            # Phone
            try:
                phone_field = page.locator('input[type="tel"]').first
                if phone_field.is_visible(timeout=1000):
                    phone_field.fill(USER_INFO["phone"])
                    fields_filled.append("phone")
            except:
                pass
            
            # First name
            try:
                fname_field = page.locator('input[name*="first" i]').first
                if fname_field.is_visible(timeout=1000):
                    fname_field.fill(USER_INFO["first_name"])
                    fields_filled.append("first_name")
            except:
                pass
            
            # Last name
            try:
                lname_field = page.locator('input[name*="last" i]').first
                if lname_field.is_visible(timeout=1000):
                    lname_field.fill(USER_INFO["last_name"])
                    fields_filled.append("last_name")
            except:
                pass
            
            print(f"    ✓ Filled fields: {', '.join(fields_filled)}")
            
            # Step 6: Upload resume
            print("\n[6] Uploading resume...")
            try:
                # Look for file input
                file_input = page.locator('input[type="file"]').first
                if file_input.is_visible(timeout=2000):
                    file_input.set_input_files(str(RESUME_PATH))
                    print(f"    ✓ Uploaded: {RESUME_PATH.name}")
                    page.wait_for_timeout(2000)
                else:
                    print("    ⚠️  No file upload field found (may be on next page)")
            except Exception as e:
                print(f"    ⚠️  Upload issue: {e}")
            
            # Step 7: Check for additional questions
            print("\n[7] Checking for additional questions...")
            
            # Common additional questions
            question_selectors = [
                'input[type="text"]',
                'select',
                'textarea',
                'input[type="radio"]',
            ]
            
            additional_fields = []
            for selector in question_selectors:
                fields = page.locator(selector).all()
                for field in fields:
                    try:
                        if field.is_visible():
                            # Get label or placeholder
                            label = field.locator('xpath=../label').text_content() or \
                                   field.get_attribute('placeholder') or \
                                   field.get_attribute('aria-label') or \
                                   'Unknown field'
                            additional_fields.append(label[:50])
                    except:
                        pass
            
            if additional_fields:
                print(f"    ⚠️  Additional questions detected ({len(additional_fields)} fields):")
                for field in additional_fields[:5]:
                    print(f"      - {field}")
            else:
                print("    ✓ No additional questions")
            
            # Step 8: Look for Next/Submit buttons
            print("\n[8] Application form status:")
            
            button_selectors = [
                ('Next', 'button:has-text("Next")'),
                ('Submit', 'button:has-text("Submit")'),
                ('Submit application', 'button:has-text("Submit application")'),
                ('Apply', 'button:has-text("Apply")'),
            ]
            
            found_buttons = []
            for name, selector in button_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=1000):
                        found_buttons.append(name)
                except:
                    pass
            
            if found_buttons:
                print(f"    Available buttons: {', '.join(found_buttons)}")
            
            # Summary
            print("\n" + "=" * 60)
            print("✅ FORM AUTO-FILLED SUCCESSFULLY")
            print("=" * 60)
            print(f"\nResume: {RESUME_PATH.name}")
            print(f"Fields filled: {', '.join(fields_filled)}")
            
            if additional_fields:
                print(f"\n⚠️  {len(additional_fields)} additional questions need manual handling")
            
            print("\n🎯 READY FOR SUBMISSION")
            print("\nOptions:")
            print("  1. Type 'submit' and press Enter - I will click the Submit button")
            print("  2. Type 'next' and press Enter - I will click Next (if multi-page)")
            print("  3. Press Enter alone - Keep browser open for manual review")
            print("\nYour choice: ", end='')
            
            user_input = input().strip().lower()
            
            if user_input == 'submit':
                print("\n[9] Submitting application...")
                try:
                    submit_btn = page.locator('button:has-text("Submit")').first
                    if not submit_btn.is_visible():
                        submit_btn = page.locator('button:has-text("Submit application")').first
                    
                    if submit_btn.is_visible():
                        submit_btn.click()
                        print("    ✓ Application submitted!")
                        page.wait_for_timeout(3000)
                        
                        # Check for confirmation
                        if page.locator('text=/application.*submitted/i').first.is_visible(timeout=3000):
                            print("    ✓ Confirmation message received")
                    else:
                        print("    ❌ Submit button not found")
                except Exception as e:
                    print(f"    ❌ Error: {e}")
                    
            elif user_input == 'next':
                print("\n[9] Clicking Next...")
                try:
                    next_btn = page.locator('button:has-text("Next")').first
                    if next_btn.is_visible():
                        next_btn.click()
                        print("    ✓ Proceeded to next page")
                        print("    (Browser stays open for manual review)")
                        page.wait_for_timeout(30000)
                except Exception as e:
                    print(f"    ❌ Error: {e}")
            else:
                print("\n[9] Browser stays open for manual review...")
                print("    (Closing in 60 seconds)")
                page.wait_for_timeout(60000)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    success = semi_auto_apply()
    sys.exit(0 if success else 1)
