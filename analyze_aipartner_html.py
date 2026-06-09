import re
import sys
from bs4 import BeautifulSoup

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    
    html_path = "aipartner_management.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
    except Exception as e:
        print(f"Error: {html_path} 파일을 읽는 중 오류 발생: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")
    print("==================================================")
    print(" AI파트너(이실장) 매물관리 HTML 구조 분석 결과")
    print("==================================================")
    
    # 1. 매물 리스트 테이블/리스트 탐색
    print("\n[1] 매물 리스트 컨테이너 구조")
    # 스크린샷 상의 첫 번째 매물번호 "6270553"을 타겟으로 행(row)을 찾습니다.
    target_no = "6270553"
    first_no_element = soup.find(text=re.compile(target_no))
    
    if first_no_element:
        # 이 번호가 들어있는 tr 혹은 li 등 행 단위를 찾습니다.
        row = first_no_element.parent
        depth = 0
        while row and depth < 8:
            if row.name in ["tr", "li"] or (row.name == "div" and "row" in row.get("class", [])):
                break
            row = row.parent
            depth += 1
            
        print(f"▶ 매물 행(Row) 컨테이너 정보:")
        print(f"   - Tag: {row.name}")
        print(f"   - Class: {row.get('class')}")
        print(f"   - Attributes: {row.attrs}")
        
        # 행의 자식 셀(Cell) 구조 분석
        if row.name == "tr":
            cells = row.find_all("td", recursive=False)
            print(f"   - td 개수: {len(cells)}")
            for idx, cell in enumerate(cells):
                cell_text = cell.get_text(strip=True)
                # 텍스트가 너무 길면 줄임
                short_text = cell_text[:50] + "..." if len(cell_text) > 50 else cell_text
                print(f"     * td[{idx}]: Class={cell.get('class')}, Text='{short_text}'")
                
                # '수정하기' 버튼 위치 찾기
                if "수정하기" in cell_text:
                    edit_a = cell.find("a")
                    if edit_a:
                        print(f"       -> '수정하기' 링크 발견: Tag={edit_a.name}, Class={edit_a.get('class')}, href={edit_a.get('href')}, click={edit_a.get('onclick')}")
                    else:
                        edit_div = cell.find(["div", "button"])
                        print(f"       -> '수정하기' 버튼 발견: Tag={edit_div.name}, Class={edit_div.get('class')}")
    else:
        print("▶ 첫 번째 매물번호 '6270553' 요소를 찾을 수 없습니다. HTML에서 다른 매물 매칭을 시도합니다.")
        # '수정하기' 텍스트를 가진 요소 기준 역추적
        edit_text = soup.find(string=re.compile(r"수정하기"))
        if edit_text:
            print("▶ '수정하기' 텍스트 기반 행 추적 성공")
            parent_a = edit_text.parent
            while parent_a and parent_a.name not in ["a", "button", "div"]:
                parent_a = parent_a.parent
            print(f"   - '수정하기' 클릭 요소: Tag={parent_a.name}")
            print(f"   - Attributes: {parent_a.attrs}")
            # 부모 행(Row)도 역추적해서 전체 정보와 다른 속성도 봅니다.
            row = parent_a.parent
            while row and row.name not in ["tr", "li"]:
                row = row.parent
            if row:
                print(f"   - Row Tag: {row.name}, Attributes: {row.attrs}")
        else:
            print("▶ 매물 데이터를 전혀 찾을 수 없습니다.")

if __name__ == "__main__":
    main()
