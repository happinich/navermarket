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
        page.wait_for_load_state("load")
        time.sleep(3)
        
        # 아이디/패스워드 입력
        id_field = page.locator("#member-id").first
        if id_field.is_visible():
            id_field.focus()
            id_field.press_sequentially(username, delay=100)
            
        pw_field = page.locator("#member-pw").first
        if pw_field.is_visible():
            pw_field.focus()
            pw_field.press_sequentially(password, delay=100)
            
        time.sleep(2)
        
        # 로그인 버튼 클릭
        login_btn = page.locator("a.btn-login").first
        if login_btn.is_visible():
            login_btn.click()
        else:
            pw_field.press("Enter")
            
        print("로그인 처리 대기 중...")
        try:
            page.wait_for_url(lambda url: "login" not in url, timeout=20000)
            print("로그인 완료")
        except Exception as e:
            print(f"URL 대기 에러: {e}")
            
        page.wait_for_load_state("load")
        time.sleep(5) 
        
        # 매물관리 페이지로 이동
        print("매물관리 페이지(offerings/ad_list)로 이동 중...")
        page.goto("https://www.aipartner.com/offerings/ad_list")
        page.wait_for_load_state("load")
        time.sleep(8)
        
        # 팝업 닫기
        popup_close_btn = page.get_by_text("닫기")
        for i in range(popup_close_btn.count()):
            btn = popup_close_btn.nth(i)
            if btn.is_visible():
                try:
                    btn.click()
                    time.sleep(1)
                except Exception:
                    pass
        
        # 첫 번째 '수정하기' 버튼 클릭
        # CSS 선택자: a.management.GTM_offerings_ad_list_listing_re (exposedModify)
        print("첫 번째 매물의 '수정하기' 버튼을 클릭합니다...")
        # id가 exposedModify이거나 수정하기 텍스트를 가진 첫 번째 visible 링크 클릭
        edit_btn = page.locator("a:has-text('수정하기'), #exposedModify").first
        if edit_btn.is_visible():
            print("수정하기 버튼을 클릭했습니다.")
            edit_btn.click()
        else:
            print("수정하기 버튼을 찾을 수 없습니다.")
            
        print("수정/등록 페이지 이동 대기 중 (10초)...")
        time.sleep(10)
        page.wait_for_load_state("load")
        
        print(f"상세 수정 페이지 URL: {page.url}")
        
        # HTML 저장
        detail_html = page.content()
        with open("aipartner_detail.html", "w", encoding="utf-8") as f:
            f.write(detail_html)
        print("매물 상세 페이지 HTML 저장 완료 (aipartner_detail.html)")
        
        # 스크린샷 저장
        page.screenshot(path="aipartner_detail.png", full_page=True)
        print("매물 상세 페이지 스크린샷 저장 완료 (aipartner_detail.png)")
        
        browser.close()
        print("상세 조회 작업을 완료했습니다.")

if __name__ == "__main__":
    main()
