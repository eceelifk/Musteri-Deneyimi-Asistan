from deep_translator import GoogleTranslator
import re

def translate_tr_to_en(text):
    if not text or not text.strip():
        return text
    try:
        translator = GoogleTranslator(source='tr', target='en')
        return translator.translate(text)
    except Exception as e:
        print(f"Çeviri hatası (TR->EN): {e}")
        return text

def translate_en_to_tr(text):
    if not text or not text.strip():
        return text
    try:
        translator = GoogleTranslator(source='en', target='tr')
        return translator.translate(text)
    except Exception as e:
        print(f"Çeviri hatası (EN->TR): {e}")
        return text

def translate_stream_en_to_tr(generator):
    """
    Takes an English text generator (stream), translates each chunk,
    and yields it. The incoming generator should ideally yield complete sentences.
    """
    translator = GoogleTranslator(source='en', target='tr')
    
    for chunk in generator:
        if not chunk.strip():
            yield chunk
            continue
            
        max_retries = 3
        translated = chunk
        for attempt in range(max_retries):
            try:
                result = translator.translate(chunk)
                if result is not None:
                    translated = result
                break
            except Exception:
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.5)
        
        # Orijinal sonlandırmaları koru
        if chunk.endswith('\n'):
            if not translated.endswith('\n'):
                translated += '\n'
        elif chunk.endswith(' '):
            if not translated.endswith(' '):
                translated += ' '
            
        # UI'da kelime kelime akıcı görünmesi için parçala
        words = translated.split(' ')
        for i, word in enumerate(words):
            if i < len(words) - 1:
                yield word + ' '
                import time
                time.sleep(0.02) # Küçük bir gecikme ile akış hissi ver
            else:
                yield word
