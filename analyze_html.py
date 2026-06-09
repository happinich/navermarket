import re
import sys
from bs4 import BeautifulSoup

def main():
    # 윈도우 콘솔 한글 깨짐 방지용 출력 인코딩 재설정
    sys.stdout.reconfigure(encoding='utf-8')
    
    html_path = "gongsil_management.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"Error: {html_path} 파일을 읽는 중 오류 발생: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")
    print("==================================================")
    print(" 공실클럽 매물관리 HTML 구조 분석 결과")
    print("==================================================")
    
    # 1. 상단 주요 버튼 분석
    print("\n[1] 상단 주요 버튼 분석")
    
    # + 매물등록 버튼 찾기
    reg_btn = soup.find(text=re.compile(r"\+\s*매물등록"))
    if reg_btn:
        parent = reg_btn.parent
        # 부모 노드를 추적하여 실제 버튼 요소 찾기
        while parent and parent.name not in ["button", "a", "div"]:
            parent = parent.parent
        print(f"▶ '+ 매물등록' 버튼 정보:")
        print(f"   - Tag: {parent.name}")
        print(f"   - Class: {parent.get('class')}")
        print(f"   - Text: {parent.get_text(strip=True)}")
        print(f"   - Attributes: {parent.attrs}")
    else:
        # 텍스트로 못 찾은 경우
        print("▶ '+ 매물등록' 버튼을 찾지 못해 전체 검색 시도...")
        all_buttons = soup.find_all(["button", "div", "a"])
        for btn in all_buttons:
            text = btn.get_text(strip=True)
            if "+ 매물등록" in text or "매물등록" in text:
                print(f"   - Tag: {btn.name}, Class: {btn.get('class')}, Text: {text}")
                break

    # 네이버 매물 가져오기 버튼 찾기
    naver_btn = soup.find(text=re.compile(r"네이버\s*매물\s*가져오기"))
    if naver_btn:
        parent = naver_btn.parent
        while parent and parent.name not in ["button", "a", "div"]:
            parent = parent.parent
        print(f"▶ '네이버 매물 가져오기' 버튼 정보:")
        print(f"   - Tag: {parent.name}")
        print(f"   - Class: {parent.get('class')}")
        print(f"   - Text: {parent.get_text(strip=True)}")
        print(f"   - Attributes: {parent.attrs}")
    else:
        print("▶ '네이버 매물 가져오기' 버튼을 찾지 못함.")
        
    # 2. 탭 분류 분석
    print("\n[2] 탭 분류 분석 (등록 매물, 종료·취소 등)")
    tabs = ["등록 매물", "종료·취소·실패", "동일주소 거래완료", "신고매물", "전송 내역"]
    for tab in tabs:
        tab_element = soup.find(text=re.compile(tab))
        if tab_element:
            parent = tab_element.parent
            print(f"▶ 탭 '{tab}': Tag={parent.name}, Class={parent.get('class')}, Text={parent.get_text(strip=True)}")
        else:
            print(f"▶ 탭 '{tab}': 찾을 수 없음")

    # 3. 매물 카드 리스트 분석
    print("\n[3] 매물 카드 리스트 분석")
    # 스크린샷 상의 첫 번째 매물인 "G 13062" 또는 "N 2630984122" 등의 숫자를 단서로 첫 번째 매물 카드 요소를 찾습니다.
    target_num = "13062"
    first_item_text = soup.find(text=re.compile(target_num))
    
    if first_item_text:
        # 해당 텍스트를 가진 부모 카드의 최상단 컨테이너를 찾습니다.
        # 스크린샷 상 둥근 테두리와 배경색을 보아 카드 형태의 div입니다.
        parent_card = first_item_text.parent
        depth = 0
        # 적절한 카드 컨테이너(보통 테두리가 있는 div)를 찾기 위해 부모로 올라감
        while parent_card and depth < 10:
            card_class = parent_card.get("class", [])
            # 일반적으로 리스트 아이템은 고유한 class 구조를 갖습니다.
            # class 리스트 중 카드 형태를 암시하는 요소를 찾거나 적절한 높이에서 멈춤
            if any("card" in c or "item" in c or "list" in c or "box" in c for c in card_class) or parent_card.name == "li":
                break
            # class가 없더라도 둥근 모서리 보더 등이 지정된 최상위 div를 추적
            if parent_card.name == "div" and parent_card.parent and parent_card.parent.name == "div" and len(parent_card.parent.find_all(recursive=False)) > 2:
                # 형제 노드가 여러개 있는 div 컨테이너가 리스트일 가능성이 높음
                break
            parent_card = parent_card.parent
            depth += 1
            
        print(f"▶ 매물 카드 컨테이너 정보:")
        print(f"   - Tag: {parent_card.name if parent_card else 'None'}")
        print(f"   - Class: {parent_card.get('class') if parent_card else 'None'}")
        
        # 카드 내부 주요 정보 셀렉터 파악
        if parent_card:
            # 공실클럽 번호 (G xxxxx)
            g_num = parent_card.find(text=re.compile(r"G\s*\d+"))
            if not g_num:
                g_num = parent_card.find(text=re.compile(r"13062"))
            if g_num:
                print(f"   - 공실클럽 번호 요소: Tag={g_num.parent.name}, Class={g_num.parent.get('class')}, Text={g_num.parent.get_text(strip=True)}")
                # 링크 A 태그인 경우 href 분석
                a_tag = g_num.parent if g_num.parent.name == "a" else g_num.parent.find_parent("a")
                if a_tag:
                    print(f"     * Link: href={a_tag.get('href')}")
            
            # 네이버 매물번호 (N xxxxx)
            n_num = parent_card.find(text=re.compile(r"2630984122"))
            if n_num:
                print(f"   - 네이버 매물번호 요소: Tag={n_num.parent.name}, Class={n_num.parent.get('class')}, Text={n_num.parent.get_text(strip=True)}")
                a_tag = n_num.parent if n_num.parent.name == "a" else n_num.parent.find_parent("a")
                if a_tag:
                    print(f"     * Link: href={a_tag.get('href')}")

            # 매물 주소/정보
            addr = parent_card.find(text=re.compile(r"퍼시픽"))
            if addr:
                print(f"   - 매물 주소 요소: Tag={addr.parent.name}, Class={addr.parent.get('class')}, Text={addr.parent.get_text(strip=True)}")
            
            # 금액 정보
            price = parent_card.find(text=re.compile(r"월세\s*900"))
            if price:
                print(f"   - 매물 금액 요소: Tag={price.parent.name}, Class={price.parent.get('class')}, Text={price.parent.get_text(strip=True)}")

            # "매물수정" 및 "광고종료" 버튼 분석
            edit_btn = parent_card.find(text=re.compile(r"매물수정"))
            if edit_btn:
                parent_btn = edit_btn.parent
                while parent_btn and parent_btn.name not in ["button", "a", "div"]:
                    parent_btn = parent_btn.parent
                print(f"   - '매물수정' 버튼: Tag={parent_btn.name}, Class={parent_btn.get('class')}, Attrs={parent_btn.attrs}")
                
            close_btn = parent_card.find(text=re.compile(r"광고종료"))
            if close_btn:
                parent_btn = close_btn.parent
                while parent_btn and parent_btn.name not in ["button", "a", "div"]:
                    parent_btn = parent_btn.parent
                print(f"   - '광고종료' 버튼: Tag={parent_btn.name}, Class={parent_btn.get('class')}, Attrs={parent_btn.attrs}")
    else:
        print("▶ 첫 번째 매물 카드 요소를 찾을 수 없습니다. HTML 구조 파싱 필요.")

if __name__ == "__main__":
    main()
