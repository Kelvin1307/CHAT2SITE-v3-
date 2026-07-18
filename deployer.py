import os
import re
import random
import hashlib
from dotenv import load_dotenv
import requests
from pathlib import Path

try:
    import streamlit as st
except ImportError:
    st = None

load_dotenv()

# keep existing env variable names (unchanged)
SITE_ID = os.getenv("SITE_ID")  # optional fallback

SITE_SUFFIX_STATE: dict[str, dict] = {}

def get_netlify_auth_token() -> str:
    token = None
    if st is not None:
        try:
            token = st.secrets.get("NETLIFY_AUTH_TOKEN")
        except (FileNotFoundError, AttributeError):
            token = None

    token = token or os.getenv("NETLIFY_AUTH_TOKEN")
    if not token:
        raise RuntimeError("NETLIFY_AUTH_TOKEN is missing.")
    return token

NETLIFY_API = "https://api.netlify.com/api/v1"


def _headers():
    return {
        "Authorization": f"Bearer {get_netlify_auth_token()}",
        "Content-Type": "application/json"
    }


def _sha1(path: Path) -> str:
    h = hashlib.sha1()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _normalize_site_name(name: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "chat2site"


def _site_name_seed(name: str) -> int:
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _shuffle_pool(seed: int) -> list[int]:
    pool = list(range(1000, 10000))
    rnd = random.Random(seed)
    for i in range(len(pool) - 1, 0, -1):
        j = rnd.randint(0, i)
        pool[i], pool[j] = pool[j], pool[i]
    return pool


def _next_site_suffix(name: str) -> str:
    normalized = _normalize_site_name(name)
    state = SITE_SUFFIX_STATE.get(normalized)
    if state is None:
        state = {
            "name": normalized,
            "seed": _site_name_seed(normalized),
            "pool": _shuffle_pool(_site_name_seed(normalized)),
            "index": 0,
        }
        SITE_SUFFIX_STATE[normalized] = state

    if state["index"] >= len(state["pool"]):
        state["seed"] += 1
        state["pool"] = _shuffle_pool(state["seed"])
        state["index"] = 0

    suffix = state["pool"][state["index"]]
    state["index"] += 1
    return f"{suffix:04d}"


def _create_site(business_name: str | None = None) -> dict:
    normalized_name = _normalize_site_name(business_name or "chat2site")
    suffix = _next_site_suffix(normalized_name)
    site_name = f"{normalized_name}-{suffix}"

    r = requests.post(
        f"{NETLIFY_API}/sites",
        headers=_headers(),
        json={"name": site_name}
    )
    r.raise_for_status()
    return r.json()


def deploy_site(folder: str, business_name: str | None = None) -> str:
    """
    Deploys a folder to Netlify and returns the live URL
    """

    # 1️⃣ Create site automatically
    site = _create_site(business_name=business_name)
    site_id = site["id"]
    site_url = site["url"]

    # 2️⃣ Collect files + hashes
    files = {}
    base = Path(folder)

    for path in base.rglob("*"):
        if path.is_file():
            rel = "/" + str(path.relative_to(base)).replace("\\", "/")
            files[rel] = _sha1(path)

    # 3️⃣ Create deploy
    r = requests.post(
        f"{NETLIFY_API}/sites/{site_id}/deploys",
        headers=_headers(),
        json={"files": files}
    )
    r.raise_for_status()
    deploy = r.json()

    deploy_id = deploy["id"]
    required = deploy.get("required", [])

    # reverse map: hash → filepath
    hash_to_path = {v: k for k, v in files.items()}

    for file_hash in required:
        rel_path = hash_to_path.get(file_hash)
        if not rel_path:
            continue

        full_path = base / rel_path.lstrip("/")
        if not full_path.exists():
            continue

        with open(full_path, "rb") as f:
            requests.put(
                f"{NETLIFY_API}/deploys/{deploy_id}/files/{file_hash}",
                headers={"Authorization": f"Bearer {get_netlify_auth_token()}"},
                data=f.read()
            )


    return site_url

