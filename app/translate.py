from transformers import MarianMTModel, MarianTokenizer
import re

# Global variables for lazy loading the models (so they only load once)
_en_tr_model = None
_en_tr_tokenizer = None
_tr_en_model = None
_tr_en_tokenizer = None

def _get_en_tr():
    global _en_tr_model, _en_tr_tokenizer
    if _en_tr_model is None:
        print("Loading EN->TR offline model...")
        model_name = "Helsinki-NLP/opus-tatoeba-en-tr"
        _en_tr_tokenizer = MarianTokenizer.from_pretrained(model_name)
        _en_tr_model = MarianMTModel.from_pretrained(model_name)
    return _en_tr_model, _en_tr_tokenizer

def _get_tr_en():
    global _tr_en_model, _tr_en_tokenizer
    if _tr_en_model is None:
        print("Loading TR->EN offline model...")
        model_name = "Helsinki-NLP/opus-mt-tr-en"
        _tr_en_tokenizer = MarianTokenizer.from_pretrained(model_name)
        _tr_en_model = MarianMTModel.from_pretrained(model_name)
    return _tr_en_model, _tr_en_tokenizer

def translate_tr_to_en(text):
    if not text or not text.strip():
        return text
    try:
        model, tokenizer = _get_tr_en()
        encoded = tokenizer(text, return_tensors="pt", padding=True)
        translated = model.generate(**encoded)
        return tokenizer.decode(translated[0], skip_special_tokens=True)
    except Exception as e:
        print(f"Offline Çeviri hatası (TR->EN): {e}")
        return text

def translate_en_to_tr(text):
    if not text or not text.strip():
        return text
    try:
        model, tokenizer = _get_en_tr()
        encoded = tokenizer(text, return_tensors="pt", padding=True)
        translated = model.generate(**encoded)
        return tokenizer.decode(translated[0], skip_special_tokens=True)
    except Exception as e:
        print(f"Offline Çeviri hatası (EN->TR): {e}")
        return text

def translate_stream_en_to_tr(generator):
    """
    Takes an English text generator (stream), buffers text until a sentence is complete,
    translates the complete sentence to Turkish using local MarianMT, and yields it.
    """
    buffer = ""
    min_buffer_size = 50
    is_first_chunk = True
    
    for chunk in generator:
        buffer += chunk
        
        # Sadece buffer belirli bir büyüklüğe ulaştıysa veya paragraf sonuysa çeviri yap
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
                        translated = translate_en_to_tr(text_to_translate)
                        if text_to_translate.endswith('\n'):
                            translated += '\n'
                        else:
                            translated += ' '
                        yield translated
                        
                        if is_first_chunk:
                            min_buffer_size = 300
                            is_first_chunk = False
                            
                    except Exception:
                        yield text_to_translate
                else:
                    yield text_to_translate

    # Translate anything left in the buffer
    if buffer.strip():
        try:
            yield translate_en_to_tr(buffer)
        except Exception:
            yield buffer
