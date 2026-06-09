import json
import time
import os
import re
import sys
import io
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# 터미널 출력 인코딩을 UTF-8로 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', write_through=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', write_through=True)

def main():
    log_file = open("task_run.log", "w", encoding="utf-8", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file
    
    config_path = r"c:\Users\happinich\Documents\9.vibecoding\navermarket\config.json"
    if not os.path.exists(config_path):
        print(f"Error: {config_path} 파일이 존재하지 않습니다.")
        return
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    gongsil_config = config.get("gongsilclub", {})
    username = gongsil_config.get("username")
    password = gongsil_config.get("password")
    
    # 공통 JS 마우스 이벤트 디스패처 정의
    js_trigger = """
    el => {
        if (!el) return;
        el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
        el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
        el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
    }
    """
    
    print("Playwright를 시작합니다...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        # Dialog 자동 승인 및 로깅
        page.on("dialog", lambda dialog: (print(f"★ 브라우저 경고창 발생: {dialog.message}"), dialog.accept()))
        
        # 로그인
        page.goto("https://www.gongsilclub.co.kr/")
        time.sleep(2)
        btn_open_web = page.locator("text=웹브라우저에서 열기")
        if btn_open_web.count() > 0:
            btn_open_web.first.click()
        else:
            page.goto("https://www.gongsilclub.co.kr/group/login/")
        time.sleep(4)
        
        page.locator("input[placeholder*='ID']").first.press_sequentially(username, delay=100)
        password_field = page.locator("input[type='password']").first
        password_field.press_sequentially(password, delay=100)
        time.sleep(1)
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
            time.sleep(4)
            
        # 1단계: 종료 탭에서 기존 13062 매물 상세/검증정보 수집
        print("매물관리 페이지로 이동...")
        page.goto("https://www.gongsilclub.co.kr/group/management/")
        page.wait_for_load_state("load")
        time.sleep(4)
        
        print("종료 탭으로 이동합니다...")
        tab_btn = page.locator("text=종료·취소·실패").first
        if tab_btn.is_visible():
            tab_btn.evaluate("el => el.click()")
            time.sleep(5)
            
            target_seq = "13062"
            print(f"종료 탭에서 공실번호 {target_seq} 매물 카드 클릭...")
            stopped_card = page.locator(f"div.border-gray50:has-text('{target_seq}')").first
            if stopped_card.is_visible():
                stopped_card.click()
                time.sleep(4)
                
                # HTML 덤프 및 스크린샷 저장
                print("13062 상세 정보 덤프 저장 중...")
                page.screenshot(path="stopped_13062_detail.png")
                with open("stopped_13062_detail.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("stopped_13062_detail.html / png 저장 완료.")
                
                # HTML 파싱하여 기존 검증 정보 수집
                html_content = page.content()
                soup = BeautifulSoup(html_content, "html.parser")
                
                owner_name = ""
                carrier = ""
                phone = ""
                verify_method = "모바일확인2" # 기본값
                
                # 검증방식
                card_div = None
                for div in soup.find_all("div", class_=lambda c: c and "border-gray50" in c):
                    if target_seq in div.text:
                        card_div = div
                        break
                if card_div:
                    method_span = card_div.find(string=lambda s: s and ("모바일확인" in s or "홍보확인서" in s or "현장확인" in s))
                    if method_span:
                        verify_method = method_span.strip()
                
                # 소유자명
                owner_label = soup.find(string=lambda s: s and "등기부상의 소유자명" in s)
                if owner_label:
                    label_cell = None
                    curr = owner_label.parent
                    for _ in range(5):
                        if curr and curr.name == "div" and curr.get("class") and any("background" in cls for cls in curr.get("class")):
                            label_cell = curr
                            break
                        curr = curr.parent
                    if label_cell:
                        data_cell = label_cell.find_next_sibling()
                        if data_cell:
                            owner_name = data_cell.text.replace("*", "").strip()
                            
                # 휴대폰/통신사
                phone_span = soup.find(string=lambda s: s and re.match(r"^010-\d{3,4}-\d{4}$", s.strip()))
                if phone_span:
                    phone = phone_span.strip()
                    parent_div = phone_span.parent.parent
                    spans = parent_div.find_all("span")
                    for sp in spans:
                        txt = sp.text.strip()
                        if txt in ["SKT", "KT", "LGU+", "SKT알뜰폰", "KT알뜰폰", "LGU+알뜰폰"]:
                            carrier = txt
                            break
                            
                print(f"★ 수집된 검증정보: 방식={verify_method}, 소유자={owner_name}, 통신사={carrier}, 연락처={phone}")
            else:
                print("종료 탭에서 기존 매물을 찾지 못했습니다.")
                return
        else:
            print("종료 탭 버튼을 찾지 못했습니다.")
            return

        # 2단계: 완전히 리프레시하여 새 세션처럼 광고전송 개시
        print("페이지를 완전히 새로고침하여 등록 매물 탭 초기 상태로 이동합니다...")
        page.goto("https://www.gongsilclub.co.kr/group/management/")
        page.wait_for_load_state("load")
        time.sleep(5)
        
        # 신규 매물 카드의 '광고전송' 클릭
        active_card = page.locator("div.border-gray50:has-text('퍼시픽'):has-text('805호')").first
        if active_card.is_visible():
            print("신규 매물 카드를 찾았습니다. '광고전송' 버튼을 클릭합니다...")
            ad_btn = active_card.locator("text=광고전송").first
            if ad_btn.is_visible():
                ad_btn.click()
                print("광고전송 클릭 완료. 모달 대기...")
                time.sleep(3)
                
                # '광고하기' 버튼 클릭
                print("모달에서 '광고하기' 버튼을 클릭합니다...")
                ad_submit_btn = page.get_by_text("광고하기", exact=True)
                if ad_submit_btn.count() > 0:
                    ad_submit_btn.first.click()
                    print("'광고하기' 버튼 클릭 완료. 다음 폼 로딩 대기 (10초)...")
                    time.sleep(5)
                    page.wait_for_load_state("load")
                    
                    # 검증방식 선택 텍스트가 완전히 뜰 때까지 대기
                    page.wait_for_selector("text=검증방식 선택", state="visible", timeout=15000)
                    
                    # 로딩 마스크가 완전히 사라질 때까지 대기 (가로채기 방지)
                    print("로딩 오버레이 소멸 대기 중...")
                    try:
                        page.wait_for_selector(".absolute-div.background-gray0", state="detached", timeout=5000)
                        print("로딩 오버레이가 사라졌습니다.")
                    except:
                        print("로딩 오버레이 대기 생략 (이미 없거나 다른 클래스)")
                    
                    time.sleep(4)
                    page.screenshot(path="research_ad_verify_form.png")
                    print("검증방식 선택 화면 진입 완료. 스크린샷 저장 (research_ad_verify_form.png)")
                    
                    # 3단계: 수집한 검증방식(예: 모바일확인2)을 클릭
                    print(f"수집한 검증방식 '{verify_method}' 라디오 카드를 클릭합니다...")
                    xpath_sel = f"xpath=//form//div[contains(@class, 'border-gray50') and contains(., '{verify_method}')]"
                    mobile_card = page.locator(xpath_sel).first
                    
                    if mobile_card.count() > 0:
                        print("★ 매칭된 카드 텍스트:", mobile_card.inner_text().replace('\n', ' '))
                        try:
                            print("JS 강제 클릭 시도...")
                            mobile_card.evaluate("el => el.click()")
                            print("JS 강제 클릭 성공")
                        except Exception as e:
                            print(f"JS 클릭 실패: {e}. 일반 클릭 시도...")
                            mobile_card.click(force=True)
                            
                        print(f"'{verify_method}' 클릭 처리 완료. 동적 입력 폼 로딩 대기 (8초)...")
                        time.sleep(8)
                        page.wait_for_load_state("load")
                        
                        # 4단계: 검증방식별 폼 기입 및 파일 업로드
                        if "모바일확인" in verify_method:
                            print("모바일확인2 검증 입력 진행...")
                            # 소유자명 입력
                            print(f"소유자명 입력란에 '{owner_name}' 기입...")
                            name_input = page.locator("input[name='verification.oname']").first
                            name_input.fill(owner_name)
                            name_input.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                            name_input.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")
                            
                            print("성별 '여' 라디오 버튼 클릭...")
                            page.locator("label").filter(has_text=re.compile(r"^여$")).first.click(force=True)
                            time.sleep(1)
                            
                            # 휴대폰 번호 입력
                            phone_parts = phone.split("-")
                            if len(phone_parts) == 3:
                                mid_num = phone_parts[1]
                                tail_num = phone_parts[2]
                                print(f"휴대폰 번호 입력: 가운데={mid_num}, 끝={tail_num}...")
                                mid_input = page.locator("input[name='dummyOphoneMiddle']").first
                                mid_input.fill(mid_num)
                                mid_input.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                                mid_input.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")
                                
                                tail_input = page.locator("input[name='dummyOphoneTail']").first
                                tail_input.fill(tail_num)
                                tail_input.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                                tail_input.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")
                            else:
                                print("Error: 휴대폰 번호 형식이 잘못되었습니다:", phone)
                                
                            # 통신사 선택 dropdown 클릭
                            print("통신사 선택 Dropdown 다각적 클릭 시도...")
                            carrier_dropdown = page.locator("xpath=//div[text()='통신사 선택' or text()='통신사']/ancestor::div[contains(@class, 'position-div') and contains(@style, 'cursor: pointer')][1]").first
                            
                            try:
                                carrier_dropdown.evaluate(js_trigger)
                                print("Dropdown JS 이벤트 디스패치 성공")
                            except Exception as e:
                                print(f"Dropdown JS 디스패치 실패: {e}")
                            
                            try:
                                carrier_dropdown.click(force=True)
                                print("Dropdown click(force=True) 성공")
                            except Exception as e:
                                print(f"Dropdown click 실패: {e}")
                                
                            try:
                                svg_btn = carrier_dropdown.locator("svg").first
                                if svg_btn.count() > 0:
                                    svg_btn.click(force=True)
                                    print("Dropdown svg 클릭 성공")
                            except Exception as e:
                                print(f"Dropdown svg 클릭 실패: {e}")
                                
                            try:
                                carrier_dropdown.dblclick(force=True)
                                print("Dropdown dblclick 성공")
                            except Exception as e:
                                print(f"Dropdown dblclick 실패: {e}")
                                
                            try:
                                carrier_dropdown.focus()
                                page.keyboard.press("Space")
                                page.keyboard.press("ArrowDown")
                                print("Dropdown keyboard(Space, ArrowDown) 입력 성공")
                            except Exception as e:
                                print(f"Dropdown keyboard 입력 실패: {e}")
                                
                            time.sleep(3)
                            page.screenshot(path="research_carrier_dropdown_clicked.png")
                            print("드롭다운 클릭 시도 후 상태 스크린샷 저장 완료 (research_carrier_dropdown_clicked.png)")
                            
                            print("통신사 목록 'KT' 대기 및 클릭 시도...")
                            try:
                                all_divs = page.locator("div").all()
                                carriers_found = []
                                for d in all_divs:
                                    try:
                                        txt = d.inner_text().strip()
                                        if txt in ["SKT", "KT", "LGU+", "알뜰폰", "SKT알뜰폰", "KT알뜰폰", "LGU+알뜰폰"]:
                                            if txt not in carriers_found:
                                                carriers_found.append(txt)
                                    except:
                                        pass
                                print("★ 현재 화면에서 감지된 통신사 목록 텍스트:", carriers_found)

                                kt_selectors = [
                                    "xpath=//div[text()='KT']",
                                    "xpath=//span[text()='KT']",
                                    "xpath=//*[text()='KT']",
                                    "text=KT"
                                ]
                                
                                kt_clicked = False
                                for sel in kt_selectors:
                                    locator = page.locator(sel)
                                    if locator.count() > 0:
                                        for i in range(locator.count()):
                                            opt = locator.nth(i)
                                            if opt.is_visible():
                                                print(f"매칭된 KT 셀렉터 발견: {sel} (index {i}), 클릭 진행...")
                                                try:
                                                    opt.click(force=True)
                                                    print("KT click(force=True) 호출 성공")
                                                    kt_clicked = True
                                                    break
                                                except Exception as click_err:
                                                    print(f"KT click 실패, JS 디스패치 시도: {click_err}")
                                                    try:
                                                        opt.evaluate(js_trigger)
                                                        print("KT JS 디스패치 성공")
                                                        kt_clicked = True
                                                        break
                                                    except Exception as eval_err:
                                                        print(f"KT JS 디스패치 실패: {eval_err}")
                                        if kt_clicked:
                                            break
                                    if kt_clicked:
                                        break
                                
                                if not kt_clicked:
                                    page.wait_for_selector("text=KT", state="visible", timeout=3000)
                                    kt_option = page.locator("text=KT").last
                                    kt_box = kt_option.bounding_box()
                                    if kt_box:
                                        kx = kt_box["x"] + kt_box["width"] / 2
                                        ky = kt_box["y"] + kt_box["height"] / 2
                                        page.mouse.click(kx, ky)
                                        print(f"KT 백업 좌표 클릭 성공: x={kx}, y={ky}")
                                        kt_clicked = True
                                    else:
                                        kt_option.evaluate(js_trigger)
                                        print("KT 백업 JS 디스패치 성공")
                                        kt_clicked = True
                                        
                            except Exception as e:
                                print(f"KT 대기/클릭 중 오류 발생: {e}")
                            time.sleep(2)
                            
                        elif "홍보확인" in verify_method:
                            print("구홍보확인서 검증 기입을 시작합니다...")
                            # 1. 소유자명 입력
                            print(f"소유자명 입력란에 '{owner_name}' 기입...")
                            name_input = page.locator("input[name='verification.oname']").first
                            name_input.fill(owner_name)
                            name_input.evaluate("el => el.dispatchEvent(new Event('input', { bubbles: true }))")
                            name_input.evaluate("el => el.dispatchEvent(new Event('change', { bubbles: true }))")

                            # 2. 소유자 구분 '개인' 라디오 버튼 클릭
                            print("소유자 구분 '개인' 클릭...")
                            page.locator("label").filter(has_text=re.compile(r"^개인$")).first.click(force=True)
                            time.sleep(1)

                            # 3. 의뢰인과 소유자와의 관계 드롭다운 클릭 후 '본인' 선택
                            print("의뢰인과 소유자와의 관계 드롭다운 클릭...")
                            relation_dropdown = page.locator("xpath=//div[contains(text(), '의뢰인과 소유자와의 관계')]/following-sibling::div[1]//div[contains(text(), '선택')]").first
                            try:
                                relation_dropdown.click(force=True)
                                print("Dropdown Click(force=True) 성공")
                            except Exception as click_err:
                                print(f"Dropdown Click 실패: {click_err}")
                            time.sleep(2)
                            
                            # 혹시 옵션이 안 보인다면 JS로 강제 트리거
                            try:
                                if page.locator("text=본인").count() == 0:
                                    print("본인 옵션이 안 보여 JS 트리거 실행...")
                                    relation_dropdown.evaluate(js_trigger)
                                    time.sleep(2)
                            except:
                                pass
                            
                            print("관계 '본인' 옵션 대기 및 클릭...")
                            page.locator("text=본인").last.click(force=True)
                            time.sleep(1)

                            # 4. 홍보확인서 전송방식 '온라인 전송' 클릭
                            print("홍보확인서 전송방식 '온라인 전송' 클릭...")
                            page.locator("label").filter(has_text=re.compile(r"^온라인 전송$")).first.click(force=True)
                            time.sleep(2)

                            # 화면 덤프 저장
                            print("홍보확인서 작성 클릭 전 폼 덤프 저장...")
                            page.screenshot(path="verify_form_filled.png")
                            with open("verify_form_filled.html", "w", encoding="utf-8") as f:
                                f.write(page.content())

                            # 5. "홍보확인서 작성" 버튼 클릭
                            print("'홍보확인서 작성' 버튼 클릭...")
                            page.locator("div.button:has-text('홍보확인서 작성')").first.click(force=True)
                            time.sleep(4)

                            # 팝업 상태 덤프 저장
                            print("홍보확인서 작성 팝업 덤프 저장...")
                            page.screenshot(path="popup_active.png")
                            with open("popup_active.html", "w", encoding="utf-8") as f:
                                f.write(page.content())

                            # 캔버스에 서명 그리기 시도 (이성구 세 글자 궤적 그리기)
                            print("캔버스 서명 그리기 시도 (이성구 3글자 획 시뮬레이션)...")
                            # 자바스크립트로 직접 PointerEvent 디스패치하여 캔버스 드로잉 수행
                            print("JS PointerEvent 기반 캔버스 드로잉 시도...")
                            try:
                                js_draw_code = """
                                () => {
                                    const canvas = document.querySelectorAll('canvas');
                                    if (canvas.length < 2) return "canvas_not_found";
                                    const c = canvas[canvas.length - 1]; // z-index: 1 캔버스
                                    
                                    // 1. 2D 컨텍스트에 진짜 십자선 그리기
                                    const ctx = c.getContext('2d');
                                    if (!ctx) return "context_not_found";
                                    
                                    ctx.lineWidth = 6;
                                    ctx.strokeStyle = '#000000';
                                    ctx.lineCap = 'round';
                                    
                                    // 가로선
                                    ctx.beginPath();
                                    ctx.moveTo(c.width * 0.2, c.height * 0.5);
                                    ctx.lineTo(c.width * 0.8, c.height * 0.5);
                                    ctx.stroke();
                                    
                                    // 세로선
                                    ctx.beginPath();
                                    ctx.moveTo(c.width * 0.5, c.height * 0.2);
                                    ctx.lineTo(c.width * 0.5, c.height * 0.8);
                                    ctx.stroke();
                                    
                                    // 2. pointerdown/move/up 이벤트를 통해 라이브러리에 좌표 등록 유도
                                    const rect = c.getBoundingClientRect();
                                    function dispatch(type, x_ratio, y_ratio) {
                                        const x = rect.left + rect.width * x_ratio;
                                        const y = rect.top + rect.height * y_ratio;
                                        const ev = new PointerEvent(type, {
                                            clientX: x,
                                            clientY: y,
                                            pointerId: 1,
                                            isPrimary: true,
                                            bubbles: true,
                                            cancelable: true,
                                            pointerType: 'mouse',
                                            pressure: 0.5
                                        });
                                        c.dispatchEvent(ev);
                                    }
                                    
                                    dispatch('pointerdown', 0.2, 0.5);
                                    dispatch('pointermove', 0.8, 0.5);
                                    dispatch('pointerup', 0.8, 0.5);
                                    
                                    dispatch('pointerdown', 0.5, 0.2);
                                    dispatch('pointermove', 0.5, 0.8);
                                    dispatch('pointerup', 0.5, 0.8);
                                    
                                    // 3. 변경 감지 이벤트 디스패치
                                    c.dispatchEvent(new Event('input', { bubbles: true }));
                                    c.dispatchEvent(new Event('change', { bubbles: true }));
                                    
                                    return "hybrid_drawing_completed";
                                }
                                """
                                draw_res = page.evaluate(js_draw_code)
                                print(f"JS 드로잉 디스패치 결과: {draw_res}")
                            except Exception as draw_err:
                                print(f"JS 드로잉 중 오류 발생: {draw_err}")

                            # '확인' 버튼 클릭
                            print("'확인' 버튼 클릭...")
                            confirm_btn = page.locator("div.button:has-text('확인')").first
                            try:
                                confirm_btn.click(force=True)
                                print("일반 클릭 완료")
                            except Exception as c_err:
                                print(f"일반 클릭 실패: {c_err}")
                                
                            try:
                                confirm_btn.evaluate(js_trigger)
                                print("JS 트리거 클릭 완료")
                            except Exception as js_err:
                                print(f"JS 트리거 클릭 실패: {js_err}")
                                
                            print("확인 버튼 클릭 완료. 2단계 대기 (8초)...")
                            time.sleep(8)

                            # 2단계 팝업 상태 덤프 저장
                            print("2단계 팝업 덤프 저장 중...")
                            page.screenshot(path="popup_step2.png")
                            with open("popup_step2.html", "w", encoding="utf-8") as f:
                                f.write(page.content())

                            # 분석을 위해 여기서 중단
                            print("★ 임시 중단: 구홍보확인서 작성 팝업 2단계 분석을 위해 종료합니다.")
                            browser.close()
                            return

                        # 결제 페이지 활성화 조치
                        print("결제 수단 'Gpay 사용' 명시적 클릭...")
                        try:
                            gpay_radio = page.locator("text=Gpay 사용").first
                            gpay_radio.click(force=True)
                            print("Gpay 사용 라디오 버튼 클릭 성공")
                        except Exception as e:
                            print(f"Gpay 사용 클릭 실패: {e}")
                            
                        print("Gpay 잔액 '새로고침' 클릭...")
                        try:
                            refresh_btn = page.get_by_text("새로고침", exact=True).first
                            if refresh_btn.count() > 0:
                                refresh_btn.click(force=True)
                                print("잔액 새로고침 클릭 성공")
                        except Exception as e:
                            print(f"잔액 새로고침 클릭 실패: {e}")
                            
                        time.sleep(1)
                             
                        # 개인정보 동의 클릭 (약관 동의 팝업 열기)
                        print("개인정보 수집 및 이용 동의 클릭 (팝업 열기)...")
                        agree_btn = page.locator("text=(필수)개인정보").first
                        agree_btn.click(force=True)
                        time.sleep(2)
                        
                        # 약관 팝업 속 '동의합니다' 클릭 (자동 팝업 닫힘 및 결제 화면 이동)
                        print("약관 팝업창 내부의 '동의합니다' 부모 div 클릭...")
                        popup_agree_div = page.locator("xpath=//div[contains(@class, 'border-blue50') and .//span[contains(text(), '동의합니다')]]").first
                        popup_agree_div.click(force=True)
                        time.sleep(4) # 결제 화면 렌더링 대기
                        
                        # 결제 전 상태 스크린샷 저장
                        page.screenshot(path="before_payment.png")
                        print("결제 전 상태 스크린샷 저장 완료 (before_payment.png)")
                        
                        # 결제 버튼 강제 활성화 조치 (클래스에서 disabled 제거)
                        print("결제 버튼 disabled 클래스 강제 제거 시도...")
                        try:
                            page.evaluate("() => { const btn = document.querySelector('div.button.disabled'); if (btn) { btn.classList.remove('disabled'); console.log('disabled 클래스 제거됨'); } }")
                        except Exception as e:
                            print(f"disabled 클래스 제거 중 예외: {e}")
                            
                        # '1,900원 결제' 버튼 클릭
                        print("최종 '1,900원 결제' 버튼 클릭 시도...")
                        pay_btn = page.locator("xpath=//div[contains(@class, 'button') and ( .//div[contains(text(), '결제')] or contains(text(), '결제') )]").first
                        try:
                            pay_btn.click(force=True)
                            print("결제 버튼 click(force=True) 완료")
                        except Exception as click_err:
                            print(f"결제 버튼 click 실패: {click_err}")
                            
                        try:
                            pay_btn.evaluate(js_trigger)
                            print("결제 버튼 JS 디스패치 완료")
                        except Exception as eval_err:
                            print(f"결제 버튼 JS 디스패치 실패: {eval_err}")
                        
                        print("결제 완료 대기 (8초)...")
                        time.sleep(8)
                        page.wait_for_load_state("load")
                        
                        # 최종 결과 화면 덤프
                        page.screenshot(path="ad_complete.png")
                        with open("ad_complete.html", "w", encoding="utf-8") as f:
                            f.write(page.content())
                        print("최종 광고전송 완료 덤프 저장 완료 (ad_complete.html / png)")
                    else:
                        print(f"'{verify_method}' 카드를 찾을 수 없습니다.")
                else:
                    print("'광고하기' 버튼을 찾지 못했습니다.")
            else:
                print("광고전송 버튼을 찾지 못했습니다.")
        else:
            print("등록 매물 탭에서 신규 카드를 찾지 못했습니다.")
            
        browser.close()
        print("리서치 연계 작업이 완결되었습니다.")

if __name__ == "__main__":
    main()
