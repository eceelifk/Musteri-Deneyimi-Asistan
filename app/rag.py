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
YOUR TASK: Provide a highly engaging, helpful, and direct answer based ONLY on the provided English PRODUCT REVIEWS.

{SYSTEM_PROMPT}

ADDITIONAL RULES FOR REVIEWS:
1. CRITICAL: First check if the retrieved context actually talks about the specific product or topic the user is asking about. If it does NOT, you MUST say exactly: "I do not have any information regarding this product in my database." and NOTHING else. Do not give a star rating.
2. If the context IS relevant, write a very comprehensive, detailed, and visually appealing explanation of what customers experienced.
3. Feel free to use bold text, bullet points, numbers, and markdown formatting to make the answer easy to read and detailed.
4. CRITICAL: DO NOT use the word "reviews". Instead, say "Customers mentioned" or "People said".
5. At the end, estimate a star rating like this: "Estimated Rating: 4/5 stars".
6. Start directly with the core answer. Do not use introductory phrases."""
        
        user_prompt = f"""Context:
{context}

Chat History:
{memory_context}

Customer: {english_query}

Please write exactly one short paragraph summarizing the reviews. End your paragraph with an estimated star rating out of 5 based on the overall sentiment (e.g., Estimated Rating: 4/5 stars). DO NOT use any introductory labels.
"""
    else:
        system_instruction = f"""You are Amazon's Customer Advisor.
YOUR TASK: Answer the user's question based ONLY on the provided English DOCUMENT CONTEXT.

{SYSTEM_PROMPT}

ADDITIONAL RULES FOR FAQ:
1. CRITICAL: If the provided context does not explicitly contain the answer to the user's question, you MUST say exactly: "I do not have any information regarding this question in my database." and NOTHING else.
2. If it is relevant, write naturally and provide detailed, comprehensive, and helpful information.
3. If giving instructions, write them out as a clear, step-by-step list using numbers or bullet points. Use bold text for key terms.
4. Make the formatting visually appealing and extremely easy to read using markdown.
5. Start your response IMMEDIATELY with the direct answer. DO NOT say "Based on the context" or "Here is the information".
"""
        user_prompt = f"""Context:
{context}

Chat History:
{memory_context}

Customer: {english_query}

Provide a clear and direct answer based on the context. Write a single, plain paragraph. DO NOT use lists, numbers, or bullet points. Stop generating once the question is fully answered.
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
                        
                # Loop detection using visible_answer
                if len(visible_answer) > 100:
                    import re
                    clean_text = re.sub(r'[^a-zA-ZğüşıöçĞÜŞİÖÇ\s]', '', visible_answer.lower())
                    words = clean_text.split()
                    for i in range(4, 100):
                        if loop_detected: break
                        for j in range(max(0, len(words) - i * 3), len(words) - i * 3 + 1):
                            if words[j:j+i] == words[j+i:j+2*i] == words[j+2*i:j+3*i]:
                                loop_detected = True
                                break
                if loop_detected:
                    yield "\n\n... (Aynı cümlelerin tekrar ettiği algılandığı için otomatik olarak kesildi. Başka bir sorunuz varsa lütfen sorun.)"
                    yielded_anything = True
                    break

            if line_buffer.strip():
                yield line_buffer
                yielded_anything = True
            elif line_buffer:
                yield line_buffer

            if not yielded_anything:
                yield NOT_FOUND_TR

        return {
            "answer_stream": translate_stream_en_to_tr(realtime_stream()),
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