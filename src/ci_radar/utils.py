import hashlib, csv

def stable_key(title: str, link: str) -> str:
    return hashlib.md5((title.strip() + link.strip()).encode("utf-8")).hexdigest()

def save_csv(rows, path):
    if not rows: return "no rows"
    keys = sorted({k for r in rows for k in r.keys()})
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)
    return f"saved {len(rows)} rows to {path}"
