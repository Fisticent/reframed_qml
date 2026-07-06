"""
Auto-update silencieux : au démarrage (exe uniquement), vérifie la dernière
release GitHub et, si plus récente, télécharge le zip, remplace les fichiers
et relance l'app — sans rien demander à l'utilisateur.
"""

import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import zipfile

from constants import APP_VERSION, GITHUB_REPO, get_app_dir, log_exception

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _version_tuple(v):
    v = v.strip().lstrip("vV")
    parts = [p for p in v.split(".") if p.isdigit()]
    return tuple(int(p) for p in parts) or (0,)


def check_and_apply_update():
    """Ne fait rien en dev, hors ligne, ou si déjà à jour. Sinon télécharge, remplace et relance."""
    if not getattr(sys, "frozen", False):
        return
    try:
        req = urllib.request.Request(API_URL, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            release = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        log_exception("update check", e)
        return

    tag = release.get("tag_name", "")
    if not tag or _version_tuple(tag) <= _version_tuple(APP_VERSION):
        return

    asset = next((a for a in release.get("assets", []) if a["name"].endswith(".zip")), None)
    if not asset:
        return

    try:
        tmp_dir = tempfile.mkdtemp(prefix="reframed_update_")
        zip_path = os.path.join(tmp_dir, asset["name"])
        urllib.request.urlretrieve(asset["browser_download_url"], zip_path)

        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

        app_dir = get_app_dir()
        exe_name = os.path.basename(sys.executable)
        pid = os.getpid()

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
                f'xcopy /e /y /i "{extract_dir}\\*" "{app_dir}\\" >nul\r\n'
                f'start "" "{os.path.join(app_dir, exe_name)}"\r\n'
                f'rmdir /s /q "{tmp_dir}"\r\n'
            )
        subprocess.Popen(
            ["cmd", "/c", bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW,
            cwd=tmp_dir,
        )
        sys.exit(0)
    except Exception as e:
        log_exception("update apply", e)
