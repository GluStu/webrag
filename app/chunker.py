from typing import List, Tuple
import tiktoken

def chunk_text_o200k(text: str, max_tokens: int = 700, overlap: int = 100) -> List[Tuple[str, int]]:

    enc = tiktoken.get_encoding("o200k_base")
    tokens = enc.encode(text)
    n = len(tokens)
    chunks: List[Tuple[str, int]] = []

    if n == 0:
        return chunks

    start = 0
    while start < n:
        end = min(start + max_tokens, n)
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append((chunk_text, len(chunk_tokens)))
        if end == n:
            break
        start = end - overlap

        if start < 0:
            start = 0
    return chunks