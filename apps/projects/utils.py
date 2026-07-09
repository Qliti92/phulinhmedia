import re
from urllib.parse import urlparse


DOMAIN_RE = re.compile(r"^(?!-)([a-z0-9-]{1,63}\.)+[a-z]{2,63}$")


def normalize_domain(value):
    raw = (value or "").strip().lower()
    if not raw:
        return ""
    parsed = urlparse(raw if "://" in raw else f"http://{raw}")
    host = parsed.netloc or parsed.path.split("/")[0]
    if host.startswith("www."):
        host = host[4:]
    return host.split(":")[0].strip(".")


def is_valid_domain(domain):
    return bool(DOMAIN_RE.match(domain or ""))
