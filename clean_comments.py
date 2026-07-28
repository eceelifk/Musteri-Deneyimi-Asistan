import glob
import re

def clean_comments():
    files = glob.glob('app/*.py') + ['streamlit_app.py']
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        with open(f, 'w', encoding='utf-8') as file:
            for line in lines:
                # If line is entirely a comment (maybe with leading spaces)
                if re.match(r'^\s*#.*$', line):
                    continue
                # If there's an inline comment, strip it (but careful with URLs or strings)
                # We'll just remove full line comments to be safe
                file.write(line)

if __name__ == '__main__':
    clean_comments()
