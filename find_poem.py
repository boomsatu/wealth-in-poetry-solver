with open('clean_article.txt', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'poem', text, re.IGNORECASE)]
for idx in matches:
    print("--- MATCH AT", idx, "---")
    print(text[max(0, idx-100):min(len(text), idx+200)])
