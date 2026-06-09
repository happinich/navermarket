import os
import sys
import io
import re
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', write_through=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', write_through=True)

html_path = r"c:\Users\happinich\Documents\9.vibecoding\navermarket\stopped_13062_detail.html"
if not os.path.exists(html_path):
    print(f"Error: {html_path} does not exist.")
    exit(1)

with open(html_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

print("=== Searching for unique numbers or registry numbers ===")
# Search for patterns like xxxx-xxxx-xxxx
text = soup.get_text()
matches = re.findall(r"\b\d{4}-\d{4}-\d{4}\b", text)
print("Regex matches for xxxx-xxxx-xxxx:", matches)

# Also search for "고유번호" or "등기" or "등록" or "번호" in text
for tag in soup.find_all(True):
    if tag.text and len(tag.text.strip()) < 100:
        txt = tag.text.strip()
        if "고유번호" in txt or "등기" in txt or "번호" in txt:
            print(f"Tag <{tag.name}>: {txt}")
