import email
from email import policy
from bs4 import BeautifulSoup, Comment

with open('article.mhtml', 'rb') as fp:
    msg = email.message_from_binary_file(fp, policy=policy.default)

for part in msg.walk():
    if part.get_content_type() == 'text/html':
        html_content = part.get_content()
        break

soup = BeautifulSoup(html_content, 'html.parser')

print("=== HTML Comments ===")
comments = soup.find_all(string=lambda text: isinstance(text, Comment))
for c in comments:
    if len(c.strip()) > 0 and len(c.strip()) < 500:
        print("Comment:", c.strip())

print("\n=== All Links (href) ===")
links = soup.find_all('a')
for a in links:
    href = a.get('href')
    text = a.get_text().strip()
    if href and ('bitcoin' in href or 'btc' in href or 'blockchain' in href or 't.me' in href or 'twitter' in href or 'medium' in href or 'http' in href):
        print(f"{text} -> {href}")

print("\n=== All Images (src, alt) ===")
imgs = soup.find_all('img')
for img in imgs:
    src = img.get('src')
    alt = img.get('alt')
    print(f"Alt: {alt} | Src: {src[:60] if src else 'None'}")
