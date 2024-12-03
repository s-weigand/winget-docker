# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx",
#     "python-dotenv",
#     "rich",
# ]
# ///
from pathlib import Path
import httpx
import os
from zipfile import ZipFile
from io import BytesIO
from typing import IO
from dotenv import load_dotenv

from rich.tree import Tree
from rich.console import Console

load_dotenv()
USE_CACHE = "CI" not in os.environ
REPO_ROOT =Path(__file__).parent
CACHE_DIR = REPO_ROOT / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

CACHED_WINGET_DL = CACHE_DIR / "winget.zip"

WINGET_VERSION = (REPO_ROOT/".version").read_text().strip()


EXTRACT_DIR = Path(__file__).parent / "winget_min_cli"
EXTRACT_DIR.mkdir(exist_ok=True)

MIN_CLI_FILES = ["winget.exe", "WindowsPackageManager.dll", "resources.pri"]


EXTRA_HEADERS = {}
# Needed for CI rate limits
gh_token = os.getenv("GH_TOKEN")
if gh_token is not None:
    EXTRA_HEADERS["Authorization"] = f"Bearer {gh_token}"

console = Console(force_terminal=True)

def fetch_download_url() -> str:
    """Fetch the bundle download url for the release with tag ``WINGET_VERSION``."""
    resp = httpx.get(
        "https://api.github.com/repos/microsoft/winget-cli/releases", headers=EXTRA_HEADERS
    )
    resp.raise_for_status()
    for release in resp.json():
        if release.get("tag_name", None) == WINGET_VERSION:
            for asset in release["assets"]:
                if asset["name"].endswith(".msixbundle"):
                    return asset["browser_download_url"]
    msg = "API response has unexpected shape."
    raise ValueError(msg)

def create_bundle_buffer() -> IO[bytes]:
    """Create buffer of the bundle either from cache or download."""
    if USE_CACHE is True and CACHED_WINGET_DL.is_file() is True:
        console.print(f"[blue]Using cached bundle: [dark_violet]{CACHED_WINGET_DL.as_posix()}")
        return BytesIO(CACHED_WINGET_DL.read_bytes())
    download_url = fetch_download_url()
    console.print(f"[yellow] Downloading new bundle from  [dark_violet]{download_url}")
    resp = httpx.get(download_url, follow_redirects=True, headers=EXTRA_HEADERS)
    resp.raise_for_status()
    if USE_CACHE is True:
        CACHED_WINGET_DL.write_bytes(resp.content)
    return BytesIO(resp.content)


def main() -> None:
    """Extract files minimal required files to run the winget cli

    Thanks to this answer
    https://github.com/microsoft/winget-cli/issues/3037#issuecomment-1579449533
    """
    tree = Tree(f"[green]{EXTRACT_DIR.name}")
    with ZipFile(create_bundle_buffer()) as outer_zip:
        console.print("[blue]Extracting CLI files from bundle")
        with outer_zip.open("AppInstaller_x64.msix") as inner_fd:
            with ZipFile(inner_fd) as inner_zip:
                # inner_zip.extractall(EXTRACT_DIR)
                for cli_file in MIN_CLI_FILES:
                    tree.add(f"[green]{cli_file}")
                    inner_zip.extract(cli_file, EXTRACT_DIR)
    console.print("[green]Done extracting")
    console.print(tree)

if __name__ == "__main__":
    main()
