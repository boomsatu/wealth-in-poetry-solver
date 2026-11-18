import re

with open('clean_article.txt', encoding='utf-8') as f:
    text = f.read()

lines = text.split('\n')
print(f"Total lines in clean_article.txt: {len(lines)}")

# Let's see all numbers in the text
numbers = re.findall(r'\b\d+[\d\.,\-\/]*\b', text)
print("All numbers found in text:")
print(numbers)
