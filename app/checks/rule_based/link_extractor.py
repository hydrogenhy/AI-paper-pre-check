import re
from typing import List, Dict, Any


def _join_wrapped_urls(text: str) -> str:
    """Heuristically join URLs split by line breaks."""
    # Handle protocol split like "https:\n//example.com"
    text = re.sub(r"(https?):\s*[\r\n]+\s*//", r"\1://", text)
    text = re.sub(r"(http):\s*[\r\n]+\s*//", r"\1://", text)

    pattern = re.compile(
        r'(https?://[^\s\)<>\[\]{}"\']+)\s*[\r\n]+\s*([^\s\)<>\[\]{}"\']+)'
    )

    def repl(match: re.Match) -> str:
        left = match.group(1)
        right = match.group(2)
        if not left or not right:
            return match.group(0)
        if left[-1] in "/#?&=.-_":
            return left + right
        if right.startswith("www"):
            return left + right
        if any(ch in right for ch in "/#?&=.-_"):
            return left + right
        return left + " " + right

    prev = None
    while prev != text:
        prev = text
        text = pattern.sub(repl, text)
    return text


def _trim_sentence_artifacts(link: str) -> str:
    """Remove accidental sentence fragments appended to a URL."""
    # Trim common trailing punctuation first
    link = re.sub(r"[.,;:!?]+$", "", link)

    stopwords = {
        "do", "we", "it", "is", "are", "the", "this", "that", "these", "those",
        "a", "an", "and", "or", "but", "if", "in", "on", "at", "to", "for",
    }
    m = re.search(r"(.*)\.([A-Z][a-z]{1,6})$", link)
    if m:
        tail = m.group(2).lower()
        if tail in stopwords:
            return m.group(1)
    return link


def extract_http_links(text: str) -> List[str]:
    """Extract all HTTP/HTTPS links from text using regex.
    
    Args:
        text: Input text to search for links
        
    Returns:
        List of URLs found in the text
    """
    if not text:
        return []
    
    text = _join_wrapped_urls(text)

    # Regex pattern to match http:// or https:// URLs
    # Matches URLs with common TLDs and query parameters
    pattern = r'https?://[^\s\)<>\[\]{}"\']+'
    
    links = re.findall(pattern, text)
    
    # Remove trailing punctuation that's likely not part of URL
    cleaned_links = []
    for link in links:
        # Remove trailing punctuation: . , ; : ! ?
        link = _trim_sentence_artifacts(link)
        # Remove trailing closing brackets if unmatched
        while link and link[-1] in ')]}':
            link = link[:-1]
        if link:
            cleaned_links.append(link)
    
    return list(set(cleaned_links))  # Remove duplicates


def check_links_existence(text: str) -> Dict[str, Any]:
    """Check if HTTP links exist in text.

    Args:
        text: Text to check (typically full paper text)

    Returns:
        Dict with:
        - check_type: "links"
        - results: list of per-link findings or a message when empty
    """
    links = extract_http_links(text)
    if len(links) == 0:
        details = 'No HTTP/HTTPS links found in the manuscript.'
    else:
        details = [
            {
                "links": link,
                "risk": "Please use an anonymous repository and ensure no identifying information appears in the code." if "github" in link.lower() or "gitlab" in link.lower()
                        else "Be cautious of sharing links that may contain sensitive information.",
                "confidence": "high" if "github" in link.lower() or "gitlab" in link.lower() else "medium",
            }
            for link in links
        ]
        
        order = {"high": 0, "medium": 1, "low": 2, "unknown": 3,}
        details = sorted(details, key=lambda x: order.get(x["confidence"], 99))
    
    return {
        "check_type": "links",
        "results": details
    }
