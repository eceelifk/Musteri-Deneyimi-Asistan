from deep_translator import GoogleTranslator

def tr_to_en(text):
    """Kullanıcının Türkçe sorusunu arama yapmak için İngilizceye çevirir."""
    if not text:
        return ""
    
    try:
        translated = GoogleTranslator(source='tr', target='en').translate(text)
        return translated if translated is not None else text
    except Exception as e:
        print(f"Translation error: {e}")
        # Hata olursa orijinal metni döndür (RAG şansını dener)
        return text

def en_to_tr(text):
    """Yapay zekanın ürettiği İngilizce cevabı Türkçe olarak çevirir."""
    if not text or not text.strip():
        return text or ""
        
    try:
        translated = GoogleTranslator(source='en', target='tr').translate(text)
        return translated if translated is not None else text
    except Exception as e:
        print(f"Translation error (en_to_tr): {e}")
        return text
