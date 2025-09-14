#!/usr/bin/env python3
import os
import requests

SLUGS_FILE = "static/logos_to_fetch.txt"
OUT_DIR = "static/logos"

def load_slugs():
    if os.path.exists(SLUGS_FILE):
        with open(SLUGS_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip() and not line.lstrip().startswith("#")]
    return ["github", "python", "react", "node.js", "docker"]

def fetch_slug(slug):
    url = f"https://cdn.simpleicons.org/{slug}"
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 200 and "svg" in r.headers.get("content-type", ""):
            return r.text
    except Exception:
        pass
    return None

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    slugs = load_slugs()
    for slug in slugs:
        print(f"Fetching {slug} ...", end=" ")
        svg = fetch_slug(slug)
        if svg:
            path = os.path.join(OUT_DIR, f"{slug}.svg")
            with open(path, "w", encoding="utf-8") as f:
                f.write(svg)
            print("OK")
        else:
            print("Not found or error")

if __name__ == "__main__":
    main()
