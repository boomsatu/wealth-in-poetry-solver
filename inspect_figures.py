import email
from email import policy
from bs4 import BeautifulSoup

with open('article.mhtml', 'rb') as fp:
    msg = email.message_from_binary_file(fp, policy=policy.default)

for part in msg.walk():
    if part.get_content_type() == 'text/html':
        html_content = part.get_content()
        break

soup = BeautifulSoup(html_content, 'html.parser')

figures = soup.find_all('figure')
for i, f in enumerate(figures):
    caption = f.find('figcaption')
    cap_text = caption.get_text().strip() if caption else "NO CAPTION"
    img = f.find('img')
    img_src = img.get('src') if img else "NO IMG"
    print(f"\nFigure {i}:")
    print(f"  Caption: {cap_text}")
    print(f"  Img: {img_src[:80]}")
