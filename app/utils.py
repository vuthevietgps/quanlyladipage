import re
from typing import Optional

HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)
BODY_CLOSE_RE = re.compile(r"</body>", re.IGNORECASE)
SUBDOMAIN_PATTERN = re.compile(r"^[a-z0-9-]{1,40}$")


def sanitize_subdomain(raw: str) -> Optional[str]:
    raw = raw.strip().lower()
    if SUBDOMAIN_PATTERN.match(raw):
        return raw
    return None


def inject_tracking(html: str, head_snippet: str, body_end_snippet: str) -> str:
    if HEAD_CLOSE_RE.search(html):
        html = HEAD_CLOSE_RE.sub(head_snippet + '\n</head>', html, count=1)
    else:
        # If no head tag, prepend
        html = head_snippet + '\n' + html

    if BODY_CLOSE_RE.search(html):
        html = BODY_CLOSE_RE.sub(body_end_snippet + '\n</body>', html, count=1)
    else:
        html = html + '\n' + body_end_snippet
    return html
