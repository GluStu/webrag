# from typing import List
# from app.config import settings

# _SYSTEM_PROMPT = """You are a concise assistant. Use ONLY the provided context to answer the question.
# If the answer is not in the context, say you don't have enough information.
# Cite sources by their URL and chunk index when helpful."""

# def format_context(chunks: List[tuple[str, str, int]]) -> str:
#     lines = []
#     for text, url, idx in chunks:
#         # keep context bounded; truncation handled upstream by chunk size
#         lines.append(f"[{url}#chunk-{idx}] {text}")
#     return "\n\n".join(lines[:10])  # cap to 10 chunks max in prompt

# def answer_with_llm(query: str, chunks: List[tuple[str, str, int]]) -> tuple[str, bool]:
#     """
#     Returns (answer, used_llm: bool). If USE_LLM=1, returns extractive stitched answer-like text.
#     """
#     if not settings.USE_LLM or not settings.LLM_API_KEY:
#         # Fallback: simple extractive summary snippet
#         if not chunks:
#             return "I don't have enough information to answer that yet.", False
#         snippets = []
#         for text, url, idx in chunks[:5]:
#             snippets.append(f"From {url} (chunk {idx}): {text[:300]}{'…' if len(text) > 300 else ''}")
#         stitched = " | ".join(snippets)
#         return f"(No LLM) Relevant excerpts: {stitched}", False

#     # OpenAI path
#     try:
#         from openai import OpenAI
#         client = OpenAI(api_key=settings.LLM_API_KEY)

#         context = format_context(chunks)
#         msgs = [
#             {"role": "system", "content": _SYSTEM_PROMPT},
#             {"role": "user", "content": f"Question: {query}\n\nContext:\n{context}"},
#         ]
#         resp = client.chat.completions.create(
#             model=settings.OPENAI_MODEL,
#             messages=msgs,
#             temperature=0.2,
#         )
#         return resp.choices[0].message.content.strip(), True
#     except Exception as e:
#         return f"LLM error: {e}. Falling back to excerpts.", False

from typing import List, Tuple
from app.config import settings

_SYSTEM_PROMPT = """You are a concise assistant. Use ONLY the provided context to answer the question.
If the answer is not in the context, say you don't have enough information.
Cite sources by their URL and chunk index when helpful."""

def format_context(chunks: List[Tuple[str, str, int]]) -> str:
    formatted = []
    for text, url, idx in chunks:
        formatted.append(f"--- Document Chunk {idx} ---\nSource: {url}\nText: {text}\n")
    return "\n".join(formatted)



def answer_with_llm(query: str, chunks: List[Tuple[str, str, int]]) -> Tuple[str, bool]:

    if not settings.USE_LLM or not settings.LLM_API_KEY:
        if not chunks:
            return "I don't have enough information to answer that yet.", False
        snippets = []
        for text, url, idx in chunks[:3]:
            snippets.append(f"From {url} (chunk {idx}): {text[:300]}{'…' if len(text) > 300 else ''}")
        stitched = " | ".join(snippets)
        return f"(No LLM) Relevant excerpts: {stitched}", False

    # Gemini API path
    try:
        from google import genai
        client = genai.Client(api_key=settings.LLM_API_KEY)

        context = format_context(chunks)
        
        prompt = (
            f"{_SYSTEM_PROMPT}\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}"
        )
        
        resp = client.models.generate_content(
            model=settings.LLM_MODEL,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                temperature=0.2,
            ),
        )

        return resp.text.strip(), True
        
    except Exception as e:
        return f"LLM error: {e}. Falling back to excerpts.", False