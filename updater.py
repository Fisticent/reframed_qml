"""
Auto-update silencieux : au démarrage (exe uniquement), vérifie la dernière
release GitHub et, si plus récente, télécharge le zip EN ARRIÈRE-PLAN pendant
que l'app tourne déjà normalement, puis remplace les fichiers et relance —
sans rien demander à l'utilisateur.
"""

import json
import os
import subprocess
import sys
import tempfile
import threading
import urllib.request
import zipfile

from constants import APP_VERSION, GITHUB_REPO, get_app_dir, log_exception

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
DOWNLOAD_TIMEOUT = 15  # secondes par opération réseau (connect/read), pas un total


def _version_tuple(v):
    v = v.strip().lstrip("vV")
    parts = [p for p in v.split(".") if p.isdigit()]
    return tuple(int(p) for p in parts) or (0,)


def check_update_available():
    """Vérification rapide (petit JSON, timeout court). Retourne la release GitHub si plus récente, sinon None."""
    if not getattr(sys, "frozen", False):
        return None
    try:
        req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            release = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log_exception("update check", e)
        return None

    tag = release.get("tag_name", "")
    if not tag or _version_tuple(tag) <= _version_tuple(APP_VERSION):
        return None

    asset = next((a for a in release.get("assets", []) if a["name"].endswith(".zip")), None)
    if not asset:
        return None

    release["_asset"] = asset
    return release


def download_and_apply_async(release, on_ready_to_quit):
    """Télécharge et applique la mise à jour dans un thread — n'appelle on_ready_to_quit
    (thread-safe, ex: un Signal Qt) que lorsque tout est prêt à être relancé."""

    def _worker():
        try:
            _download_and_apply(release)
            on_ready_to_quit()
        except Exception as e:
            log_exception("update apply", e)

    threading.Thread(target=_worker, daemon=True).start()


def _download_and_apply(release):
    asset = release["_asset"]
    tmp_dir = tempfile.mkdtemp(prefix="reframed_update_")
    zip_path = os.path.join(tmp_dir, asset["name"])

    req = urllib.request.Request(asset["browser_download_url"])
    with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp, open(zip_path, "wb") as out:
        while True:
            chunk = resp.read(1024 * 256)
            if not chunk:
                break
            out.write(chunk)

    extract_dir = os.path.join(tmp_dir, "extracted")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    app_dir = get_app_dir()
    exe_name = os.path.basename(sys.executable)
    pid = os.getpid()
    relaunch_args = " ".join(f'"{a}"' if " " in a else a for a in sys.argv[1:])

    bat_path = os.path.join(tmp_dir, "apply_update.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(
            "@echo off\r\n"
            ":wait\r\n"
            f'tasklist /fi "PID eq {pid}" | find "{pid}" >nul\r\n'
            "if not errorlevel 1 (\r\n"
            "    timeout /t 1 /nobreak >nul\r\n"
            "    goto wait\r\n"
            ")\r\n"
            f'if exist "{app_dir}\\_internal" rmdir /s /q "{app_dir}\\_internal"\r\n'
            f'xcopy /e /y /i "{extract_dir}\\*" "{app_dir}\\" >nul\r\n'
            f'start "" "{os.path.join(app_dir, exe_name)}" {relaunch_args}\r\n'
            f'rmdir /s /q "{tmp_dir}"\r\n'
        )
    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=subprocess.CREATE_NO_WINDOW,
        cwd=tmp_dir,
    )
