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
        
    username = config.get("username")
    password = config.get("password")
    
    if not username or not password or username == "여기에_아이디를_입력하세요":
        print("Error: config.json 파일에 올바른 아이디와 비밀번호를 입력해주세요.")
        return

    print("Playwright를 시작합니다...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Dialog 핸들러 등록 (일반 Alert 대처용)
        def handle_dialog(dialog):
            print(f"★ 경고창(Alert) 발생: {dialog.message}")
            dialog.dismiss()
        page.on("dialog", handle_dialog)
        
        print("공실클럽 메인 페이지로 이동 중...")
        page.goto("https://www.gongsilclub.co.kr/")
        page.wait_for_load_state("networkidle")
        time.sleep(3)
        
        print("'웹브라우저에서 열기' 버튼을 클릭합니다.")
        btn_open_web = page.locator("text=웹브라우저에서 열기")
        if btn_open_web.count() > 0:
            btn_open_web.first.click()
        else:
            page.goto("https://www.gongsilclub.co.kr/group/login/")
            
        page.wait_for_load_state("networkidle")
        time.sleep(5)
        
        # 아이디 입력 필드 찾기 및 포커스 후 순차 입력
        print("아이디 입력 필드 탐색 및 입력...")
        username_field = page.locator("input[placeholder*='ID']").first
        if username_field.is_visible():
            username_field.focus()
            username_field.press_sequentially(username, delay=100)
            print("아이디 입력 완료")
            
        # 비밀번호 입력 필드 찾기 및 포커스 후 순차 입력
        print("비밀번호 입력 필드 탐색 및 입력...")
        password_field = page.locator("input[type='password']").first
        if password_field.is_visible():
            password_field.focus()
            password_field.press_sequentially(password, delay=100)
            print("비밀번호 입력 완료")
            
        time.sleep(2)
        page.screenshot(path="step4_input_filled.png")
        
        # 로그인 버튼 클릭 시도 (비밀번호창에서 Enter 입력)
        print("로그인 전송(Enter 키 입력) 시도 중...")
        password_field.press("Enter")
        
        print("로그인 요청 후 4초간 대기합니다...")
        time.sleep(4)
        
        page.screenshot(path="after_login_attempt.png")
        
        # 중복 로그인 모달 팝업 존재 여부 확인
        print("중복 로그인 팝업 확인 중...")
        overlay_text = page.locator("text=다른 PC에서 로그인 중입니다")
        if overlay_text.count() > 0 and overlay_text.first.is_visible():
            print("★ 중복 로그인 팝업이 감지되었습니다. '확인' 버튼을 누릅니다.")
            # get_by_text("확인")을 사용하여 CSS 셀렉터 파싱 에러를 완벽하게 방지
            confirm_btn = page.get_by_text("확인")
            clicked_confirm = False
            for i in range(confirm_btn.count()):
                btn = confirm_btn.nth(i)
                if btn.is_visible():
                    btn_text = btn.text_content()
                    print(f"확인 버튼 클릭 시도: {btn_text}")
                    btn.click()
                    clicked_confirm = True
                    break
            
            if not clicked_confirm:
                print("확인 버튼의 직접 클릭을 시도합니다.")
                page.click("text=확인")
            
            print("강제 로그아웃 및 재로그인 처리 대기 중 (5초)...")
            time.sleep(5)
            page.screenshot(path="after_modal_confirm.png")
        else:
            print("중복 로그인 팝업이 감지되지 않았습니다. 계속 진행합니다.")
            
        # 매물관리 페이지로 이동
        print("매물관리 페이지로 이동 중...")
        page.goto("https://www.gongsilclub.co.kr/group/management/")
        page.wait_for_load_state("networkidle")
        time.sleep(8)
        
        print(f"매물관리 이동 후 URL: {page.url}")
        
        # 최종 결과 저장
        html_content = page.content()
        with open("gongsil_management.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("매물관리 페이지 HTML 저장 완료 (gongsil_management.html)")
        
        page.screenshot(path="gongsil_screenshot.png", full_page=True)
        print("매물관리 페이지 스크린샷 저장 완료 (gongsil_screenshot.png)")
        
        browser.close()
        print("Playwright 작업을 완료했습니다.")

if __name__ == "__main__":
    main()
