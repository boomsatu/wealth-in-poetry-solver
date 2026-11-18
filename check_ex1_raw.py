with open('clean_article.txt', encoding='utf-8') as f:
    text = f.read()

start = text.find('Example:\nThe faint lines')
end = text.find('Letter & GPS location')
ex1_raw = text[start:end]
print("=== Example 1 Raw Text ===")
print(ex1_raw)
