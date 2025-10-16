import httpx
from bs4 import BeautifulSoup
import trafilatura
from tenacity import retry, wait_exponential, stop_after_attempt

# DEFAULT_HEADERS = {
#     "User-Agent": "RAGWebBot/1.0 (+https://github.com/yourname/rag-web)"
# }

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
def fetch_url(url: str, timeout: float = 15.0) -> tuple[str | None, str | None]:
    """
    Returns (text, title). Uses trafilatura; falls back to simple BS4 cleaned text.
    """
    downloaded = trafilatura.fetch_url(url)
    if downloaded:
        extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        if extracted:
            # Trafilatura doesn't always return title; fetch HEAD/HTML to get one.
            try:
                with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                    r = client.get(url)
                    r.raise_for_status()
                    soup = BeautifulSoup(r.text, "html.parser")
                    title = soup.title.string.strip() if soup.title and soup.title.string else None
            except Exception:
                title = None
            return extracted, title

    # fallback: basic fetch + clean
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        r = client.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = " ".join(soup.get_text(separator=" ").split())
        title = soup.title.string.strip() if soup.title and soup.title.string else None
        return text, title