"""Shared helpers: all network I/O goes through curl (honours the session proxy/CA)."""
import subprocess, pathlib, json, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
UA = "food-prices-research/1.0 (academic price-transmission study)"

def fetch(url, dest=None, timeout=300, retries=3):
    """Download url. Returns bytes; also writes to dest when given."""
    dest = pathlib.Path(dest) if dest else None
    if dest:
        dest.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for attempt in range(retries):
        cmd = ["curl", "-sS", "-L", "--compressed", "-A", UA,
               "--max-time", str(timeout), url]
        if dest:
            cmd += ["-o", str(dest)]
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0:
            return dest.read_bytes() if dest else r.stdout
        last = r.stderr.decode("utf-8", "replace")[:300]
        print(f"  retry {attempt+1}/{retries}: {last}", file=sys.stderr)
    raise RuntimeError(f"fetch failed: {url}\n{last}")

def fetch_json(url, dest=None, **kw):
    b = fetch(url, dest, **kw)
    return json.loads(b)
