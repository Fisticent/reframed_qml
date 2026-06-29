"""
RadialController — pilote la roue radiale de focus.

Porte radial_menu.py (tkinter Canvas) vers une fenêtre QML translucide :
 - calcul de la tranche survolée à partir du curseur GLOBAL (win32), car la
   fenêtre est transparente aux entrées (le bouton souris est maintenu ailleurs)
 - sons hover / click via pygame
 - sélection au relâchement (hide)
L'état (items, hoveredIndex, position) est exposé à QML via Properties.
"""

import os
import math

import win32api
import win32con
import win32gui
from PySide6.QtCore import QObject, Signal, Property, QTimer
from PySide6.QtGui import QWindow

from constants import resource_path, log_exception, COLORS as C

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "hide")
try:
    import pygame
except Exception:
    pygame = None


class RadialController(QObject):
    itemsChanged = Signal()
    hoveredChanged = Signal()
    currentNameChanged = Signal()
    geometryChanged = Signal()
    openChanged = Signal()

    SIZE = 400
    RADIUS_OUTER = 175
    RADIUS_INNER = 35

    def __init__(self, on_select_callback, parent=None):
        super().__init__(parent)
        self.on_select_callback = on_select_callback
        self._items = []
        self._hovered = -1
        self._current_name = ""
        self._pos_x = 0
        self._pos_y = 0
        self._is_open = False
        self.base_volume = 0.5
        self.scale = 1.0   # devicePixelRatio : curseur win32 (physique) -> Qt (logique)
        self._window = None

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._update_hover)

        self.mixer_active = False
        self.sound_hover = None
        self.sound_click = None
        if pygame is not None:
            try:
                pygame.mixer.init()
                self.mixer_active = True
                hp = resource_path("sounds/hover.wav")
                cp = resource_path("sounds/click.wav")
                self.sound_hover = pygame.mixer.Sound(hp) if os.path.exists(hp) else None
                self.sound_click = pygame.mixer.Sound(cp) if os.path.exists(cp) else None
                self.set_base_volume(0.5)
            except Exception as e:
                log_exception("radial sound init", e)
                self.mixer_active = False

    def set_scale(self, scale):
        self.scale = scale if scale and scale > 0 else 1.0

    # ---- volume ----
    def set_base_volume(self, volume):
        self.base_volume = volume
        if self.mixer_active:
            if self.sound_hover:
                self.sound_hover.set_volume(0.3 * self.base_volume)
            if self.sound_click:
                self.sound_click.set_volume(0.8 * self.base_volume)

    # ---- propriétés QML ----
    def _get_items(self):
        return self._items

    items = Property("QVariantList", _get_items, notify=itemsChanged)

    def _get_hovered(self):
        return self._hovered

    hoveredIndex = Property(int, _get_hovered, notify=hoveredChanged)

    def _get_current(self):
        return self._current_name

    currentName = Property(str, _get_current, notify=currentNameChanged)

    def _get_px(self):
        return self._pos_x

    posX = Property(int, _get_px, notify=geometryChanged)

    def _get_py(self):
        return self._pos_y

    posY = Property(int, _get_py, notify=geometryChanged)

    def _get_size(self):
        return self.SIZE

    wheelSize = Property(int, _get_size, constant=True)

    def _get_inner(self):
        return self.RADIUS_INNER

    radiusInner = Property(int, _get_inner, constant=True)

    def _get_outer(self):
        return self.RADIUS_OUTER

    radiusOuter = Property(int, _get_outer, constant=True)

    def _get_open(self):
        return self._is_open

    isOpen = Property(bool, _get_open, notify=openChanged)

    def _get_colors(self):
        return dict(C)

    colors = Property("QVariantMap", _get_colors, constant=True)

    def set_window(self, window):
        """Fenêtre QML RadialMenu — pour HWND_TOPMOST au-dessus du jeu."""
        if isinstance(window, QWindow):
            self._window = window

    def _ensure_topmost(self):
        if not self._is_open or not self._window:
            return
        try:
            hwnd = int(self._window.winId())
            if hwnd:
                win32gui.SetWindowPos(
                    hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE,
                )
        except Exception as e:
            log_exception("radial topmost", e)

    # ---- show / hide (appelés sur le thread GUI via queued signals) ----
    def show(self, x, y, items, current_name=""):
        if not items:
            return
        rows = []
        for it in items:
            classe = it.get("classe", "Inconnu")
            clean = classe.lower().replace("é", "e").replace("è", "e").replace("â", "a")
            path = resource_path(f"skin/{clean}.png")
            from PySide6.QtCore import QUrl
            icon = QUrl.fromLocalFile(path).toString() if os.path.exists(path) else ""
            rows.append({"name": it.get("name", ""), "classe": classe, "icon": icon})
        self._items = rows
        self.itemsChanged.emit()
        self._current_name = current_name or ""
        self.currentNameChanged.emit()
        # curseur en pixels physiques -> coordonnées logiques Qt
        lx = x / self.scale
        ly = y / self.scale
        self._pos_x = int(lx - self.SIZE / 2)
        self._pos_y = int(ly - self.SIZE / 2)
        self.geometryChanged.emit()
        self._hovered = -1
        self.hoveredChanged.emit()
        self._is_open = True
        self.openChanged.emit()
        self._timer.start()
        self._ensure_topmost()

    def hide(self):
        if not self._is_open:
            return
        self._is_open = False
        self.openChanged.emit()
        self._timer.stop()
        if 0 <= self._hovered < len(self._items):
            if self.mixer_active and self.sound_click:
                self.sound_click.play()
            selected = self._items[self._hovered]["name"]
            if self.on_select_callback:
                self.on_select_callback(selected)

    # ---- hover polling (curseur global) ----
    def _update_hover(self):
        if not self._is_open or not self._items:
            return
        self._ensure_topmost()
        try:
            mx, my = win32api.GetCursorPos()
        except Exception:
            return
        # curseur physique -> logique pour rester cohérent avec posX/posY
        mx /= self.scale
        my /= self.scale
        cx = self._pos_x + self.SIZE / 2
        cy = self._pos_y + self.SIZE / 2
        dist = math.hypot(mx - cx, my - cy)
        if dist < self.RADIUS_INNER or dist > self.RADIUS_OUTER:
            self._set_hovered(-1)
        else:
            dx = mx - cx
            dy = my - cy
            cw_angle = (math.degrees(math.atan2(dx, -dy)) + 360) % 360
            per = 360 / len(self._items)
            self._set_hovered(int(cw_angle // per))

    def _set_hovered(self, index):
        if index == self._hovered:
            return
        self._hovered = index
        if index != -1 and self.mixer_active and self.sound_hover:
            self.sound_hover.play()
        self.hoveredChanged.emit()
