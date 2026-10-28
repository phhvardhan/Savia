import re

FILE_HEADER_RE = re.compile(r"^===== FILE \d+ of \d+: .* =====$", re.MULTILINE)


def split_files(text: str) -> list[str]:
    starts = [m.start() for m in FILE_HEADER_RE.finditer(text)]
    if len(starts) < 2:
        return [text]
    return [text[a:b] for a, b in zip(starts, starts[1:] + [len(text)])]


def fit_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    parts = split_files(text)
    if len(parts) < 2:
        return text[:limit]
    budget, remaining = limit, len(parts)
    shares = {}
    for i in sorted(range(len(parts)), key=lambda i: len(parts[i])):
        shares[i] = min(len(parts[i]), budget // remaining)
        budget -= shares[i]
        remaining -= 1
    return "\n".join(
        parts[i][: shares[i]] + ("\n[...rest of this file omitted for length...]" if shares[i] < len(parts[i]) else "")
        for i in range(len(parts))
    )


def chunk_text(text: str, size: int) -> list[str]:
    chunks: list[str] = []
    for part in split_files(text):
        header = part.splitlines()[0] if FILE_HEADER_RE.match(part) else ""
        start = 0
        while start < len(part):
            end = min(start + size, len(part))
            if end < len(part):
                cut = max(part.rfind("\n\n", start, end), part.rfind("\n", start, end), part.rfind(". ", start, end))
                if cut > start + size // 2:
                    end = cut + 1
            piece = part[start:end].strip()
            if piece:
                chunks.append(piece if not header or piece.startswith(header) else f"{header}\n{piece}")
            start = end
    return chunks


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()
