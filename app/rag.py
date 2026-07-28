from app.llm import ask_llm
from app.retrieve import retrieve
from app.translate import translate_tr_to_en, translate_en_to_tr, translate_stream_en_to_tr
from app.memory import add_to_memory
from app.config import TOP_K, MINIMUM_SIMILARITY, SYSTEM_PROMPT


NOT_FOUND_TR = "Bunun hakkında bir bilgi bulunamadı."


def get_simulated_stream(text):
    import time
    for char in text:
        yield char
        time.sleep(0.005)

def is_small_talk(question: str) -> bool:
    normalized_question = question.lower().strip()
    greetings = {"merhaba", "selam", "hello", "hi", "hey", "naber", "nasılsın"}
    return normalized_question in greetings


def build_context(docs: list[dict]) -> str:
    context_parts = []
    for index, doc in enumerate(docs, start=1):
        chunk = doc["chunk"]
        context_parts.append(f"[INFORMATION {index}]\n{chunk}")
    return "\n\n".join(context_parts)

def ask(question_tr: str, filter_type: str = "all") -> dict:
    question_tr = question_tr.strip()

    if is_small_talk(question_tr):
        answer_tr = "Merhaba! Ben Amazon Müşteri Deneyimi ve SSS Danışmanıyım. Size nasıl yardımcı olabilirim?"
        return {"answer_stream": get_simulated_stream(answer_tr), "sources": []}

    from app.embedding import unload_embedding
    from app.memory import chat_history
    
    # Context-aware retrieval: if we have history, prepend the last question to the search query
    # to help the vector database find the right product when user says "this product"
    # Translate Turkish query to English for DB search
    english_query = translate_tr_to_en(question_tr)
    
    # SADECE VERİTABANINDA SEMANTİK OLARAK ARAYACAĞIZ (ASIN FİLTRESİ YOK)
    try:
        docs = retrieve(question=english_query, top_k=TOP_K, minimum_similarity=MINIMUM_SIMILARITY, filter_type=filter_type)
        unload_embedding()
    except Exception as error:
        print("Retrieval error:", error)
        docs = []

    if not docs:
        return {
            "answer_stream": get_simulated_stream(NOT_FOUND_TR),
            "sources": []
        }
        
    # (ASIN detection will be done after building the full context)

    if not docs:
        return {
            "answer_stream": get_simulated_stream(NOT_FOUND_TR),
            "sources": []
        }

    context = build_context(docs)
    
    # Kapsam sınırını aşmamak için bağlamı kırp (Yaklaşık 4000 karakter)
    if len(context) > 4000:
        context = context[:4000] + "\n... [Bağlam Kırpıldı]"

    from app.memory import get_memory_text
    memory_context = get_memory_text()
    
    full_text_for_asin = context + "\n\n" + memory_context
    detected_asins = []
    if filter_type == "review":
        import re
        matches = re.findall(r'\b([B0-9][A-Z0-9]{9})\b', full_text_for_asin)
        detected_asins = list(dict.fromkeys(matches))
    context = context + "\n\n" + memory_context
    
    if len(memory_context) > 1000:
        memory_context = "... [Geçmiş Kırpıldı]\n" + memory_context[-1000:]

    if filter_type == "review":
        system_instruction = f"""You are Amazon's expert Customer Advisor.
YOUR TASK: Provide a highly engaging, helpful, and direct answer based ONLY on the provided English PRODUCT REVIEWS or SPECS.

{SYSTEM_PROMPT}

ADDITIONAL RULES FOR REVIEWS:
1. IF the retrieved context does not talk about the specific product(s) requested by the user, output exactly: "I do not have any information regarding this product in my database." and nothing else.
2. For single product inquiries, ALWAYS include:
   - General features of the product based on the context.
   - A clear verdict on whether it should be bought or not (e.g. "Should you buy it? Yes/No" or "Alınır mı?").
3. For comparisons or "suggest a product" inquiries between multiple products, you MUST use this structure:
   - First, create a section for the First Product. Detail its features and user feedback.
   - Next, create a section for the Second Product. Detail its features and user feedback.
   - Finally, create a "Final Recommendation" section where you make a firm, clear selection on which one to choose.
4. Keep your answer focused. ALWAYS provide a response, never output an empty string.
5. DO NOT use the word "reviews". Instead say "Customers mentioned" or "Users noted".
6. At the very end of your response, provide exactly ONE star rating using ONLY emojis (e.g. ⭐⭐⭐⭐⭐). Do NOT output multiple star ratings or duplicate bullet points.
7. CRITICAL: Give your answer ONCE and STOP. Do NOT summarize your own answer at the end. Do NOT add a duplicate "Solution", "Conclusion", or "Çözüm" section if you already gave your recommendation.
"""
        
        user_prompt = f"""--- CONTEXT ---
{context}

--- CURRENT QUESTION ---
{english_query}

Answer the user's question directly based ONLY on the provided context. Make sure to include general features, a "should you buy it" verdict, and exactly ONE estimated star rating using emojis (⭐) at the very end. If comparing products, YOU MUST detail BOTH products FIRST before making your final selection. ONCE YOU PROVIDE THE RECOMMENDATION AND STAR RATING, YOU MUST STOP GENERATING IMMEDIATELY. DO NOT LOOP OR REPEAT YOURSELF.
"""
    else:
        system_instruction = f"""You are Amazon's Customer Advisor.
YOUR TASK: Answer the user's question based ONLY on the provided English DOCUMENT CONTEXT.

{SYSTEM_PROMPT}

ADDITIONAL RULES FOR FAQ:
1. IF the provided context does not explicitly contain the answer, YOU MUST output exactly: "I do not have any information regarding this question in my database." and nothing else.
2. ELSE (if it is relevant), provide helpful and concise information.
3. DO NOT repeat yourself. Keep it short.
4. Make the formatting easy to read.
"""
        user_prompt = f"""--- CONTEXT ---
{context}

--- CURRENT QUESTION ---
{english_query}

Provide a short, clear answer. DO NOT loop or repeat sentences. Stop when finished.
"""

    sources = list(dict.fromkeys(doc["source"] for doc in docs))

    try:
        def realtime_stream():
            buffer = ""
            in_think = False
            visible_answer = ""
            line_buffer = ""
            loop_detected = False
            yielded_anything = False

            for chunk in ask_llm(system_instruction, user_prompt):
                buffer += chunk
                
                while buffer:
                    if not in_think:
                        if "<think>" in buffer:
                            parts = buffer.split("<think>", 1)
                            line_buffer += parts[0]
                            buffer = parts[1]
                            in_think = True
                            continue
                        else:
                            possible_partial = False
                            for tag in ["<think>", "</think>"]:
                                for i in range(1, len(tag)):
                                    if buffer.endswith(tag[:i]):
                                        possible_partial = True
                                        line_buffer += buffer[:-i].replace("</think>", "")
                                        buffer = buffer[-i:]
                                        break
                                if possible_partial:
                                    break
                            
                            if not possible_partial:
                                line_buffer += buffer.replace("</think>", "")
                                buffer = ""
                            
                            while True:
                                n_idx = line_buffer.find("\n")
                                d_idx = line_buffer.find(". ")
                                
                                if n_idx == -1 and d_idx == -1:
                                    break
                                    
                                if n_idx != -1 and (d_idx == -1 or n_idx < d_idx):
                                    split_idx = n_idx
                                    delimiter = "\n"
                                else:
                                    split_idx = d_idx + 1
                                    delimiter = " "
                                
                                line = line_buffer[:split_idx]
                                line_buffer = line_buffer[split_idx + len(delimiter):]
                                
                                if line.strip():
                                    yield line + delimiter
                                    visible_answer += line + delimiter
                                    yielded_anything = True
                                else:
                                    yield delimiter
                                    visible_answer += delimiter
                            break
                    else:
                        if "</think>" in buffer:
                            parts = buffer.split("</think>", 1)
                            buffer = parts[1]
                            in_think = False
                            continue
                        else:
                            possible_partial = False
                            for i in range(1, len("</think>")):
                                if buffer.endswith("</think>"[:i]):
                                    possible_partial = True
                                    buffer = buffer[-i:]
                                    break
                                    
                            if not possible_partial:
                                buffer = ""
                            break
                        
                # Akıllı Tekrar Tespit Sistemi (Smart Repetition Detection)
                # Yeni bir satırın, bir önceki veya ondan önceki satırla aynı olup olmadığını kontrol eder
                import re
                lines = [line.strip() for line in visible_answer.split('\n') if line.strip()]
                if len(lines) >= 3:
                    # Rakamları ve noktalama işaretlerini temizleyerek sadece metne odaklan (Örn: "31. Fiyat" -> "fiyat")
                    clean_lines = [re.sub(r'^[\d\W]+', '', l).strip().lower() for l in lines]
                    last_line = clean_lines[-1]
                    
                    if len(last_line) > 5: # Çok kısa (boş) kelimeleri sayma
                        # Eğer son yazılan cümle, önceki 2 cümleden biriyle birebir aynıysa (döngü başladıysa)
                        if last_line == clean_lines[-2] or (len(clean_lines) >= 3 and last_line == clean_lines[-3]):
                            break # Sessizce kes, hata mesajı verme

            if line_buffer.strip():
                yield line_buffer
                yielded_anything = True
            elif line_buffer:
                yield line_buffer

            if not yielded_anything:
                yield "I could not find any information about this."

        # Log the output as well
        def logging_wrapper(generator):
            full_response = ""
            for chunk in generator:
                full_response += chunk
                yield chunk
            
            with open("chat_log.txt", "a", encoding="utf-8") as f:
                f.write(f"--- YENİ SORU ---\n")
                f.write(f"SORU (TR): {question_tr}\n")
                f.write(f"BULUNAN CONTEXT UZUNLUĞU: {len(context)}\n")
                f.write(f"CEVAP: {full_response}\n\n")

        return {
            "answer_stream": logging_wrapper(translate_stream_en_to_tr(realtime_stream())),
            "sources": sources,
            "asins": detected_asins if filter_type == "review" else []
        }

    except Exception as error:
        print("LLM error:", error)
        def error_stream():
            yield f"LLM Hatası: {error}"
        return {
            "answer_stream": error_stream(),
            "sources": sources
        }