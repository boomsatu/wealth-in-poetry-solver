import quopri
from bs4 import BeautifulSoup

with open('article.mhtml', 'rb') as f:
    raw = f.read()

decoded = quopri.decodestring(raw).decode('utf-8', errors='ignore')
soup = BeautifulSoup(decoded, 'html.parser')

print("=== ALL LINKS IN ARTICLE ===")
links = soup.find_all('a')
for i, a in enumerate(links):
    href = a.get('href', '')
    text = a.get_text(' ', strip=True)
    if 'medium.com' not in href and not href.startswith('#') and href:
        print(f"[{i:2d}] Text: '{text}' -> URL: {href}")

print("\n=== ALL <PRE> BLOCKS IN ARTICLE ===")
pres = soup.find_all('pre')
for i, pre in enumerate(pres):
    print(f"\n--- PRE BLOCK {i} ---")
    print(pre.get_text('\n', strip=True))
