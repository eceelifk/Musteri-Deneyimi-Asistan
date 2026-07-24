import sys
import time
import logging
from app.rag import ask
from app.memory import chat_history

logging.basicConfig(
    filename="test_v3.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

questions = [
    # --- GEÇERLİ FAQ (Sıkça Sorulan Sorular) ---
    {"q": "Şifremi unuttum, hesabımı nasıl kurtarabilirim?", "filter": "faq", "type": "Geçerli"},
    {"q": "Sipariş iptali sonrasında para iadesi hemen yapılır mı?", "filter": "faq", "type": "Geçerli"},
    {"q": "Amazon Prime'a video ve müzik dahil mi?", "filter": "faq", "type": "Geçerli"},
    {"q": "Kapıda ödeme seçeneğiniz bulunuyor mu?", "filter": "faq", "type": "Geçerli"},
    {"q": "Faturamı nasıl indirebilirim veya görebilirim?", "filter": "faq", "type": "Geçerli"},
    {"q": "Prime üyeliğimi nasıl iptal edebilirim?", "filter": "faq", "type": "Geçerli"},
    {"q": "Hafta sonu kargo teslimatı yapıyor musunuz?", "filter": "faq", "type": "Geçerli"},
    {"q": "Hasarlı gelen kargoyu kuryeden teslim alırken ne yapmalıyım?", "filter": "faq", "type": "Geçerli"},
    {"q": "Kargo takip numaramı unuttum, nerede bulabilirim?", "filter": "faq", "type": "Geçerli"},
    {"q": "Gümrük vergisi ve ithalat ücretleri fiyatlara dahil mi?", "filter": "faq", "type": "Geçerli"},

    # --- GEÇERLİ YORUMLAR (Reviews) ---
    {"q": "Memorex Portable CD Boombox radyosunun ses kalitesi nasıl?", "filter": "review", "type": "Geçerli"},
    {"q": "Nikon MH-61 Batarya Şarj Cihazı iyi şarj ediyor mu?", "filter": "review", "type": "Geçerli"},
    {"q": "Symphonized NRG Premium ahşap kulaklık bas konusunda nasıl?", "filter": "review", "type": "Geçerli"},
    {"q": "Philips ActionFit spor kulaklık egzersiz yaparken rahat mı?", "filter": "review", "type": "Geçerli"},
    {"q": "Flexion KS-902 Bluetooth kulaklığın gürültü engellemesi çalışıyor mu?", "filter": "review", "type": "Geçerli"},

    # --- GEÇERSİZ / TUZAK SORULAR (Out of Scope - Bilmiyorum demeli) ---
    {"q": "Türkiye'nin başkenti neresidir?", "filter": "all", "type": "Geçersiz (Tuzak)"},
    {"q": "Dolar kuru bugün ne kadar oldu?", "filter": "faq", "type": "Geçersiz (Tuzak)"},
    {"q": "Fenerbahçe'nin son oynadığı derbinin skoru nedir?", "filter": "all", "type": "Geçersiz (Tuzak)"},
    {"q": "Tavada krep nasıl yapılır tarif verir misin?", "filter": "all", "type": "Geçersiz (Tuzak)"},
    {"q": "Samsung Galaxy S24 Ultra'nın kamerası iyi mi?", "filter": "review", "type": "Geçersiz (Tuzak)"}
]

total_tests = len(questions)
print(f"20 Soruluk Kapsamlı Test V3 Başlıyor...\n")
logging.info("--- YENİ KAPSAMLI TEST V3 BAŞLADI (20 SORU) ---")

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
        if "bilgi" in ans.lower() and ("bulunamadı" in ans.lower() or "veritabanı" in ans.lower() or "database" in ans.lower() or "yok" in ans.lower()):
            status = "BAŞARILI (Doğru Reddetme)"
        else:
            status = "BAŞARISIZ (Uydurdu)"
            
    print(f"  -> Durum: {status} ({total_time:.2f}s)")
    logging.info(f"Durum: {status} | Süre: {total_time:.2f}s")
    logging.info(f"Cevap: {ans}\n")

print("\nTüm testler tamamlandı! Sonuçlar test_v3.log dosyasına kaydedildi.")
logging.info("--- TEST BİTTİ ---")
