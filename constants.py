import sys
import os
import ctypes

APP_VERSION = "1.0.0"
GITHUB_REPO = "Fisticent/reframed_qml"


def get_app_dir():
    """Répertoire de l'exe (PyInstaller) ou du projet (dev)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = get_app_dir()
    return os.path.join(base_path, relative_path)


def log_exception(context, exc):
    print(f"[REFRAMED] {context}: {exc}", file=sys.stderr)


BLOCKED_MOUSE_HOTKEY_PARTS = frozenset({"left_click", "right_click"})
BLOCKED_MOUSE_HOTKEY_MSG = (
    "⚠️ Clic gauche et clic droit sont interdits comme raccourcis "
    "(conflits avec le jeu). Utilisez une touche clavier ou la molette."
)


def hotkey_uses_blocked_mouse(value):
    if not value or not isinstance(value, str):
        return False
    parts = {p.strip().lower() for p in value.split("+") if p.strip()}
    return bool(parts & BLOCKED_MOUSE_HOTKEY_PARTS)


def sanitize_blocked_mouse_hotkeys(data):
    """Retire les raccourcis clic G/D au chargement (anciens profils)."""
    changed = False
    for key, value in list(data.items()):
        if not (key.endswith("_key") or key.endswith("_hotkey")):
            continue
        if hotkey_uses_blocked_mouse(value):
            data[key] = ""
            changed = True
    return changed


COLORS = {
    "bg": "#1e2128",
    "bg_card": "#262a33",
    "bg_elevated": "#2f3540",
    "text": "#e8eaed",
    "text_muted": "#8b95a5",
    "text_on_accent": "#1e2128",
    "primary": "#5a9e3e",
    "primary_hover": "#4a8532",
    "primary_bright": "#6db84a",
    "primary_button": "#3d6b28",
    "primary_button_hover": "#356024",
    "secondary": "#363d4a",
    "secondary_hover": "#424957",
    "secondary_dark": "#2a2f3a",
    "disabled_bg": "#2a2f3a",
    "success": "#4caf6a",
    "success_hover": "#3d9460",
    "danger": "#b83a32",
    "danger_hover": "#962f28",
    "warning": "#c4782a",
    "warning_hover": "#a86520",
    "calib": "#363d4a",
    "calib_hover": "#424957",
    "calib_border": "#c4782a",
    "team1": "#5a9e3e",
    "team1_hover": "#4a8532",
    "team2": "#8b4040",
    "team2_hover": "#723535",
    "leader": "#c4782a",
    "separator": "#363d4a",
    "focus_ring": "#8bc96e",
    "tooltip_bg": "#363d4a",
    "tooltip_fg": "#e8eaed",
    "toolbar_header": "#3d5a2a",
    "font_family": "Segoe UI",
    "font_size_ui": 12,
    "font_size_secondary": 11,
    "font_size_heading": 14,
    "font_size_title": 20,
    "radius_card": 8,
    "radius_control": 6,
    "radius_window": 10,
    "radial_accent": "#5a9e3e",
    "radial_hover": "#4a8532",
    "radial_active": "#3d5a2a",
    "radial_bg": "#262a33",
    "radial_outline": "#363d4a",
}


def get_work_area():
    """Zone utilisable de l'écran (exclut la barre des tâches)."""
    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", ctypes.c_long),
            ("top", ctypes.c_long),
            ("right", ctypes.c_long),
            ("bottom", ctypes.c_long),
        ]

    rect = RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
    return (
        rect.left,
        rect.top,
        rect.right - rect.left,
        rect.bottom - rect.top,
    )


AZERTY_TO_SCAN = {
    'a': 16, 'z': 17, 'e': 18, 'r': 19, 't': 20, 'y': 21, 'u': 22, 'i': 23, 'o': 24, 'p': 25,
    'q': 30, 's': 31, 'd': 32, 'f': 33, 'g': 34, 'h': 35, 'j': 36, 'k': 37, 'l': 38, 'm': 39,
    'w': 44, 'x': 45, 'c': 46, 'v': 47, 'b': 48, 'n': 49,
    '1': 2, '2': 3, '3': 4, '4': 5, '5': 6, '6': 7, '7': 8, '8': 9, '9': 10, '0': 11,
    'f1': 59, 'f2': 60, 'f3': 61, 'f4': 62, 'f5': 63, 'f6': 64,
    'f7': 65, 'f8': 66, 'f9': 67, 'f10': 68, 'f11': 87, 'f12': 88,
    'tab': 15, 'enter': 28, 'space': 57, 'esc': 1, 'backspace': 14,
    '²': 41, '&': 2, 'é': 3, '"': 4, "'": 5, '(': 6, '-': 7,
    'è': 8, '_': 9, 'ç': 10, 'à': 11, ')': 12, '=': 13,
    'num 1': 79, 'num 2': 80, 'num 3': 81, 'num 4': 75, 'num 5': 76,
    'num 6': 77, 'num 7': 71, 'num 8': 72, 'num 9': 73, 'num 0': 82,
}

SCAN_TO_AZERTY = {v: k for k, v in AZERTY_TO_SCAN.items()}
