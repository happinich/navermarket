import json
import time
import os
from playwright.sync_api import sync_playwright

def main():
    config_path = "config.json"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} 파일이 존재하지 않습니다.")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    aipartner_config = config.get("aipartner", {})
    username = aipartner_config.get("username")
    password = aipartner_config.get("password")
    
    if not username or not password or "여기에" in username:
        print("Error: config.json 파일에 올바른 AI파트너 아이디와 비밀번호를 입력해주세요.")
        return

    print("Playwright를 시작합니다...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Dialog 핸들러
        def handle_dialog(dialog):
            print(f"★ 경고창(Alert) 발생: {dialog.message}")
            dialog.dismiss()
        page.on("dialog", handle_dialog)
        
        print("AI파트너 로그인 페이지로 이동 중...")
        page.goto("https://www.aipartner.com/integrated/login")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        # 아이디 입력
        print("아이디 입력 중...")
        id_field = page.locator("#member-id").first
        if id_field.is_visible():
            id_field.focus()
            id_field.press_sequentially(username, delay=100)
            
        # 비밀번호 입력
        print("비밀번호 입력 중...")
        pw_field = page.locator("#member-pw").first
        if pw_field.is_visible():
            pw_field.focus()
            pw_field.press_sequentially(password, delay=100)
            
        time.sleep(2)
        page.screenshot(path="aipartner_step1_filled.png")
        
        # 로그인 버튼 클릭
        print("로그인 버튼 클릭 시도...")
        login_btn = page.locator("a.btn-login").first
        if login_btn.is_visible():
            login_btn.click()
        else:
            print("로그인 버튼을 직접 클릭하지 못해 Enter 키를 입력합니다.")
            pw_field.press("Enter")
            
        print("로그인 처리 대기 중 (8초)...")
        time.sleep(8)
        
        print(f"로그인 시도 후 URL: {page.url}")
        page.screenshot(path="aipartner_after_login.png", full_page=True)
        
        # HTML 저장
        html_content = page.content()
        with open("aipartner_after_login.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("로그인 후 페이지 HTML 저장 완료 (aipartner_after_login.html)")
        
        # 만약 로그인 상태가 성공했고 대시보드 화면에 도달했다면, 매물 메뉴를 탐색합니다.
        # 대시보드에서 매물관리(예: /estate 또는 매물 목록 버튼 등)가 있는지 파악하기 위해 로그 저장
        browser.close()
        print("Playwright 작업을 완료했습니다.")

if __name__ == "__main__":
    main()
