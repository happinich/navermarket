import os
import sys
import io
import re
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

def main():
    html_file = r"c:\Users\happinich\Documents\9.vibecoding\navermarket\research_ad_verify_form_clicked.html"
    if not os.path.exists(html_file):
        print("파일이 없습니다.")
        return
        
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
        soup = BeautifulSoup(content, "html.parser")
        
    print("--- Tracing carrier inputs in clicked HTML ---")
    # 'SKT' 또는 '선택' 또는 '통신사' 텍스트를 담은 모든 div
    divs = soup.find_all("div")
    found = 0
    for d in divs:
        txt = d.text.strip()
        # 하위 div가 없는 말단 div 위주로
        if len(d.find_all("div")) == 0 and any(kw in txt for kw in ["SKT", "KT", "LGU+", "통신사"]):
            print(f"Match {found}: tag={d.name}, class={d.get('class')}, style={d.get('style')}, text='{txt}'")
            # 3단계 조상까지 출력
            curr = d.parent
            for idx in range(3):
                print(f"  Ancestor {idx}: tag={curr.name}, class={curr.get('class')}, style={curr.get('style')}")
                curr = curr.parent
            found += 1
            if found > 20:
                break

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
