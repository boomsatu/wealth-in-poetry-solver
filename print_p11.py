with open('text.txt', encoding='utf-8') as f:
    full_text = f.read()

paragraphs = [p.strip() for p in full_text.split('\n\n') if p.strip()]
print(paragraphs[11])
