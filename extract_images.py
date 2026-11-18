import email
from email import policy
import os

with open('article.mhtml', 'rb') as fp:
    msg = email.message_from_binary_file(fp, policy=policy.default)

os.makedirs('extracted_images', exist_ok=True)

img_idx = 0
for part in msg.walk():
    ctype = part.get_content_type()
    if ctype.startswith('image/'):
        loc = part.get('Content-Location', f'image_{img_idx}')
        # filename
        ext = ctype.split('/')[-1]
        fname = f"extracted_images/img_{img_idx}.{ext}"
        payload = part.get_payload(decode=True)
        if payload:
            with open(fname, 'wb') as f:
                f.write(payload)
            print(f"Saved {fname} (size: {len(payload)}, location: {loc[:60]})")
            img_idx += 1
