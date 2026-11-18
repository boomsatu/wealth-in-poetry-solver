import email
from email import policy
import re
from bs4 import BeautifulSoup

with open('article.mhtml', 'rb') as fp:
    msg = email.message_from_binary_file(fp, policy=policy.default)

print("Subject:", msg.get('Subject'))
print("Parts:", len(msg.get_payload()))

html_content = ""
for part in msg.walk():
    if part.get_content_type() == 'text/html':
        html_content = part.get_content()
        break

soup = BeautifulSoup(html_content, 'html.parser')
# find article text
article = soup.find('article') or soup.find('main') or soup
text = article.get_text('\n', strip=True)

with open('clean_article.txt', 'w', encoding='utf-8') as out:
    out.write(text)

print("Wrote clean_article.txt, length:", len(text))
