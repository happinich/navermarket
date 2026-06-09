import os
import sys
import io
from bs4 import BeautifulSoup

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8', write_through=True)
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding='utf-8', write_through=True)

html_path = r"c:\Users\happinich\Documents\9.vibecoding\navermarket\popup_step2.html"
if not os.path.exists(html_path):
    print(f"Error: {html_path} does not exist.")
    exit(1)

with open(html_path, "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

print("=== All text strings in popup_step2.html ===")
body = soup.find("body")
if body:
    for s in body.stripped_strings:
        if len(s) > 1:
            print(s)
else:
    print("Body not found.")






