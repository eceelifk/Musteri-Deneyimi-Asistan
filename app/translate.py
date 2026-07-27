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
    Takes an English text generator (stream), buffers text until a sentence is complete,
    translates the complete sentence to Turkish, and yields it.
    """
    translator = GoogleTranslator(source='en', target='tr')
    buffer = ""
    
    min_buffer_size = 50
    is_first_chunk = True
    
    for chunk in generator:
        buffer += chunk
        
        # Sadece buffer belirli bir büyüklüğe ulaştıysa veya paragraf sonuysa çeviri yap (API yükünü azaltmak için)
        if len(buffer) > min_buffer_size or '\n\n' in buffer:
            last_newline = buffer.rfind('\n')
            last_period = buffer.rfind('. ')
            last_bang = buffer.rfind('! ')
            last_question = buffer.rfind('? ')
            
            split_idx = max(last_newline, last_period, last_bang, last_question)
            
            if split_idx != -1:
                cut_point = split_idx + 1 if split_idx == last_newline else split_idx + 2
                
                text_to_translate = buffer[:cut_point]
                buffer = buffer[cut_point:]
                
                if text_to_translate.strip():
                    try:
                        translated = translator.translate(text_to_translate)
                        if text_to_translate.endswith('\n'):
                            translated += '\n'
                        else:
                            translated += ' '
                        yield translated
                        
                        # İlk cümle hızlıca ekrana düştükten sonra buffer'ı çok daha büyüt ki API hiç yorulmasın
                        if is_first_chunk:
                            min_buffer_size = 500
                            is_first_chunk = False
                            
                    except Exception:
                        yield text_to_translate
                else:
                    yield text_to_translate

    # Translate anything left in the buffer
    if buffer.strip():
        try:
            yield translator.translate(buffer)
        except Exception:
            yield buffer
