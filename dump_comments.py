import os
import glob

def find_comments():
    files = glob.glob('**/*.py', recursive=True)
    with open('comments_dump.txt', 'w', encoding='utf-8') as out:
        for f in files:
            if 'venv' in f or '.venv' in f or '__pycache__' in f:
                continue
            with open(f, 'r', encoding='utf-8') as inf:
                lines = inf.readlines()
                for i, line in enumerate(lines):
                    if '#' in line:
                        out.write(f"{f}:{i+1}:{line}")

if __name__ == '__main__':
    find_comments()
