from playwright.sync_api import sync_playwright
import time
import os

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    # 設置視窗大小
    page.set_viewport_size({"width": 1280, "height": 800})
    
    print("Navigating to http://localhost:5173 ...")
    page.goto('http://localhost:5173')
    
    print("Waiting for page load state...")
    page.wait_for_load_state('networkidle')
    
    # 模擬滾動到頁面底部以觸發所有 framer-motion 滾動動畫
    print("Simulating scroll to trigger animations...")
    for i in range(1, 11):
        page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {i} / 10)")
        time.sleep(0.3)
    
    # 滾回頂部
    page.evaluate("window.scrollTo(0, 0)")
    time.sleep(1.5)
    
    output_dir = r"C:\Users\BWM2\.gemini\antigravity-cli\brain\885bdca4-7dfa-479c-9264-38d23ecb1a84"
    screenshot_path = os.path.join(output_dir, "landing_page.png")
    
    print(f"Taking screenshot to {screenshot_path} ...")
    page.screenshot(path=screenshot_path, full_page=True)
    
    browser.close()
    print("Done!")
