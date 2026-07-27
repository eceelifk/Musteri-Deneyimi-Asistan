import sqlite3
import re
conn = sqlite3.connect('database/rag.db')
cur = conn.cursor()
cur.execute("SELECT chunk FROM documents WHERE type='review'")
names = set()
for row in cur.fetchall():
    match = re.search(r'Product Name:\s*(.*?)\n', row[0])
    if match:
        names.add(match.group(1).strip())
print(list(names)[:20])
conn.close()
