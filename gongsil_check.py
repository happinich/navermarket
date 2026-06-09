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
        
    gongsil_config = config.get("gongsilclub", {})
    username = gongsil_config.get("username")
    password = gongsil_config.get("password")
    
    if not username or not password or "여기에" in username:
        print("Error: config.json 파일에 올바른 공실클럽 아이디와 비밀번호를 입력해주세요.")
        return

    print("Playwright를 시작합니다...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Dialog
        def handle_dialog(dialog):
            print(f"★ Dialog: {dialog.message}")
            dialog.dismiss()
        page.on("dialog", handle_dialog)
        
        print("공실클럽 메인 페이지로 이동 중...")
        page.goto("https://www.gongsilclub.co.kr/")
        page.wait_for_load_state("load")
        time.sleep(3)
        
        print("'웹브라우저에서 열기' 버튼을 클릭합니다.")
        btn_open_web = page.locator("text=웹브라우저에서 열기")
        if btn_open_web.count() > 0:
            btn_open_web.first.click()
        else:
            page.goto("https://www.gongsilclub.co.kr/group/login/")
            
        page.wait_for_load_state("load")
        time.sleep(5)
        
        # 로그인
        username_field = page.locator("input[placeholder*='ID']").first
        if username_field.is_visible():
            username_field.focus()
            username_field.press_sequentially(username, delay=100)
            
        password_field = page.locator("input[type='password']").first
        if password_field.is_visible():
            password_field.focus()
            password_field.press_sequentially(password, delay=100)
            
        time.sleep(2)
        password_field.press("Enter")
        time.sleep(4)
        
        # 중복 로그인 처리
        overlay_text = page.locator("text=다른 PC에서 로그인 중입니다")
        if overlay_text.count() > 0 and overlay_text.first.is_visible():
            confirm_btn = page.get_by_text("확인", exact=True)
            for i in range(confirm_btn.count()):
                btn = confirm_btn.nth(i)
                if btn.is_visible():
                    btn.click()
                    break
            time.sleep(5)
            
        # 매물관리 페이지 이동 (등록 매물 확인)
        print("매물관리 등록 매물 확인 중...")
        page.goto("https://www.gongsilclub.co.kr/group/management/")
        page.wait_for_load_state("load")
        time.sleep(6)
        
        page.screenshot(path="gongsil_status.png", full_page=True)
        with open("gongsil_status.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("등록 매물 덤프 완료 (gongsil_status.html / png)")
        
        # 종료 탭 이동
        print("종료·취소·실패 탭 확인 중...")
        tab_btn = page.locator("text=종료·취소·실패").first
        if tab_btn.is_visible():
            tab_btn.evaluate("el => el.click()") # 안전하게 JS 강제 클릭
            time.sleep(6)
            
            page.screenshot(path="gongsil_status_stopped.png", full_page=True)
            with open("gongsil_status_stopped.html", "w", encoding="utf-8") as f:
                f.write(page.content())
            print("종료 매물 덤프 완료 (gongsil_status_stopped.html / png)")
        else:
            print("종료 탭 버튼을 찾을 수 없습니다.")
            
        browser.close()
        print("진단 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
