import os
import uuid
from dotenv import load_dotenv
import hashlib
import requests
from pathlib import Path

try:
    import streamlit as st
except ImportError:
    st = None

load_dotenv()

# keep existing env variable names (unchanged)
SITE_ID = os.getenv("SITE_ID")  # optional fallback

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


def _create_site() -> dict:
    site_name = f"chat2site-{uuid.uuid4().hex[:6]}"

    r = requests.post(
        f"{NETLIFY_API}/sites",
        headers=_headers(),
        json={"name": site_name}
    )
    r.raise_for_status()
    return r.json()


def deploy_site(folder: str) -> str:
    """
    Deploys a folder to Netlify and returns the live URL
    """

    # 1️⃣ Create site automatically
    site = _create_site()
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

