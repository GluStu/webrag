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
