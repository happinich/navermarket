import json
import time
import os
import re
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
    phone = gongsil_config.get("phone")
    
    if not username or not password or "여기에" in username:
        print("Error: config.json 파일에 올바른 공실클럽 아이디와 비밀번호를 입력해주세요.")
        return

    if not phone or "XXXX" in phone:
        print("Error: config.json 파일의 gongsilclub 아래 'phone' 항목에 실제 사용하는 휴대폰 번호를 채워 넣어주세요.")
        return

    print("Playwright를 시작합니다...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Dialog(Confirm) 자동 승인 핸들러 등록
        def handle_dialog(dialog):
            print(f"★ 컨펌창/경고창(Dialog) 감지: {dialog.message}")
            dialog.accept()
            print("Dialog 승인 완료(확인 클릭)")
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
        
        # 로그인 입력
        print("아이디 입력...")
        username_field = page.locator("input[placeholder*='ID']").first
        if username_field.is_visible():
            username_field.focus()
            username_field.press_sequentially(username, delay=100)
            
        print("비밀번호 입력...")
        password_field = page.locator("input[type='password']").first
        if password_field.is_visible():
            password_field.focus()
            password_field.press_sequentially(password, delay=100)
            
        time.sleep(2)
        
        # 로그인 전송 (Enter)
        password_field.press("Enter")
        print("로그인 처리 대기 중...")
        time.sleep(4)
        
        # 중복 로그인 모달 팝업 존재 시 확인 버튼 클릭
        overlay_text = page.locator("text=다른 PC에서 로그인 중입니다")
        if overlay_text.count() > 0 and overlay_text.first.is_visible():
            print("★ 중복 로그인 팝업 감지, '확인' 버튼을 누릅니다.")
            confirm_btn = page.get_by_text("확인", exact=True)
            clicked_confirm = False
            for i in range(confirm_btn.count()):
                btn = confirm_btn.nth(i)
                if btn.is_visible():
                    print(f"확인 버튼 클릭: {btn.text_content()}")
                    btn.click()
                    clicked_confirm = True
                    break
            if not clicked_confirm:
                page.click("text=확인")
            time.sleep(5)
            
        # 매물관리 페이지로 이동
        print("매물관리 페이지로 이동 중...")
        page.goto("https://www.gongsilclub.co.kr/group/management/")
        page.wait_for_load_state("load")
        time.sleep(5)
        
        # 잘못 종료된 삼성동 퍼시픽 805호 매물 복구(재등록)를 위한 탐색
        target_seq = "13062" # 복구할 공실번호
        print(f"공실번호 {target_seq} 매물 카드 탐색 중...")
        
        # 특정 공실번호를 가진 개별 매물 카드 컨테이너를 정확히 타겟팅
        card_locator = page.locator(f"div.border-gray50:has-text('{target_seq}')").first
        
        if card_locator.is_visible():
            print("매물 카드를 찾았습니다. 광고종료 버튼을 클릭합니다...")
            close_btn = card_locator.locator("text=광고종료").first
            if close_btn.is_visible():
                print("광고종료 버튼을 클릭합니다.")
                close_btn.click()
                print("광고종료 버튼 클릭 완료. 옵션 선택 팝업 로딩을 기다립니다...")
                time.sleep(4)
                
                # 광고종료 클릭 직후 화면 캡처 저장
                page.screenshot(path="after_stop_click.png")
                
                # 팝업 내 '노출종료' 라디오 옵션 클릭
                print("팝업 옵션 중 '노출종료'를 선택합니다...")
                option_btn = page.get_by_text("노출종료")
                if option_btn.count() > 0:
                    option_btn.first.click()
                    print("'노출종료' 옵션 라디오 선택 완료.")
                    time.sleep(2)
                else:
                    print("'노출종료' 옵션 버튼을 찾을 수 없습니다.")
                
                # 옵션 선택 후 화면 캡처 저장
                page.screenshot(path="after_option_select.png")
                print("옵션 선택 후 스크린샷 저장 완료 (after_option_select.png)")
                    
                # 활성화된 '확인' 버튼 클릭 (exact=True로 구홍보확인서 등 엉뚱한 요소 간섭 배제)
                confirm_btn = page.get_by_text("확인", exact=True)
                clicked_modal_ok = False
                for i in range(confirm_btn.count()):
                    btn = confirm_btn.nth(i)
                    if btn.is_visible():
                        print(f"모달 팝업의 '확인' 버튼을 클릭합니다: {btn.text_content()}")
                        btn.click()
                        clicked_modal_ok = True
                        time.sleep(2)
                        break
                        
                if not clicked_modal_ok:
                    print("모달 확인 버튼을 찾을 수 없어 직접 텍스트 기반 클릭을 시도합니다.")
                    page.click("text=확인")
                    time.sleep(2)

                # 확인 클릭 직후 캡처 및 대기
                page.screenshot(path="after_confirm_click.png")
                print("확인 클릭 후 스크린샷 저장 완료 (after_confirm_click.png)")
                time.sleep(2)

                # 2차 컨펌 팝업 "종료" 버튼 처리
                print("2차 컨펌 팝업의 '종료' 버튼을 찾습니다...")
                confirm_sub_btn = page.get_by_text("종료", exact=True)
                clicked_confirm_sub = False
                for i in range(confirm_sub_btn.count()):
                    btn = confirm_sub_btn.nth(i)
                    if btn.is_visible():
                        print(f"2차 팝업의 '종료' 버튼을 클릭합니다: {btn.text_content()}")
                        btn.click()
                        clicked_confirm_sub = True
                        break
                
                if not clicked_confirm_sub:
                    # nth()로 안 찾아지면 직접 클릭 시도
                    print("일반 텍스트 기반으로 '종료' 버튼 클릭 시도...")
                    page.click("text=종료")
                
                time.sleep(3)
                page.screenshot(path="after_final_stop_confirm.png")
                print("최종 종료 승인 후 스크린샷 저장 완료 (after_final_stop_confirm.png)")

                # 모달 팝업 또는 로딩 오버레이가 사라질 때까지 안전하게 대기
                print("모달 팝업 및 오버레이가 사라지기를 대기합니다...")
                try:
                    # 2차 팝업 사라짐 대기
                    page.wait_for_selector("text=광고를 종료하시겠습니까?", state="hidden", timeout=10000)
                    # 1차 광고 종료 옵션 선택 모달이 화면에서 사라질 때까지 대기
                    page.wait_for_selector("text=광고 종료 옵션 선택", state="hidden", timeout=10000)
                    print("모달 팝업들이 사라졌습니다.")
                except Exception as e:
                    print(f"모달 팝업 닫힘 대기 타임아웃/오류: {e}")

                try:
                    # 회색 로딩 백드롭 오버레이가 사라질 때까지 대기
                    page.wait_for_selector(".background-gray100-t50", state="detached", timeout=5000)
                    print("로딩 백드롭 오버레이가 사라졌습니다.")
                except Exception as e:
                    print(f"오버레이 분리 대기 타임아웃/오류: {e}")
                
                time.sleep(3)
            else:
                print("광고종료 버튼을 찾을 수 없습니다. (이미 종료되었을 수 있습니다)")
        else:
            print(f"공실번호 {target_seq} 매물 카드가 보이지 않습니다. (이미 광고 종료 상태)")
            
        # 2단계: '종료·취소·실패' 탭으로 이동
        print("'종료·취소·실패' 탭으로 이동합니다...")
        tab_btn = page.locator("text=종료·취소·실패").first
        if tab_btn.is_visible():
            try:
                tab_btn.click(timeout=10000)
            except Exception as e:
                print(f"일반 클릭 실패로 JS 강제 클릭을 시도합니다. 에러: {e}")
                tab_btn.evaluate("el => el.click()")
                
            print("탭 이동 완료. 로딩 대기 (5초)...")
            time.sleep(5)
            page.wait_for_load_state("load")
        else:
            print("종료·취소·실패 탭 버튼을 찾을 수 없습니다.")
            
        # 이동된 탭 화면 저장
        print("종료 탭 화면 저장 중...")
        page.screenshot(path="gongsil_stopped_tab.png", full_page=True)
        with open("gongsil_stopped_tab.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        print("종료 탭 HTML 및 스크린샷 저장 완료 (gongsil_stopped_tab.html / png)")
        
        # 3단계: 종료 탭에서 11583 매물 카드를 찾고 '복사' 버튼 클릭해 재등록 시도
        print(f"종료 탭에서 공실번호 {target_seq} 매물 카드를 탐색합니다...")
        stopped_card = page.locator(f"div.border-gray50:has-text('{target_seq}')").first
        
        if stopped_card.is_visible():
            print("종료된 매물 카드를 찾았습니다. '복사' 버튼을 클릭합니다...")
            copy_btn = stopped_card.locator("text=복사").first
            if copy_btn.is_visible():
                copy_btn.click()
                print("'복사' 버튼을 클릭했습니다. 처리 대기 및 결과 캡처 준비 (5초)...")
                time.sleep(5)
                page.wait_for_load_state("load")
                
                # 복사 처리 후 최종 화면 캡처 및 저장
                page.screenshot(path="after_copy_click.png")
                with open("after_copy_click.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("복사 버튼 클릭 후 덤프 완료 (after_copy_click.html / png)")
                
                # 4단계: 복사된 등록 폼에서 '등록하기' 버튼 클릭해 재등록 완결
                print("'등록하기' 버튼이 나타나기를 기다립니다...")
                btn_register = page.get_by_text("등록하기", exact=True).first
                if btn_register.is_visible():
                    # 필수 항목인 휴대폰 번호(realtor.cphone) 입력란 확인 및 기입
                    phone_input = page.locator("input[name='realtor.cphone']").first
                    if phone_input.is_visible():
                        current_val = phone_input.input_value()
                        if not current_val or current_val.strip() == "":
                            print(f"휴대폰 번호 입력칸이 비어 있습니다. 설정 파일의 연락처({phone})를 입력합니다...")
                            phone_input.fill(phone)
                            time.sleep(1)
                    
                    print("등록하기 버튼이 보입니다. 클릭합니다...")
                    try:
                        btn_register.click(timeout=5000)
                    except Exception as e:
                        print(f"일반 클릭 실패로 JS 강제 클릭을 시도합니다. 에러: {e}")
                        btn_register.evaluate("el => el.click()")
                    print("등록하기 클릭 완료. 처리 대기 (6초)...")
                    time.sleep(6)
                    page.wait_for_load_state("load")
                    
                    # 최종 완료 후 화면 저장
                    page.screenshot(path="after_registration_complete.png")
                    with open("after_registration_complete.html", "w", encoding="utf-8") as f:
                        f.write(page.content())
                    print("최종 등록 완료 화면 덤프 완료 (after_registration_complete.html / png)")
                else:
                    print("'등록하기' 버튼을 찾을 수 없습니다. (데이터 부족 등 입력 폼에 에러가 났을 수 있음)")
            else:
                print("'복사' 버튼을 찾을 수 없습니다.")
        else:
            print(f"종료 탭에서 공실번호 {target_seq} 매물 카드를 찾을 수 없습니다. (종료 처리가 덜 반영되었거나 검색 범위 오류일 수 있음)")
            
        browser.close()
        print("광고종료 및 종료 탭 복사등록 시도 작업을 성공적으로 마쳤습니다.")

if __name__ == "__main__":
    main()
