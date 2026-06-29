import copy
import json
import os
import shutil
import sys

from constants import get_app_dir, log_exception


def default_settings_data():
    return {
        "prev_key": "tab",
        "next_key": "²",
        "leader_key": "f1",
        "sync_key": "f3",
        "sync_right_key": "",
        "swap_xp_drop_key": "",
        "toggle_app_key": "f10",
        "paste_enter_key": "",
        "auto_zaap_key": "",
        "refresh_key": "f5",
        "calib_key": "f4",
        "sort_taskbar_key": "",
        "invite_group_key": "",
        "zaap_delay": "1.0",
        "game_inv_key": "i",
        "game_char_key": "c",
        "game_spell_key": "s",
        "game_haven_key": "h",
        "radial_menu_active": True,
        "radial_menu_hotkey": "alt+left_click",
        "leader_name": "",
        "accounts_state": {},
        "accounts_team": {},
        "current_mode": "ALL",
        "classes": {},
        "auto_accept_trade": False,
        "auto_group_accept": False,
        "custom_order": [],
        "macro_positions": {
            "chat_position": None,
            "xp_drop_button": None,
            "group_accept_button": None,
            "trade_accept_button": [0.58645833, 0.53022795],
            "zaaps": {},
        },
        "advanced_bind_mode": "cycle",
        "persistent_character_binds": {},
        "cycle_row_binds": [
            "ctrl+F1",
            "ctrl+F2",
            "ctrl+F3",
            "ctrl+F4",
            "ctrl+F5",
            "ctrl+F6",
            "ctrl+F7",
            "ctrl+F8",
        ],
        "click_speed": "Lent",
        "toolbar_active": False,
        "spam_click_active": False,
        "return_to_leader": True,
        "show_tooltips": True,
        "toolbar_x": 100,
        "toolbar_y": 100,
        "window_x": None,
        "window_y": None,
        "volume_level": 50,
        "ignore_organizer_warning": False,
    }


def get_settings_dir():
    """Dossier de settings : AppData (exe) ou racine projet (dev)."""
    if getattr(sys, "frozen", False):
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return os.path.join(base, "Reframed")
    return get_app_dir()


def default_settings_path():
    return os.path.join(get_settings_dir(), "settings.json")


def _is_reframed_settings(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return isinstance(data, dict) and (
            "macro_positions" in data or "prev_key" in data or "leader_name" in data
        )
    except Exception:
        return False


def _search_legacy_settings(exclude_path, max_depth=4):
    """Cherche un settings.json d'une install portable ailleurs sur le PC."""
    profile = os.environ.get("USERPROFILE", "")
    roots = [
        os.path.join(profile, "Desktop"),
        os.path.join(profile, "Documents"),
        os.path.join(profile, "Downloads"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    found = []

    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        root = os.path.normpath(root)
        for dirpath, dirnames, filenames in os.walk(root):
            depth = dirpath[len(root):].count(os.sep) if dirpath.startswith(root) else 0
            if depth > max_depth:
                dirnames.clear()
                continue
            dirnames[:] = [
                d for d in dirnames
                if d.lower() not in {"node_modules", ".git", "__pycache__", "build", "skin", "sounds"}
            ]
            if "settings.json" not in filenames:
                continue
            path = os.path.normpath(os.path.join(dirpath, "settings.json"))
            if path == exclude_path or path in found:
                continue
            if not _is_reframed_settings(path):
                continue
            has_exe = any(f.lower() == "reframed.exe" for f in filenames)
            found.append((path, os.path.getmtime(path), has_exe))

    if not found:
        return None
    found.sort(key=lambda item: (not item[2], -item[1]))
    return found[0][0]


def find_legacy_settings(exclude_path):
    """Chemins probables d'une ancienne install (portable ou dist/)."""
    app_dir = get_app_dir()
    parent = os.path.dirname(app_dir)

    fixed_candidates = [
        os.path.join(app_dir, "settings.json"),
        os.path.join(app_dir, "dist", "settings.json"),
        os.path.join(parent, "settings.json"),
        os.path.join(parent, "dist", "settings.json"),
    ]

    for path in fixed_candidates:
        path = os.path.normpath(path)
        if path != exclude_path and _is_reframed_settings(path):
            return path

    return _search_legacy_settings(exclude_path)


def migrate_legacy_settings(target_path):
    """Copie un ancien settings.json ; retourne la source ou None."""
    source = find_legacy_settings(os.path.normpath(target_path))
    if not source:
        return None
    try:
        target_dir = os.path.dirname(target_path)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        shutil.copy2(source, target_path)
        return source
    except Exception as e:
        log_exception(f"migration settings {source} -> {target_path}", e)
        return None


class Config:
    def __init__(self, filename=None):
        self.filename = filename or default_settings_path()
        self.migrated_from = None
        self.data = copy.deepcopy(default_settings_data())
        self.load()

    def load(self):
        if not os.path.exists(self.filename):
            self.migrated_from = migrate_legacy_settings(self.filename)

        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self.data.update(loaded)
            except Exception as e:
                log_exception(f"lecture {self.filename}", e)

    def save(self):
        try:
            settings_dir = os.path.dirname(self.filename)
            if settings_dir:
                os.makedirs(settings_dir, exist_ok=True)
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception as e:
            log_exception(f"écriture {self.filename}", e)

    def reset_settings(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)
        self.migrated_from = None
        self.data = copy.deepcopy(default_settings_data())
        self.save()
