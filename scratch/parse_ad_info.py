import os
import sys
import io
import re
from bs4 import BeautifulSoup

# 터미널 출력 인코딩을 UTF-8로 설정
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

def main():
    html_file = r"c:\Users\happinich\Documents\9.vibecoding\navermarket\research_stopped_card_detail.html"
    if not os.path.exists(html_file):
        print("파일이 없습니다.")
        return
        
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    # 정보 추출 초기화
    owner_name = ""
    carrier = ""
    phone = ""
    verify_method = ""
    
    # 1. 특정 공실번호(11583)를 포함하는 카드 컨테이너 찾기
    target_seq = "11583"
    card_div = None
    for div in soup.find_all("div", class_=lambda c: c and "border-gray50" in c):
        if target_seq in div.text:
            card_div = div
            break
            
    if card_div:
        # 카드 안에서 검증방식 추출 (모바일확인1, 모바일확인2, 구홍보확인서 등)
        method_span = card_div.find(string=lambda s: s and ("모바일확인" in s or "홍보확인서" in s or "현장확인" in s))
        if method_span:
            verify_method = method_span.strip()
    print("검증방식:", verify_method)
    
    # 2. 하단 매물 검증정보 섹션에서 등기부상 소유자명 추출
    # '등기부상의 소유자명' 이라는 라벨을 찾습니다.
    owner_label = soup.find(string=lambda s: s and "등기부상의 소유자명" in s)
    if owner_label:
        # 해당 라벨의 부모 div 중 background-pc-table 클래스 등을 가진 요소를 찾아봅니다.
        label_cell = None
        curr = owner_label.parent
        for _ in range(5):
            if curr and curr.name == "div" and curr.get("class") and any("background" in cls for cls in curr.get("class")):
                label_cell = curr
                break
            curr = curr.parent
            
        if label_cell:
            # 이 라벨 셀의 다음 형제 div가 실제 데이터를 갖고 있습니다.
            data_cell = label_cell.find_next_sibling()
            if data_cell:
                owner_name = data_cell.text.replace("*", "").strip()
    print("소유자명:", owner_name)
    
    # 3. 소유자 휴대폰 번호 및 통신사 추출
    # 페이지 전체에서 010-XXXX-XXXX 번호를 찾습니다.
    phone_span = soup.find(string=lambda s: s and re.match(r"^010-\d{3,4}-\d{4}$", s.strip()))
    if phone_span:
        phone = phone_span.strip()
        # 통신사는 이 휴대폰 번호 span과 같은 부모 아래의 이전 형제 span에 있을 것입니다.
        parent_div = phone_span.parent.parent # span -> div(flex-div)
        spans = parent_div.find_all("span")
        for sp in spans:
            txt = sp.text.strip()
            if txt in ["SKT", "KT", "LGU+", "SKT알뜰폰", "KT알뜰폰", "LGU+알뜰폰"]:
                carrier = txt
                break
                
    print("통신사:", carrier)
    print("휴대폰번호:", phone)

if __name__ == "__main__":
    main()
