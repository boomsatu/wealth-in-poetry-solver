import email
from email import policy
from bs4 import BeautifulSoup
import re

with open('article.mhtml', 'rb') as fp:
    msg = email.message_from_binary_file(fp, policy=policy.default)

html_content = ""
for part in msg.walk():
    if part.get_content_type() == 'text/html':
        html_content = part.get_content()
        break

soup = BeautifulSoup(html_content, 'html.parser')
article = soup.find('article') or soup

paragraphs = []
for tag in article.find_all(['p', 'blockquote', 'h1', 'h2', 'h3']):
    txt = tag.get_text(' ', strip=True)
    if txt:
        paragraphs.append((tag.name, txt))

print(f"Total elements found: {len(paragraphs)}")

with open('pure_paragraphs.txt', 'w', encoding='utf-8') as out:
    for i, (tag_name, txt) in enumerate(paragraphs):
        out.write(f"[{i:2d}] <{tag_name}> {txt}\n\n")

print("Saved pure_paragraphs.txt")
