from app.document import Document


def split_documents(documents, chunk_size=700, overlap=150):
    chunks = []

    for doc in documents:
        text = doc.page_content

        if not text or not text.strip():
            continue

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        current_chunk = ""

        for paragraph in paragraphs:
            if len(paragraph) > chunk_size * 1.5:
                if current_chunk:
                    chunks.append(Document(page_content=current_chunk.strip(), metadata=doc.metadata))
                    current_chunk = ""
                
                words = paragraph.split(' ')
                start = 0
                while start < len(words):
                    # Count words until we reach roughly chunk_size characters
                    current_chunk_words = []
                    current_len = 0
                    idx = start
                    while idx < len(words) and current_len < chunk_size:
                        current_chunk_words.append(words[idx])
                        current_len += len(words[idx]) + 1 # +1 for space
                        idx += 1
                    
                    chunk_text = " ".join(current_chunk_words).strip()
                    if chunk_text:
                        chunks.append(Document(page_content=chunk_text, metadata=doc.metadata))
                    
                    # Calculate overlap in words roughly
                    overlap_words = overlap // 6 # assume 6 chars per word avg
                    start = max(start + 1, idx - overlap_words)
                continue
                
            if not current_chunk:
                current_chunk = paragraph
                continue
            
            if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                current_chunk += "\n\n" + paragraph
            else:
                chunks.append(
                    Document(
                        page_content=current_chunk.strip(),
                        metadata=doc.metadata
                    )
                )
                current_chunk = paragraph

        if current_chunk:
            chunks.append(
                Document(
                    page_content=current_chunk.strip(),
                    metadata=doc.metadata
                )
            )

    return chunks