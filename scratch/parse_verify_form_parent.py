import os
import sys
import io
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8')

def main():
    html_file = r"c:\Users\happinich\Documents\9.vibecoding\navermarket\research_ad_verify_form.html"
    if not os.path.exists(html_file):
        print("파일이 없습니다.")
        return
        
    with open(html_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
        
    # '매물 광고신청' 텍스트를 포함하는 요소 찾기
    label = soup.find(string=lambda s: s and "매물 광고신청" in s)
    if label:
        print("Found Label:", label)
        curr = label.parent
        for i in range(8):
            print(f"Parent {i}: tag={curr.name}, class={curr.get('class')}")
            # 이 조상 아래에 있는 border-gray50 카드들을 출력
            cards = curr.find_all("div", class_=lambda c: c and "border-gray50" in c)
            print(f"   Number of border-gray50 cards under Parent {i}: {len(cards)}")
            # 만약 카드 개수가 6개 내외인 최적의 모달 영역을 찾으면 상세 정보 출력
            if len(cards) > 0 and len(cards) <= 6:
                print("--- Found Verification Selection Container! ---")
                for idx, card in enumerate(cards):
                    print(f"      Card {idx}: {card.text.strip()[:100]}")
                break
            break
        curr = curr.parent
    else:
        print("검증방식 선택 라벨을 찾지 못했습니다.")

if __name__ == "__main__":
    main()
