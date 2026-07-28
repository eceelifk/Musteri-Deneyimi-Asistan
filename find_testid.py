import os, re
path = r'C:\Users\elife\AppData\Local\Programs\Python\Python312\Lib\site-packages\streamlit\static\static\js'
for f in os.listdir(path):
    if f.endswith('.js'):
        with open(os.path.join(path, f), encoding='utf-8', errors='ignore') as file:
            content = file.read()
            matches = re.findall(r'data-testid="st[^"]*"', content)
            for m in set(matches):
                if 'chat' in m.lower() or 'avatar' in m.lower():
                    print(m)
