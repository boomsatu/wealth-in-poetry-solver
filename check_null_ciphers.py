import re

with open('text.txt', encoding='utf-8') as f:
    text = f.read()

# 1. First letter of each paragraph
paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
p_first_letters = "".join([p[0] for p in paragraphs if p])
print("First letter of each paragraph:")
print(p_first_letters)

# 2. First letter of each sentence
sentences = re.split(r'[.!?]+', text)
s_first_letters = "".join([re.sub(r'[^a-zA-Z]', '', s)[0] for s in sentences if re.sub(r'[^a-zA-Z]', '', s)])
print("\nFirst letter of each sentence:")
print(s_first_letters[:150])

# 3. All capital letters in text
caps = re.findall(r'[A-Z]', text)
print("\nTotal capital letters:", len(caps))
print("".join(caps[:150]))
