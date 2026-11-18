with open('text.txt') as f:
    lines = f.readlines()

# Revolution section:
# Lines 19 to 38
rev_lines = lines[18:38]
rev_text = ''.join(rev_lines)
print("=== REVOLUTION TEXT ===")
print(rev_text)
