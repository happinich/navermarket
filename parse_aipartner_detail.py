import re
import sys
import json
from bs4 import BeautifulSoup

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    html_path = "aipartner_detail.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"Error: {html_path} 파일을 읽는 중 오류 발생: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")
    
    data = {}
    
    print("==================================================")
    print(" AI파트너(이실장) 매물 상세 데이터 추출 시작")
    print("==================================================")
    
    # 1. 기본 정보 (텍스트 형태로 렌더링된 정보)
    # 매물종류, 소재지, 단지, 동/호, 면적 등
    print("\n[1] 기본 정보 추출")
    
    def get_row_value(label_text):
        label = soup.find(text=re.compile(label_text))
        if label:
            # 보통 label 옆의 div나 td에 값이 있습니다.
            parent = label.parent
            # 형제 노드나 부모의 형제 노드 탐색
            # 이실장 마크업은 보통 td나 div.input-form 구조입니다.
            sibling = parent.find_next_sibling()
            if sibling:
                return sibling.get_text(strip=True)
            # 또는 상위 노드로 올라가서 다음 td/div 찾기
            p = parent.parent
            for child in p.find_all(recursive=False):
                if child != parent:
                    return child.get_text(strip=True)
        return "None"

    # 이실장 상세 페이지는 React 또는 일반 form 구조로 되어 있으므로,
    # select 태그와 input 태그의 value를 직접 읽는 것이 정확합니다.
    
    # 2. 위치/구조 (input, select, checked)
    print("\n[2] 위치 및 구조 정보 추출")
    
    # 방수
    room_cnt = soup.find("input", {"name": re.compile(r"room.*cnt|room.*count", re.I)})
    if not room_cnt:
        room_cnt = soup.find("input", {"id": re.compile(r"room.*cnt|room.*count", re.I)})
    # 셀렉터가 애매하면 placeholder나 value 직접 탐색
    # HTML 내의 input value 목록을 딕셔너리로 다 가져와서 필터링하는 방식이 안전합니다.
    
    all_inputs = {}
    for inp in soup.find_all("input"):
        inp_name = inp.get("name") or inp.get("id")
        inp_type = inp.get("type", "text")
        
        if not inp_name:
            continue
            
        if inp_type in ["checkbox", "radio"]:
            if inp.has_attr("checked"):
                all_inputs[inp_name] = inp.get("value") or "checked"
        else:
            all_inputs[inp_name] = inp.get("value", "")
            
    # select 목록 가져오기
    all_selects = {}
    for sel in soup.find_all("select"):
        sel_name = sel.get("name") or sel.get("id")
        if not sel_name:
            continue
        selected_opt = sel.find("option", selected=True)
        if selected_opt:
            all_selects[sel_name] = selected_opt.get("value") or selected_opt.get_text(strip=True)
        else:
            first_opt = sel.find("option")
            if first_opt:
                all_selects[sel_name] = first_opt.get("value") or first_opt.get_text(strip=True)
                
    # textarea 목록 가져오기
    all_textareas = {}
    for ta in soup.find_all("textarea"):
        ta_name = ta.get("name") or ta.get("id")
        if ta_name:
            all_textareas[ta_name] = ta.get_text(strip=True)
            
    # 이미지 리스트 가져오기
    images = []
    # 사진 정보 영역의 썸네일 이미지들 추출
    # 보통 class="img" 또는 div.img-box 내의 img src
    for img in soup.find_all("img"):
        src = img.get("src", "")
        # 배너나 로고 이미지 제외, cdn.aipartner.com/estate 등 매물 관련 이미지만 필터링
        if "cdn.aipartner.com" in src and "logo" not in src and "banner" not in src:
            images.append(src)
            
    # 추출한 데이터 정리 및 콘솔 출력
    print("\n--- [추출된 전체 Input 값 요약] ---")
    for k, v in all_inputs.items():
        if v:
            print(f"Input   - {k}: {v}")
            
    print("\n--- [추출된 전체 Select 값 요약] ---")
    for k, v in all_selects.items():
        print(f"Select  - {k}: {v}")
        
    print("\n--- [추출된 전체 Textarea 값 요약] ---")
    for k, v in all_textareas.items():
        print(f"Textarea - {k}: {v}")
        
    print("\n--- [추출된 매물 사진 URL 목록] ---")
    for idx, img_url in enumerate(images):
        print(f"Image [{idx}]: {img_url}")

if __name__ == "__main__":
    main()
