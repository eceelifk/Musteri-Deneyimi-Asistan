import sys
import time
import logging
from app.rag import ask
from app.memory import chat_history

logging.basicConfig(
    filename="test_v2.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

questions = [
    # --- GEÇERLİ FAQ (Sıkça Sorulan Sorular) ---
    {"q": "Siparişim nerede kaldı, nasıl takip edebilirim?", "filter": "faq", "type": "Geçerli"},
    {"q": "Kargo ücretleri ne kadar?", "filter": "faq", "type": "Geçerli"},
    {"q": "Ürünü iade etmek istiyorum, kargo ücreti ödeyecek miyim?", "filter": "faq", "type": "Geçerli"},
    {"q": "İadem onaylandı, param ne zaman yatar?", "filter": "faq", "type": "Geçerli"},
    {"q": "Kredi kartına taksit yapıyor musunuz?", "filter": "faq", "type": "Geçerli"},
    {"q": "Prime üyesi olursam kargo bedava mı olur?", "filter": "faq", "type": "Geçerli"},
    {"q": "Müşteri hizmetlerine nasıl ulaşabilirim?", "filter": "faq", "type": "Geçerli"},
    {"q": "Hediye kartı ile ödeme yapabilir miyim?", "filter": "faq", "type": "Geçerli"},
    {"q": "Siparişim hasarlı geldi, ne yapmalıyım?", "filter": "faq", "type": "Geçerli"},
    {"q": "Yurt dışına kargo gönderiyor musunuz?", "filter": "faq", "type": "Geçerli"},

    # --- GEÇERLİ YORUMLAR (Reviews) ---
    {"q": "Sony Cyber-shot fotoğraf makinesi için yorumlar nasıl?", "filter": "review", "type": "Geçerli"},
    {"q": "Radio Flyer oyuncak vagonun montajı kolay mı?", "filter": "review", "type": "Geçerli"},
    {"q": "Canon 430EX Flaş dış çekimler için iyi mi?", "filter": "review", "type": "Geçerli"},
    {"q": "Polk Audio CS10 hoparlörün ses kalitesi nasıl?", "filter": "review", "type": "Geçerli"},

    # --- GEÇERSİZ / TUZAK SORULAR (Out of Scope - Bilmiyorum demeli) ---
    {"q": "Yarın İstanbul'da yağmur yağacak mı?", "filter": "all", "type": "Geçersiz (Tuzak)"},
    {"q": "Dyson marka süpürge almalı mıyım?", "filter": "review", "type": "Geçersiz (Tuzak)"},
    {"q": "Elon Musk'ın serveti ne kadar?", "filter": "faq", "type": "Geçersiz (Tuzak)"},
    {"q": "PlayStation 5 stoklara ne zaman girecek?", "filter": "all", "type": "Geçersiz (Tuzak)"},
    {"q": "Bana en iyi korku filmlerini önerir misin?", "filter": "all", "type": "Geçersiz (Tuzak)"},
    {"q": "iPhone 15 Pro Max kamerası nasıl yorumlanmış?", "filter": "review", "type": "Geçersiz (Tuzak)"}
]

total_tests = len(questions)
print(f"20 Soruluk Kapsamlı Test Başlıyor...\n")
logging.info("--- YENİ KAPSAMLI TEST BAŞLADI (20 SORU) ---")

for i, item in enumerate(questions, 1):
    question = item["q"]
    f_type = item["filter"]
    q_type = item["type"]
    
    print(f"[{i}/{total_tests}] Soru: {question} (Filtre: {f_type})")
    logging.info(f"Soru [{i}/{total_tests}]: {question} | Beklenti: {q_type}")
    
    chat_history.clear()
    start_time = time.time()
    
    try:
        res = ask(question, filter_type=f_type)
        ans = "".join(list(res["answer_stream"]))
    except Exception as e:
        ans = f"HATA OLUŞTU: {str(e)}"
        
    total_time = time.time() - start_time
    
    status = "BAŞARILI"
    if "Geçersiz" in q_type:
        if "bilgi bulunamadı" in ans.lower() or "bilgim bulunmuyor" in ans.lower() or "herhangi bir bilgi yok" in ans.lower():
            status = "BAŞARILI (Doğru Reddetme)"
        else:
            status = "BAŞARISIZ (Uydurdu)"
            
    print(f"  -> Durum: {status} ({total_time:.2f}s)")
    logging.info(f"Durum: {status} | Süre: {total_time:.2f}s")
    logging.info(f"Cevap: {ans}\n")

print("\nTüm testler tamamlandı! Sonuçlar test_v2.log dosyasına kaydedildi.")
logging.info("--- TEST BİTTİ ---")
