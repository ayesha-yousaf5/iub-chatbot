import re


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"[ \t]+", " ", text)

    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)

    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", " ", text)

    text = re.sub(r"\.{4,}", "...", text)

    text = re.sub(r"-{4,}", "---", text)

    lines = [line.strip() for line in text.splitlines()]

    cleaned_lines = []

    for line in lines:
        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines).strip()