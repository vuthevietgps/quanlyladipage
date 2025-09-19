import re
from typing import Optional

HEAD_CLOSE_RE = re.compile(r"</head>", re.IGNORECASE)
BODY_CLOSE_RE = re.compile(r"</body>", re.IGNORECASE)
SUBDOMAIN_PATTERN = re.compile(r"^[a-z0-9-]{1,40}$")

# Placeholders: <!-- TRACKING_HEAD -->, <!-- TRACKING_BODY --> (case-insensitive, allow spaces)
PH_HEAD_RE = re.compile(r"<!--\s*TRACKING_HEAD\s*-->", re.IGNORECASE)
PH_BODY_RE = re.compile(r"<!--\s*TRACKING_BODY\s*-->", re.IGNORECASE)

# Previously injected blocks (for idempotency when re-injecting on update)
INJECTED_HEAD_BLOCK_RE = re.compile(
    r"<!--\s*Global\s+Site\s+Tag\s*-->.*?<!--\s*/Global\s+Site\s+Tag\s*-->",
    re.IGNORECASE | re.DOTALL,
)
INJECTED_BODY_BLOCK_RE = re.compile(
    r"<!--\s*Tracking\s+Codes\s*-->.*?<!--\s*/Tracking\s+Codes\s*-->",
    re.IGNORECASE | re.DOTALL,
)


def sanitize_subdomain(raw: str) -> Optional[str]:
    raw = raw.strip().lower()
    if SUBDOMAIN_PATTERN.match(raw):
        return raw
    return None


def inject_tracking(html: str, head_snippet: str, body_end_snippet: str) -> str:
    """
    Inject tracking snippets into HTML with support for placeholders.

    Insertion order:
    1) Remove any previously injected tracking blocks (bounded by comment markers)
    2) If placeholder <!-- TRACKING_HEAD --> exists, replace its first occurrence
       Else insert before </head> or prepend if no head tag
    3) If placeholder <!-- TRACKING_BODY --> exists, replace its first occurrence
       Else insert before </body> or append if no body tag
    """
    # 1) Remove previously injected blocks for idempotency
    html = INJECTED_HEAD_BLOCK_RE.sub("", html)
    html = INJECTED_BODY_BLOCK_RE.sub("", html)

    # 2) Head: placeholder > before </head> > prepend
    if PH_HEAD_RE.search(html):
        html = PH_HEAD_RE.sub(head_snippet, html, count=1)
    elif HEAD_CLOSE_RE.search(html):
        html = HEAD_CLOSE_RE.sub(head_snippet + "\n</head>", html, count=1)
    else:
        html = head_snippet + "\n" + html

    # 3) Body: placeholder > before </body> > append
    if PH_BODY_RE.search(html):
        html = PH_BODY_RE.sub(body_end_snippet, html, count=1)
    elif BODY_CLOSE_RE.search(html):
        html = BODY_CLOSE_RE.sub(body_end_snippet + "\n</body>", html, count=1)
    else:
        html = html + "\n" + body_end_snippet

    return html
