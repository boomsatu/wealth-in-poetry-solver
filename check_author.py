import re

with open('article.mhtml', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Look for user handle / author info
matches = re.findall(r'https?://[^\s\"\'<>]*medium\.com/[^\s\"\'<>]*', text)
for m in sorted(set(matches)):
    if '@' in m or 'user' in m or 'author' in m or 'coinmonks' in m:
        print(m)

# Look for "creator" or "author" metadata
author_meta = re.findall(r'<meta[^>]*author[^>]*>', text, re.IGNORECASE)
print("Author meta:", author_meta)

creator_meta = re.findall(r'<meta[^>]*creator[^>]*>', text, re.IGNORECASE)
print("Creator meta:", creator_meta)

# Look for twitter:
twitter_meta = re.findall(r'<meta[^>]*twitter[^>]*>', text, re.IGNORECASE)
for tm in twitter_meta[:10]:
    print("Twitter meta:", tm)
