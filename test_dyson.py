import sys
import time
from app.rag import ask
from app.memory import chat_history

print("--- DYSON HALÜSİNASYON TESTİ (YENİ KATI KURALLA) ---")
question = "Dyson marka süpürge almalı mıyım?"
print(f"Soru: {question}\n")

chat_history.clear()
start_time = time.time()

res = ask(question, filter_type="review")

print("Cevap:")
for chunk in res["answer_stream"]:
    sys.stdout.write(chunk)
    sys.stdout.flush()

total_time = time.time() - start_time
print(f"\n\nSüre: {total_time:.2f} saniye")
