import inspect
import foundry_local_sdk
import os

def find_file():
    for root, dirs, files in os.walk(os.path.dirname(foundry_local_sdk.__file__)):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'def complete_streaming_chat' in content:
                        print(f"Found in {path}")
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if 'def complete_streaming_chat' in line:
                                print('\n'.join(lines[i:i+5]))
find_file()
