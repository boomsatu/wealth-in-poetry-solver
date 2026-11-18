"""Analyze MHTML for HTML formatting clues - bold, italic, links, special tags"""
import re

with open('article.mhtml', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Load BIP-39 wordlist
with open('english.txt', 'r') as f:
    bip39_words = set(f.read().strip().split('\n'))

# Extract the HTML part (after the MIME boundary)
html_start = content.find('<html')
html_end = content.find('</html>') + 7
if html_start > 0:
    html = content[html_start:html_end]
else:
    html = content

# Find all bold/strong text
bold = re.findall(r'<(?:b|strong)[^>]*>(.*?)</(?:b|strong)>', html, re.DOTALL | re.IGNORECASE)
print("=== BOLD/STRONG TEXT ===")
for i, t in enumerate(bold):
    clean = re.sub(r'<[^>]+>', '', t).strip()
    if clean:
        print(f"  {i}: {clean}")
        words = clean.lower().split()
        bip = [w for w in words if w in bip39_words]
        if bip:
            print(f"      BIP-39: {bip}")

print()

# Find all italic/em text  
italic = re.findall(r'<(?:i|em)[^>]*>(.*?)</(?:i|em)>', html, re.DOTALL | re.IGNORECASE)
print("=== ITALIC/EM TEXT ===")
for i, t in enumerate(italic):
    clean = re.sub(r'<[^>]+>', '', t).strip()
    if clean:
        print(f"  {i}: {clean}")
        words = clean.lower().split()
        bip = [w for w in words if w in bip39_words]
        if bip:
            print(f"      BIP-39: {bip}")

print()

# Find all hyperlinks (non-Medium)
links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
print("=== HYPERLINKS ===")
for i, (href, text) in enumerate(links):
    clean = re.sub(r'<[^>]+>', '', text).strip()
    if clean and len(clean) > 1:
        print(f"  {i}: [{clean}] -> {href[:80]}")

print()

# Find ALL class names used in the article
classes = re.findall(r'class="([^"]*)"', html)
unique_classes = sorted(set(classes))
print(f"=== UNIQUE CSS CLASSES ({len(unique_classes)}) ===")
for c in unique_classes[:50]:
    print(f"  {c}")

print()

# Look for any hidden or special elements
# data attributes
data_attrs = re.findall(r'data-[a-z-]+="([^"]*)"', html)
print(f"=== DATA ATTRIBUTES ({len(data_attrs)}) ===")
unique_data = sorted(set(data_attrs))
for d in unique_data[:30]:
    if len(d) > 2 and len(d) < 200:
        print(f"  {d}")

print()

# Check for blockquote text (the indented quotes in the article)
blockquotes = re.findall(r'<blockquote[^>]*>(.*?)</blockquote>', html, re.DOTALL | re.IGNORECASE)
print("=== BLOCKQUOTES ===")
for i, bq in enumerate(blockquotes):
    clean = re.sub(r'<[^>]+>', '', bq).strip()
    if clean:
        print(f"  {i}: {clean[:200]}")
        words = re.findall(r'[a-z]+', clean.lower())
        bip = [w for w in words if w in bip39_words]
        print(f"      BIP-39 words: {bip}")

print()

# Find figure captions
figcaptions = re.findall(r'<figcaption[^>]*>(.*?)</figcaption>', html, re.DOTALL | re.IGNORECASE)
print("=== FIGURE CAPTIONS ===")
for i, fc in enumerate(figcaptions):
    clean = re.sub(r'<[^>]+>', '', fc).strip()
    if clean:
        print(f"  {i}: {clean}")

# Check for any span with specific styling
styled_spans = re.findall(r'<span[^>]*style="([^"]*)"[^>]*>(.*?)</span>', html, re.DOTALL | re.IGNORECASE)
print(f"\n=== STYLED SPANS ({len(styled_spans)}) ===")
for i, (style, text) in enumerate(styled_spans):
    clean = re.sub(r'<[^>]+>', '', text).strip()
    if clean and len(clean) > 1 and 'font' not in style.lower():
        print(f"  {i}: style='{style[:60]}' text='{clean[:100]}'")
