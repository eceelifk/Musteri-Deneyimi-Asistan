import sys
sys.path.append(".")
from app.llm import ask_llm

try:
    for chunk in ask_llm("You are a helpful assistant.", "Count to 5."):
        print(chunk, end="")
except Exception as e:
    print("Error:", e)
