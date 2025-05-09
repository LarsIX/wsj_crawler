import re

# === NYT-specific regex patterns for cleaning ===
patterns_to_remove = [
    # UI / Metadata
    r'\bADVERTISEMENT\b', r'\bSKIP ADVERTISEMENT\b', r'\bSKIP\b',
    r'\bShare full article\b', r'\bRead \d+ COMMENTS\b', r'See more on:.*?(?=\n|$)',
    r'Order Reprints \| Today[’\']s Paper \| Subscribe.*?(?=\n|$)',
    r'\bThe gift that says.*?The\. New\. York\. Times\.*',

    # Navigation junk
    r'\bSHARE\b.*?', r'\bSAVE\b.*?', r'\bTEXT\b.*?',
    r'^\s*\d+\s*$', r'^Credit.*?\n', r'^\s*Image\s*$', r'^\s*Video\s*$',

    # Author/date lines
    r'^\s*By\s+[\w\s\.\-]+\n?', 
    r'Published\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}',
    r'Updated\s+[A-Za-z]+\s+\d{1,2},\s+\d{4}',

    # Abridged or stylized attribution ending
    r'A version of this article appears in print.*?(?=\n|$)',
    r'on\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},\s+\d{4},?\s+Section.*?New York edition.*?headline.*?\.',

    # Author bio blurbs at the end
    r'\bReporting was contributed by\b.*?(?=\n|$)',
    r'(?:[A-Z][a-z]+\s){1,3}(is|was)\s(a|an).*?The\. New\. York\. Times\.',
    r'[A-Z][a-z]+\s(for|of|at)\sThe\. New\. York\. Times.*?\n',
    r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s+is a Times reporter.*?covering.*?\.',
    r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\s+is an? [^.]+? based in [^.]+\..*?covering.*?\.',

    # Print edition ID blocks
    r'\bThe\. New\. York\. Times(?:\.\.\.)*',

    # General stylized attribution lines with publication dates
    r'(?:[A-Z][a-z]+\.\s*){1,6}(?:for\.|of\.|by\.) The\. New\. York\. Times\.(?: Published\.\s+[A-Z][a-z]+\.\s+\d{1,2},\s+\d{4}\.)?(?: Updated\.\s+[A-Z][a-z]+\.\s+\d{1,2},\s+\d{4}\.)?',

    # City prefix + author name attribution
    r'(?:[A-Z][a-z]+\.\s*){1,3}(?:City\.\s*)?(?:[A-Z][a-z]+\.\s*){1,6}(?:for\.|of\.|by\.) The\. New\. York\. Times\.(?: Published\.\s+[A-Z][a-z]+\.\s+\d{1,2},\s+\d{4}\.)?(?: Updated\.\s+[A-Z][a-z]+\.\s+\d{1,2},\s+\d{4}\.)?',

    # Getty or agency image credit with date
    r'\bGetty\. Images\.\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.\s+\d{1,2},\s+\d{4}\.',
    r'\b[A-Z][a-z]+\.\s+[A-Z][a-z]+\s+for\. The\. New\. York\. Times\.\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.\s+\d{1,2},\s+\d{4}\.',

    # Excess whitespace
    r'\n{3,}', r'\s{2,}'

    # Author blurbs with city prefix
    r'(?:[A-Z][a-z]+\.\s*){1,5}for\.?\s+(?:The\.?\s+)?New\.?\s+York\.?\s+Times\s*,?\s*2024\.?(?:\s*Updated\.?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},\s+2024\.?)?'
    r'(?:[A-Z][a-z]+\.\s*){1,5}(?:for\.|of\.|by\.)\s+(?:The\.?\s+)?New\.?\s+York\.?\s+Times[.,]?\s*(?:Published\.?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},\s+2024\.?)?\s*(?:Updated\.?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},\s+2024\.?)?'

]

compiled_patterns = [re.compile(p, flags=re.IGNORECASE | re.MULTILINE) for p in patterns_to_remove]

def clean_nyt_article(text: str) -> str:
    """Cleans NYT article text by removing ads, metadata, author blurbs, photo credits, and trailing clutter."""
    if not isinstance(text, str):
        return text

    for pattern in compiled_patterns:
        text = pattern.sub('', text)

    # Normalize quotation marks
    text = re.sub(r"[‘’´`]", "'", text)
    text = re.sub(r"[“”]", '"', text)

    # Strip non-standard symbols (emojis, stray unicode)
    text = re.sub(r"[^a-zA-Z0-9.,;!?\"'\n -]+", '', text)

    # Normalize spaces
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(r"^\s+|\s+$", "", text)

    # Flatten paragraphs, then re-insert missing sentence breaks
    text = text.replace('\n', ' ')
    text = re.sub(r"(?<![.!?])\s+(?=[A-Z])", ". ", text)

    return text.strip()
