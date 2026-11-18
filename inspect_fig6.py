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
fig6 = figures[6]

# Look at preceding and following paragraphs
prev_p = fig6.find_previous(['p', 'h1', 'h2', 'h3'])
next_p = fig6.find_next(['p', 'h1', 'h2', 'h3'])

print("Prev tag:", prev_p.get_text() if prev_p else None)
print("Next tag:", next_p.get_text() if next_p else None)
