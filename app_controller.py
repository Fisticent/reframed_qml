"""
AppController — pont QObject entre la logique Win32 (logic.py) et l'UI QML.

Porte l'intégralité de la classe OrganizerApp d'origine :
 - enregistrement / écoute des hotkeys globaux (keyboard + win32)
 - background_listener (souris latérale, spam clic, roue radiale, sync focus)
 - system tray (QSystemTrayIcon)
 - calibrations et capture de touches
Le tout exposé à QML via Properties / Slots / Signals (thread-safe par queued signals).
"""

import os
import sys
import time
import ctypes
import threading
import subprocess

import keyboard
import win32api
import win32con
import win32gui

from PySide6.QtCore import QObject, Signal, Slot, Property, QTimer, QUrl, Qt
from PySide6.QtWidgets import QMessageBox

from constants import (
    resource_path,
    AZERTY_TO_SCAN,
    SCAN_TO_AZERTY,
    log_exception,
    COLORS as C,
    BLOCKED_MOUSE_HOTKEY_PARTS,
    BLOCKED_MOUSE_HOTKEY_MSG,
    hotkey_uses_blocked_mouse,
)
from config_manager import Config
from logic import DofusLogic


def _skin_url(classe):
    """URL de fichier (file:///) vers l'icône de classe, ou '' si absente."""
    if not classe:
        return ""
    clean = classe.lower().replace("é", "e").replace("è", "e").replace("â", "a")
    path = resource_path(f"skin/{clean}.png")
    if os.path.exists(path):
        return QUrl.fromLocalFile(path).toString()
    return ""


def _asset_url(rel):
    path = resource_path(rel)
    if os.path.exists(path):
        return QUrl.fromLocalFile(path).toString()
    return ""


def is_organizer_running():
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq organizer.exe", "/NH"],
            capture_output=True, text=True, creationflags=flags,
        )
    except Exception as e:
        log_exception("is_organizer_running", e)
        return False
    for line in result.stdout.splitlines():
        if line.strip().lower().startswith("organizer.exe"):
            return True
    return False


class AppController(QObject):
    # --- Signaux vers QML (thread-safe : queued automatiquement) ---
    accountsChanged = Signal()
    hotkeysChanged = Signal()
    feedbackChanged = Signal()
    currentModeChanged = Signal()
    volumeChanged = Signal()
    togglesChanged = Signal()
    calibChanged = Signal()
    listeningChanged = Signal()
    activeHighlightChanged = Signal(str)
    classDisplayChanged = Signal(str)
    temporaryMessage = Signal(str, str)         # text, color
    requestShowMain = Signal()
    requestHideMain = Signal()
    requestToggleMain = Signal()
    requestQuit = Signal()
    updateReadyToApply = Signal()        # thread-safe : update téléchargée en arrière-plan, prête à s'appliquer
    hotkeyCaptured = Signal(str, str)           # config_key, value
    radialShowRequested = Signal(int, int, list, str)
    radialHideRequested = Signal()
    conflictDetected = Signal()
    launchTutorialRequested = Signal()
    calibrationError = Signal(str)
    bindKeyCaptured = Signal(str, str)          # row_id, key
    calibInstruction = Signal(str)              # texte consigne calibrage
    calibInstructionHide = Signal()
    currentIndexChanged = Signal(int)           # thread-safe : index cycle depuis listener

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.logic = DofusLogic(self.config)
        self.logic.set_error_callback(self._on_logic_error)

        self._running = True
        self._current_idx = 0
        self._accounts = []
        self._feedback_text = ""
        self._feedback_color = C["primary_bright"]
        self._is_listening = False

        self.hotkey_actions = {}
        self.mouse_hotkeys = {}
        self.mouse_states = {}
        self._hotkey_down = set()
        self._spam_click_running = False

        self.tray_icon = None
        self.radial = None            # défini par main après création de l'engine
        self._feedback_timer = QTimer(self)
        self._feedback_timer.setSingleShot(True)
        self._feedback_timer.timeout.connect(self._clear_feedback)

        # Connexions queued pour les actions devant tourner sur le thread GUI
        self.temporaryMessage.connect(self._set_feedback)
        self.calibrationError.connect(self._show_calibration_error)
        self.currentIndexChanged.connect(self._apply_current_idx)

        self._listener_thread = None
        self._shutdown_done = False

    # ======================================================================
    #  Démarrage / cycle de vie
    # ======================================================================
    def start(self):
        """Démarre listener, hotkeys, scan initial, tutoriel, vérifs."""
        self._listener_thread = threading.Thread(target=self.background_listener, daemon=True)
        self._listener_thread.start()
        self.setup_hotkeys()
        self.refresh()

        if not self.config.data.get("tutorial_done", False):
            QTimer.singleShot(800, self.launchTutorialRequested.emit)

        if self.config.migrated_from:
            QTimer.singleShot(600, lambda: self.show_temporary_message(
                "✅ Configuration importée depuis l'ancienne installation.", C["primary_bright"]))

        QTimer.singleShot(1000, self.check_conflicting_software)
        QTimer.singleShot(500, self.start_shell_hook)

    def start_shell_hook(self):
        try:
            self.logic.start_shell_hook()
        except Exception as e:
            log_exception("start_shell_hook", e)

    def _sync_shell_hook(self):
        if self.logic.shell_hook_needed():
            self.start_shell_hook()
        else:
            self.logic.stop_shell_hook()

    # ======================================================================
    #  current_idx (highlight + classe overlay)
    # ======================================================================
    @property
    def current_idx(self):
        return self._current_idx

    @current_idx.setter
    def current_idx(self, value):
        self._current_idx = value
        if not self._running:
            return
        try:
            cycle_list = self.logic.get_cycle_list()
            if cycle_list and 0 <= value < len(cycle_list):
                c_name = cycle_list[value].get("classe", "Inconnu")
                self.classDisplayChanged.emit(c_name)
                self.activeHighlightChanged.emit(cycle_list[value].get("name", ""))
            else:
                self.activeHighlightChanged.emit("")
        except Exception as e:
            log_exception("current_idx update", e)

    @Slot(int)
    def _apply_current_idx(self, value):
        self.current_idx = value

    # ======================================================================
    #  Propriétés QML
    # ======================================================================
    def _get_accounts(self):
        return self._accounts

    accounts = Property("QVariantList", _get_accounts, notify=accountsChanged)

    def _get_hotkeys(self):
        keys = [k for k in self.config.data.keys()
                if k.endswith("_key") or k.endswith("_hotkey")]
        return {k: self.config.data.get(k, "") for k in keys}

    hotkeys = Property("QVariantMap", _get_hotkeys, notify=hotkeysChanged)

    def _get_feedback_text(self):
        return self._feedback_text

    feedbackText = Property(str, _get_feedback_text, notify=feedbackChanged)

    def _get_feedback_color(self):
        return self._feedback_color

    feedbackColor = Property(str, _get_feedback_color, notify=feedbackChanged)

    def _get_current_mode(self):
        return self.config.data.get("current_mode", "ALL")

    currentMode = Property(str, _get_current_mode, notify=currentModeChanged)

    def _get_volume(self):
        return int(self.config.data.get("volume_level", 50))

    volumeLevel = Property(int, _get_volume, notify=volumeChanged)

    def _get_is_listening(self):
        return self._is_listening

    isListening = Property(bool, _get_is_listening, notify=listeningChanged)

    def _zaap_missing_accounts(self):
        zaaps = self.config.data.get("macro_positions", {}).get("zaaps", {}) or {}
        return [a["name"] for a in self.logic.get_cycle_list() if a["name"] not in zaaps]

    def _get_calib(self):
        macro = self.config.data.get("macro_positions", {})
        zaaps = macro.get("zaaps", {}) or {}
        active = self.logic.get_cycle_list()
        active_names = [a["name"] for a in active]
        missing = [n for n in active_names if n not in zaaps]
        if not active_names:
            zaap_state = "none"
        elif not missing:
            zaap_state = "full"
        else:
            zaap_state = "partial"
        return {
            "chat": bool(macro.get("chat_position")),
            "xp": bool(macro.get("xp_drop_button")),
            "invite": bool(macro.get("group_accept_button")),
            "zaap": zaap_state,
        }

    calibStates = Property("QVariantMap", _get_calib, notify=calibChanged)

    def _get_auto_zaap_ready(self):
        return self._get_calib().get("zaap") == "full"

    autoZaapReady = Property(bool, _get_auto_zaap_ready, notify=calibChanged)

    def _get_group_invite_ready(self):
        c = self._get_calib()
        return (
            bool(c.get("chat"))
            and bool(self.config.data.get("leader_name"))
            and bool(self.logic.leader_hwnd)
        )

    groupInviteReady = Property(bool, _get_group_invite_ready, notify=calibChanged)

    def _get_swap_xp_ready(self):
        return bool(self._get_calib().get("xp"))

    swapXpReady = Property(bool, _get_swap_xp_ready, notify=calibChanged)

    @Slot(result=bool)
    def canGroupInvite(self):
        return self.groupInviteReady

    @Slot(result=bool)
    def canAutoZaap(self):
        return self.autoZaapReady

    @Slot(result=str)
    def groupInviteCalibHint(self):
        if not self.config.data.get("leader_name"):
            return "Définissez un chef de groupe"
        if not self._get_calib().get("chat"):
            return "Calibrez le chat d'abord"
        if not self.logic.leader_hwnd:
            return "Ouvrez la fenêtre du chef puis F5"
        return "Invitation de Groupe"

    @Slot(result=str)
    def zaapCalibHint(self):
        active = self.logic.get_cycle_list()
        if not active:
            return "Aucun compte actif — ouvrez Dofus puis F5 (ou cochez vos persos)"
        if self._get_calib().get("zaap") == "full":
            return "Auto-Zaap"
        missing = self._zaap_missing_accounts()
        if missing:
            return "Calibrez le zaap pour : " + ", ".join(missing)
        return "Calibrez le Havre-Sac de chaque compte actif"

    @Slot(result=bool)
    def canSwapXp(self):
        return self.swapXpReady

    def _get_colors(self):
        return dict(C)

    colors = Property("QVariantMap", _get_colors, constant=True)

    # ------- toggles (lus une fois, notify global) -------
    def _b(self, key, default=False):
        return bool(self.config.data.get(key, default))

    toolbarActive = Property(bool, lambda s: s._b("toolbar_active"), notify=togglesChanged)
    returnToLeader = Property(bool, lambda s: s._b("return_to_leader", True), notify=togglesChanged)
    spamClick = Property(bool, lambda s: s._b("spam_click_active"), notify=togglesChanged)
    autoInvite = Property(bool, lambda s: s._b("auto_group_accept"), notify=togglesChanged)
    autoTrade = Property(bool, lambda s: s._b("auto_accept_trade"), notify=togglesChanged)
    showTooltips = Property(bool, lambda s: s._b("show_tooltips", True), notify=togglesChanged)
    radialActive = Property(bool, lambda s: s._b("radial_menu_active", True), notify=togglesChanged)

    # ======================================================================
    #  Slots génériques config
    # ======================================================================
    @Slot(str, result=str)
    def skinUrl(self, classe):
        return _skin_url(classe)

    @Slot(str, result=str)
    def assetUrl(self, rel):
        return _asset_url(rel)

    @Slot(str, result=str)
    def getStr(self, key):
        v = self.config.data.get(key, "")
        return "" if v is None else str(v)

    @Slot(str, result=bool)
    def getBool(self, key):
        return bool(self.config.data.get(key, False))

    @Slot(str, "QVariant")
    def saveValue(self, key, value):
        self.config.data[key] = value
        self.config.save()
        self.togglesChanged.emit()

    @Slot(str, bool)
    def saveBool(self, key, value):
        self.config.data[key] = bool(value)
        self.config.save()
        self.togglesChanged.emit()

    @Slot(str, str)
    def saveString(self, key, value):
        self.config.data[key] = value
        self.config.save()

    # ======================================================================
    #  Feedback
    # ======================================================================
    def show_temporary_message(self, text, color=None):
        self.temporaryMessage.emit(text, color or C["primary_bright"])

    @Slot(str, str)
    def _set_feedback(self, text, color):
        self._feedback_text = text
        self._feedback_color = color or C["primary_bright"]
        self.feedbackChanged.emit()
        self._feedback_timer.start(2500)

    def _clear_feedback(self):
        self._feedback_text = ""
        self.feedbackChanged.emit()

    def _on_logic_error(self, msg):
        self.calibrationError.emit(msg)

    @Slot(str)
    def _show_calibration_error(self, msg):
        self.requestShowMain.emit()
        box = QMessageBox()
        box.setWindowTitle("Action Impossible")
        box.setIcon(QMessageBox.Warning)
        box.setText(msg)
        box.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        box.exec()

    # ======================================================================
    #  Liste des comptes
    # ======================================================================
    @Slot()
    def refresh(self):
        slots = self.logic.scan_slots()
        leader_name = self.config.data.get("leader_name", "")
        rows = []
        for idx, acc in enumerate(slots):
            rows.append({
                "name": acc["name"],
                "classe": acc.get("classe", "Inconnu"),
                "active": bool(acc["active"]),
                "team": acc.get("team", "Team 1"),
                "isLeader": acc["name"] == leader_name,
                "icon": _skin_url(acc.get("classe", "Inconnu")),
                "pos": idx + 1,
                "count": len(slots),
            })
        self._accounts = rows
        self.accountsChanged.emit()
        self.calibChanged.emit()
        # ré-applique le highlight courant
        cur = self._current_idx
        cycle = self.logic.get_cycle_list()
        if cycle and 0 <= cur < len(cycle):
            self.activeHighlightChanged.emit(cycle[cur].get("name", ""))

    @Slot(str)
    def setMode(self, mode):
        self.logic.set_mode(mode)
        self.current_idx = 0
        self.currentModeChanged.emit()
        self.setup_hotkeys()
        self.refresh()

    @Slot(str)
    def setLeader(self, name):
        self.logic.set_leader(name)
        self.refresh()

    @Slot(str, bool)
    def toggleAccount(self, name, active):
        self.logic.toggle_account(name, active)
        self.refresh()

    @Slot(str)
    def changeTeam(self, name):
        current = self.config.data.get("accounts_team", {}).get(name, "Team 1")
        new_team = "Team 2" if current == "Team 1" else "Team 1"
        self.logic.change_team(name, new_team)
        self.refresh()

    @Slot(str, int)
    def moveRow(self, name, direction):
        self.logic.move_account(name, direction)
        self.refresh()

    @Slot(str, int)
    def changePosition(self, name, new_pos):
        self.logic.set_account_position(name, new_pos - 1)
        self.refresh()

    @Slot(str)
    def closeAccount(self, name):
        self.logic.close_account_window(name)
        QTimer.singleShot(500, self.refresh)

    @Slot()
    def closeAllAccounts(self):
        self.logic.close_all_active_accounts()
        QTimer.singleShot(500, self.refresh)
        self.show_temporary_message("💥 La team a été fermée !", C["danger_hover"])

    # ======================================================================
    #  Actions rapides (lancées en thread pour ne pas bloquer l'UI)
    # ======================================================================
    def _run_bg(self, func, *args):
        threading.Thread(target=func, args=args, daemon=True).start()

    @Slot()
    def sortTaskbar(self):
        self.logic.sort_taskbar()
        self.show_temporary_message("🚀 Les pages ont été rangées avec succès !", C["primary_bright"])

    @Slot()
    def groupInvite(self):
        self._run_bg(self.logic.execute_group_invite)

    @Slot()
    def pasteEnter(self):
        self._run_bg(self.logic.execute_paste_enter)

    @Slot()
    def autoZaap(self):
        self._run_bg(self.logic.execute_auto_zaap)

    @Slot(str, str)
    def broadcastKey(self, config_key, default):
        k = self.config.data.get(config_key, default)
        self._run_bg(self.logic.broadcast_key, k)

    @Slot()
    def resetSettings(self):
        ret = QMessageBox.question(
            None, "Confirmation",
            "Êtes-vous sûr de vouloir tout réinitialiser ?\n\nToutes vos touches seront perdues.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            self.config.reset_settings()
            self.setup_hotkeys()
            self.hotkeysChanged.emit()
            self.togglesChanged.emit()
            self.currentModeChanged.emit()
            self.volumeChanged.emit()
            self.refresh()

    @Slot()
    def hardKill(self):
        my_pid = os.getpid()
        subprocess.run(
            ["taskkill", "/F", "/PID", str(my_pid), "/T"],
            capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    @Slot(int)
    def setVolume(self, value):
        self.config.data["volume_level"] = value
        self.config.save()
        self.volumeChanged.emit()
        if self.radial:
            self.radial.set_base_volume(value / 100.0)

    @Slot()
    def markTutorialDone(self):
        self.config.data["tutorial_done"] = True
        self.config.save()

    @Slot()
    def launchTutorial(self):
        self.launchTutorialRequested.emit()

    @Slot()
    def onAutoTradeChange(self):
        self._sync_shell_hook()

    # ======================================================================
    #  Fenêtre / tray
    # ======================================================================
    @Slot()
    def showWindow(self):
        self.requestShowMain.emit()

    @Slot()
    def hideWindow(self):
        self.requestHideMain.emit()

    @Slot()
    def quitApp(self):
        self.shutdown()
        self.requestQuit.emit()

    def shutdown(self):
        """Arrêt propre : stoppe le listener et les hooks avant destruction Qt."""
        if self._shutdown_done:
            return
        self._shutdown_done = True
        self._running = False
        try:
            keyboard.unhook_all()
        except Exception as e:
            log_exception("shutdown unhook", e)
        try:
            self.logic.stop_shell_hook()
        except Exception as e:
            log_exception("shutdown shell hook", e)
        try:
            if self.radial:
                self.radial.shutdown()
        except Exception as e:
            log_exception("shutdown radial", e)
        try:
            if self.tray_icon:
                self.tray_icon.hide()
                self.tray_icon.setVisible(False)
                self.tray_icon.deleteLater()
                self.tray_icon = None
        except Exception as e:
            log_exception("shutdown tray", e)
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=1.0)

    # ======================================================================
    #  Vérif logiciel concurrent (Organizer)
    # ======================================================================
    def check_conflicting_software(self):
        if self.config.data.get("ignore_organizer_warning", False):
            return
        try:
            if is_organizer_running():
                self.conflictDetected.emit()
        except Exception as e:
            log_exception("check_conflicting_software", e)

    @Slot(bool)
    def resolveConflictClose(self, ignore_future):
        if ignore_future:
            self.config.data["ignore_organizer_warning"] = True
            self.config.save()
        subprocess.run(
            ["taskkill", "/F", "/IM", "organizer.exe", "/T"],
            capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self.show_temporary_message("✅ Organizer fermé avec succès !", C["primary_bright"])

    @Slot(bool)
    def resolveConflictKeep(self, ignore_future):
        if ignore_future:
            self.config.data["ignore_organizer_warning"] = True
            self.config.save()

    # ======================================================================
    #  HOTKEYS  (port direct de OrganizerApp)
    # ======================================================================
    def get_vk(self, key_str):
        key_str = key_str.lower().strip()
        mapping = {
            "alt": win32con.VK_MENU, "ctrl": win32con.VK_CONTROL, "shift": win32con.VK_SHIFT,
            "left_click": 0x01, "right_click": 0x02, "middle_click": 0x04,
            "mouse4": 0x05, "mouse5": 0x06,
        }
        if key_str in mapping:
            return mapping[key_str]
        scan_code = AZERTY_TO_SCAN.get(key_str)
        if scan_code is not None:
            vk = ctypes.windll.user32.MapVirtualKeyW(scan_code, 1)
            if vk:
                return vk
        if len(key_str) == 1:
            return ord(key_str.upper())
        if key_str.startswith("f") and key_str[1:].isdigit():
            return 0x6F + int(key_str[1:])
        return None

    def is_hotkey_pressed(self, hk_str):
        if not hk_str:
            return False
        parts = hk_str.split("+")
        for p in parts:
            vk = self.get_vk(p.strip())
            if not vk:
                return False
            if win32api.GetAsyncKeyState(vk) >= 0:
                return False
        return True

    def register_action(self, hk_str, func):
        if not hk_str or hotkey_uses_blocked_mouse(hk_str):
            return
        parts = hk_str.lower().split("+")
        if "click" in hk_str or "mouse" in hk_str:
            self.mouse_hotkeys[hk_str] = func
            return
        mods = set()
        main_scan = None
        for p in parts:
            if p in ["ctrl", "alt", "shift"]:
                mods.add(p)
            elif p in AZERTY_TO_SCAN:
                main_scan = AZERTY_TO_SCAN[p]
            else:
                try:
                    main_scan = keyboard.key_to_scan_codes(p)[0]
                except Exception as e:
                    log_exception(f"register_action scan code ({p})", e)
        if main_scan is not None:
            self.hotkey_actions[(frozenset(mods), main_scan)] = func

    def release_modifiers(self):
        try:
            win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.keybd_event(win32con.VK_SHIFT, 0, win32con.KEYEVENTF_KEYUP, 0)
            win32api.mouse_event(0x0100, 0, 0, 0x0001, 0)
            win32api.mouse_event(0x0100, 0, 0, 0x0002, 0)
        except Exception as e:
            log_exception("release_modifiers", e)

    def restore_modifiers(self, mods):
        try:
            if "alt" in mods and win32api.GetAsyncKeyState(win32con.VK_MENU) < 0:
                win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)
            if "ctrl" in mods and win32api.GetAsyncKeyState(win32con.VK_CONTROL) < 0:
                win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
            if "shift" in mods and win32api.GetAsyncKeyState(win32con.VK_SHIFT) < 0:
                win32api.keybd_event(win32con.VK_SHIFT, 0, 0, 0)
        except Exception as e:
            log_exception("restore_modifiers", e)

    def global_hook_listener(self, event):
        current_mods = set()
        if win32api.GetAsyncKeyState(win32con.VK_CONTROL) < 0:
            current_mods.add("ctrl")
        if win32api.GetAsyncKeyState(win32con.VK_MENU) < 0:
            current_mods.add("alt")
        if win32api.GetAsyncKeyState(win32con.VK_SHIFT) < 0:
            current_mods.add("shift")
        key = (frozenset(current_mods), event.scan_code)

        if event.event_type == keyboard.KEY_UP:
            self._hotkey_down.discard(key)
            return
        if event.event_type != keyboard.KEY_DOWN:
            return
        if key not in self.hotkey_actions:
            return
        if key in self._hotkey_down:
            return
        self._hotkey_down.add(key)

        def safe_execute(mods=current_mods):
            try:
                self.release_modifiers()
                self.hotkey_actions[key]()
                time.sleep(0.05)
                self.restore_modifiers(mods)
            except Exception as e:
                log_exception("hotkey safe_execute", e)
            finally:
                self._hotkey_down.discard(key)

        threading.Thread(target=safe_execute, daemon=True).start()

    def _execute_advanced_and_update(self, mode, identifier):
        new_idx = self.logic.execute_advanced_bind(mode, identifier)
        if new_idx != -1:
            self.currentIndexChanged.emit(new_idx)

    def setup_hotkeys(self):
        keyboard.unhook_all()
        self.hotkey_actions = {}
        self.mouse_hotkeys = {}
        self.mouse_states = {}
        self._hotkey_down = set()

        self.register_action("f12", self.quitApp)
        cfg = self.config.data

        mode = cfg.get("advanced_bind_mode", "cycle")
        if mode == "cycle":
            for index, bind_str in enumerate(cfg.get("cycle_row_binds", [])):
                if bind_str:
                    self.register_action(
                        bind_str,
                        lambda idx=index: self._execute_advanced_and_update("cycle", idx))
        elif mode == "bind":
            for pseudo, bind_str in cfg.get("persistent_character_binds", {}).items():
                if bind_str:
                    self.register_action(
                        bind_str,
                        lambda ps=pseudo: self._execute_advanced_and_update("bind", ps))

        try:
            if cfg.get("refresh_key"):
                self.register_action(cfg["refresh_key"], self.refresh)
            if cfg.get("auto_zaap_key"):
                self.register_action(cfg["auto_zaap_key"], self.logic.execute_auto_zaap)
            if cfg.get("sort_taskbar_key"):
                self.register_action(cfg["sort_taskbar_key"], self.logic.sort_taskbar)
            if cfg.get("invite_group_key"):
                self.register_action(cfg["invite_group_key"], self.logic.execute_group_invite)
            if cfg.get("prev_key"):
                self.register_action(cfg["prev_key"], self.prev_char)
            if cfg.get("next_key"):
                self.register_action(cfg["next_key"], self.next_char)
            if cfg.get("leader_key"):
                self.register_action(cfg["leader_key"], self.focus_leader)
            if cfg.get("sync_key"):
                self.register_action(cfg["sync_key"], self.logic.sync_click_all)
            if cfg.get("sync_right_key"):
                self.register_action(cfg["sync_right_key"], self.logic.sync_right_click_all)
            if cfg.get("swap_xp_drop_key"):
                self.register_action(cfg["swap_xp_drop_key"], self.logic.execute_swap_xp_drop)
            if cfg.get("toggle_app_key"):
                self.register_action(cfg["toggle_app_key"], self.requestToggleMain.emit)
            if cfg.get("paste_enter_key"):
                self.register_action(cfg["paste_enter_key"], self.logic.execute_paste_enter)

            keyboard.hook(self.global_hook_listener)
        except Exception as e:
            log_exception("setup_hotkeys", e)

    def focus_leader(self):
        if self.logic.leader_hwnd:
            self.logic.focus_window(self.logic.leader_hwnd)
            cycle_list = self.logic.get_cycle_list()
            leader_name = self.config.data.get("leader_name", "")
            for index, acc in enumerate(cycle_list):
                if acc["name"] == leader_name:
                    self.currentIndexChanged.emit(index)
                    break

    def next_char(self):
        cycle_list = self.logic.get_cycle_list()
        if not cycle_list:
            return
        new_idx = (self._current_idx + 1) % len(cycle_list)
        self.currentIndexChanged.emit(new_idx)
        self.logic.focus_window(cycle_list[new_idx]["hwnd"])

    def prev_char(self):
        cycle_list = self.logic.get_cycle_list()
        if not cycle_list:
            return
        new_idx = (self._current_idx - 1) % len(cycle_list)
        self.currentIndexChanged.emit(new_idx)
        self.logic.focus_window(cycle_list[new_idx]["hwnd"])

    # ======================================================================
    #  BACKGROUND LISTENER (port direct)
    # ======================================================================
    def background_listener(self):
        radial_was_open = False
        while self._running:
            if self.mouse_hotkeys:
                for hk_str, func in list(self.mouse_hotkeys.items()):
                    is_pressed = self.is_hotkey_pressed(hk_str)
                    was_pressed = self.mouse_states.get(hk_str, False)
                    if is_pressed and not was_pressed:
                        self.mouse_states[hk_str] = True

                        def safe_mouse_execute(f=func):
                            self.release_modifiers()
                            f()
                        threading.Thread(target=safe_mouse_execute, daemon=True).start()
                    elif not is_pressed and was_pressed:
                        self.mouse_states[hk_str] = False

            m_pressed = win32api.GetAsyncKeyState(win32con.VK_MBUTTON) < 0
            if m_pressed and self.config.data.get("spam_click_active", False):
                fg_hwnd = win32gui.GetForegroundWindow()
                is_dofus = any(acc["hwnd"] == fg_hwnd for acc in self.logic.all_accounts)
                if is_dofus and not self._spam_click_running:
                    self._spam_click_running = True
                    threading.Thread(target=self._spam_click_loop, daemon=True).start()

            radial_hk = self.config.data.get("radial_menu_hotkey", "")
            radial_active = self.config.data.get("radial_menu_active", True)
            if radial_active and radial_hk:
                is_pressed = self.is_hotkey_pressed(radial_hk)
                if is_pressed and not radial_was_open:
                    radial_was_open = True
                    active_accs = [
                        {"name": acc["name"], "classe": acc.get("classe", "Inconnu"), "hwnd": acc["hwnd"]}
                        for acc in self.logic.get_cycle_list()
                    ]
                    fg_hwnd = win32gui.GetForegroundWindow()
                    current_name = ""
                    for acc in active_accs:
                        if acc["hwnd"] == fg_hwnd:
                            current_name = acc["name"]
                            break
                    x, y = win32api.GetCursorPos()
                    self.radialShowRequested.emit(int(x), int(y), active_accs, current_name)
                elif radial_was_open and not is_pressed:
                    radial_was_open = False
                    self.radialHideRequested.emit()

            try:
                fg_hwnd = win32gui.GetForegroundWindow()
                cycle_list = self.logic.get_cycle_list()
                if cycle_list:
                    for index, acc in enumerate(cycle_list):
                        if acc["hwnd"] == fg_hwnd:
                            if self._current_idx != index:
                                self.currentIndexChanged.emit(index)
                            break
            except Exception as e:
                log_exception("background_listener (foreground sync)", e)

            time.sleep(0.01)

    def on_radial_focus_select(self, target_name):
        if not target_name:
            return
        for acc in self.logic.all_accounts:
            if acc["name"] == target_name:
                self.logic.focus_window(acc["hwnd"])
                break
        cycle_list = self.logic.get_cycle_list()
        for index, acc in enumerate(cycle_list):
            if acc["name"] == target_name:
                self.currentIndexChanged.emit(index)
                break

    def _spam_click_loop(self):
        try:
            while win32api.GetAsyncKeyState(win32con.VK_MBUTTON) < 0:
                cur_fg = win32gui.GetForegroundWindow()
                if not any(acc["hwnd"] == cur_fg for acc in self.logic.all_accounts):
                    break
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.02)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                time.sleep(0.20)
        finally:
            self._spam_click_running = False

    def _require_leader_for_calib(self):
        if self.logic.leader_hwnd:
            return True
        self.show_temporary_message(
            "⚠️ Définissez un chef de groupe avant de calibrer.", C["warning"])
        return False

    # ======================================================================
    #  CAPTURE DE TOUCHE  (port de _listen_hotkey_thread)
    # ======================================================================
    @Slot(str, bool)
    def catchKey(self, config_key, allow_mouse=True):
        if self._is_listening:
            return
        self._is_listening = True
        self.listeningChanged.emit()
        threading.Thread(target=self._listen_hotkey_thread,
                         args=(config_key, allow_mouse), daemon=True).start()

    def _listen_hotkey_thread(self, config_key, allow_mouse):
        captured_key = None
        captured_mods = []

        while (win32api.GetAsyncKeyState(win32con.VK_LBUTTON) < 0
               or win32api.GetAsyncKeyState(win32con.VK_RBUTTON) < 0
               or win32api.GetAsyncKeyState(win32con.VK_MBUTTON) < 0):
            time.sleep(0.01)
        time.sleep(0.1)

        def get_current_mods():
            mods = []
            if win32api.GetAsyncKeyState(win32con.VK_CONTROL) < 0:
                mods.append("ctrl")
            if win32api.GetAsyncKeyState(win32con.VK_MENU) < 0:
                mods.append("alt")
            if win32api.GetAsyncKeyState(win32con.VK_SHIFT) < 0:
                mods.append("shift")
            return mods

        skip = ['alt', 'ctrl', 'shift', 'maj', 'right alt', 'right ctrl',
                'left alt', 'left ctrl', 'menu', 'windows', 'cmd']

        if not allow_mouse:
            while True:
                event = keyboard.read_event(suppress=True)
                if event.event_type == keyboard.KEY_DOWN and event.name not in skip:
                    captured_mods = get_current_mods()
                    captured_key = SCAN_TO_AZERTY.get(event.scan_code, event.name)
                    break
        else:
            def on_key(e):
                nonlocal captured_key, captured_mods
                if e.event_type == keyboard.KEY_DOWN and e.name not in skip:
                    captured_mods = get_current_mods()
                    captured_key = SCAN_TO_AZERTY.get(e.scan_code, e.name)
            hook = keyboard.hook(on_key, suppress=True)
            blocked_mouse_warned = False
            while not captured_key:
                if win32api.GetAsyncKeyState(win32con.VK_LBUTTON) < 0:
                    captured_key = "left_click"
                elif win32api.GetAsyncKeyState(win32con.VK_RBUTTON) < 0:
                    captured_key = "right_click"
                elif win32api.GetAsyncKeyState(win32con.VK_MBUTTON) < 0:
                    captured_key = "middle_click"
                elif win32api.GetAsyncKeyState(0x05) < 0:
                    captured_key = "mouse4"
                elif win32api.GetAsyncKeyState(0x06) < 0:
                    captured_key = "mouse5"
                if captured_key in BLOCKED_MOUSE_HOTKEY_PARTS:
                    if not blocked_mouse_warned:
                        self.show_temporary_message(BLOCKED_MOUSE_HOTKEY_MSG, C["warning"])
                        blocked_mouse_warned = True
                    captured_key = None
                elif captured_key:
                    captured_mods = get_current_mods()
                    break
                time.sleep(0.01)
            keyboard.unhook(hook)

        if captured_key == "esc":
            final_key = self.config.data.get(config_key, "")
        else:
            final_key = ("+".join(captured_mods) + "+" + captured_key
                         if captured_mods else captured_key)
        time.sleep(0.5)
        # appliqué sur le thread GUI
        self.hotkeyCaptured.emit(config_key, final_key)

    @Slot(str, str)
    def applyHotkey(self, config_key, new_value):
        self.release_modifiers()
        if new_value and hotkey_uses_blocked_mouse(new_value):
            self.show_temporary_message(BLOCKED_MOUSE_HOTKEY_MSG, C["warning"])
            self._is_listening = False
            self.listeningChanged.emit()
            self.hotkeysChanged.emit()
            return
        if new_value:
            for k in list(self.config.data.keys()):
                if (k.endswith("_key") or k.endswith("_hotkey")) and k != config_key:
                    existing = self.config.data[k]
                    if isinstance(existing, str) and existing.lower() == new_value.lower():
                        self.config.data[k] = ""
        self.config.data[config_key] = new_value
        self.config.save()
        self.hotkeysChanged.emit()
        self.setup_hotkeys()
        self._is_listening = False
        self.listeningChanged.emit()

    @Slot(str)
    def clearKey(self, config_key):
        if self._is_listening:
            return
        self.applyHotkey(config_key, "")

    # ======================================================================
    #  CALIBRATIONS
    # ======================================================================
    def _calib_key_label(self):
        return self.config.data.get("calib_key", "f4").upper()

    def _wait_for_calib_or_esc(self):
        calib_key = self.config.data.get("calib_key", "f4").lower() or "f4"
        while True:
            event = keyboard.read_event(suppress=True)
            if event.event_type == keyboard.KEY_DOWN:
                if event.name == calib_key:
                    return True
                elif event.name == 'esc':
                    return False

    @Slot(result=str)
    def calibKeyLabel(self):
        return self._calib_key_label()

    def _begin_calib(self):
        if self._is_listening:
            return False
        self._is_listening = True
        self.listeningChanged.emit()
        self.requestHideMain.emit()
        return True

    def _end_calib(self):
        self._is_listening = False
        self.listeningChanged.emit()
        self.calibInstructionHide.emit()
        self.calibChanged.emit()
        self.requestShowMain.emit()

    @Slot()
    def startCalibChat(self):
        if not self._require_leader_for_calib():
            return
        if not self._begin_calib():
            return
        if self.logic.leader_hwnd:
            self.logic.focus_window(self.logic.leader_hwnd)
            time.sleep(0.2)
        k = self._calib_key_label()
        self.calibInstruction.emit(
            f"Cliquez dans le chat Dofus pour pouvoir écrire, placez la souris sur la zone de "
            f"saisie, puis appuyez sur {k}.\n(Échap pour annuler)")
        threading.Thread(target=self._calib_single,
                         args=("chat_position", "✅ Chat calibré !"), daemon=True).start()

    @Slot()
    def startCalibXpDrop(self):
        if not self._require_leader_for_calib():
            return
        if not self._begin_calib():
            return
        if self.logic.leader_hwnd:
            self.logic.focus_window(self.logic.leader_hwnd)
            time.sleep(0.2)
        k = self._calib_key_label()
        self.calibInstruction.emit(
            f"Lancez un combat, placez la souris sur le bouton XP/Drop de fin de combat, "
            f"puis appuyez sur {k}.\n(Échap pour annuler)")
        threading.Thread(target=self._calib_single,
                         args=("xp_drop_button", "✅ XP/Drop calibré !"), daemon=True).start()

    @Slot()
    def startCalibGroupAccept(self):
        if not self._require_leader_for_calib():
            return
        if not self._begin_calib():
            return
        if self.logic.leader_hwnd:
            self.logic.focus_window(self.logic.leader_hwnd)
            time.sleep(0.2)
        k = self._calib_key_label()
        self.calibInstruction.emit(
            f"Placez la souris sur le bouton « Accepter l'invitation de groupe », "
            f"puis appuyez sur {k}.\n(Échap pour annuler)")
        threading.Thread(target=self._calib_single,
                         args=("group_accept_button", "✅ Invitation calibrée !"), daemon=True).start()

    def _calib_single(self, pos_key, success_msg):
        if self._wait_for_calib_or_esc():
            rx, ry = self.logic.get_relative_ratio_pos(self.logic.leader_hwnd)
            self.config.data["macro_positions"][pos_key] = [rx, ry]
            self.config.save()
            self.show_temporary_message(success_msg, C["primary_bright"])
        self._end_calib()

    @Slot()
    def startCalibZaap(self):
        active_accounts = self.logic.get_cycle_list()
        zaaps = self.config.data.get("macro_positions", {}).get("zaaps", {}) or {}
        to_calibrate = [a for a in active_accounts if a["name"] not in zaaps]
        if not active_accounts:
            self.show_temporary_message("⚠️ Aucun compte actif à calibrer.", C["warning"])
            return
        if not to_calibrate:
            self.show_temporary_message(
                "✅ Tous les comptes actifs ont déjà un zaap calibré.", C["primary_bright"])
            self.calibChanged.emit()
            return
        if not self._begin_calib():
            return
        threading.Thread(target=self._calib_zaap_sequence,
                         args=(to_calibrate,), daemon=True).start()

    @Slot()
    def forceRecalibZaap(self):
        """Efface les positions Zaap enregistrées et relance la calibration pour tous les comptes actifs."""
        active_accounts = self.logic.get_cycle_list()
        if not active_accounts:
            self.show_temporary_message("⚠️ Aucun compte actif à calibrer.", C["warning"])
            return
        self.config.data.setdefault("macro_positions", {})["zaaps"] = {}
        self.config.save()
        self.calibChanged.emit()
        if not self._begin_calib():
            return
        threading.Thread(target=self._calib_zaap_sequence,
                         args=(active_accounts,), daemon=True).start()

    def _calib_zaap_sequence(self, active_accounts):
        k = self._calib_key_label()
        zaaps = self.config.data.setdefault("macro_positions", {}).setdefault("zaaps", {})
        calibrated_any = False
        for acc in active_accounts:
            self.logic.focus_window(acc["hwnd"])
            time.sleep(0.2)
            self.calibInstruction.emit(
                f"Allez dans le havre-sac de {acc['name']}, placez la souris sur le haut du "
                f"Zaap, puis appuyez sur {k}.\n(Échap pour annuler)")
            if not self._wait_for_calib_or_esc():
                missing = [a["name"] for a in active_accounts if a["name"] not in zaaps]
                if calibrated_any:
                    self.config.save()
                    self.calibChanged.emit()
                if missing:
                    self.show_temporary_message(
                        f"⚠️ Calibration interrompue. Manque : {', '.join(missing)}",
                        C["warning"],
                    )
                else:
                    self.show_temporary_message("❌ Calibration Zaap annulée.", C["danger_hover"])
                self._end_calib()
                return
            rx, ry = self.logic.get_relative_ratio_pos(acc["hwnd"])
            zaaps[acc["name"]] = [rx, ry]
            self.config.save()
            calibrated_any = True
            self.calibChanged.emit()
            self.show_temporary_message(f"✅ Zaap de {acc['name']} calibré !", C["primary_bright"])
        self.show_temporary_message("✅ Calibration Zaap totale terminée !", C["primary_bright"])
        self._end_calib()

    # ======================================================================
    #  GESTIONNAIRE DE BINDS AVANCÉ
    # ======================================================================
    @Slot(result="QVariantMap")
    def getBindManagerData(self):
        cfg = self.config.data
        mode = cfg.get("advanced_bind_mode", "cycle")
        modifier = cfg.get("advanced_bind_modifier", "ctrl")
        active = self.logic.get_cycle_list()
        rows = []
        if mode == "cycle":
            row_binds = cfg.get("cycle_row_binds", [])
            for i in range(8):
                full = row_binds[i] if i < len(row_binds) else ""
                base = full.split("+")[-1] if full else ""
                pseudo = active[i]["name"] if i < len(active) else "---"
                rows.append({"id": str(i), "label": f"Place n°{i+1}",
                             "sub": f"({pseudo})", "key": base, "icon": ""})
        else:
            char_binds = cfg.get("persistent_character_binds", {})
            for acc in active:
                pseudo = acc["name"]
                full = char_binds.get(pseudo, "")
                base = full.split("+")[-1] if full else ""
                rows.append({"id": pseudo, "label": pseudo, "sub": "",
                             "key": base, "icon": _skin_url(acc.get("classe", "Inconnu"))})
        return {"mode": mode, "modifier": modifier, "rows": rows}

    @Slot(str)
    def setBindMode(self, mode):
        self.config.data["advanced_bind_mode"] = mode
        self.config.save()
        self.setup_hotkeys()

    @Slot(str, "QVariantList")
    def saveBindManager(self, modifier, rows):
        prefix = f"{modifier}+" if modifier != "aucun" else ""
        cfg = self.config.data
        cfg["advanced_bind_modifier"] = modifier
        mode = cfg.get("advanced_bind_mode", "cycle")
        if mode == "cycle":
            new_binds = []
            for i in range(8):
                base = ""
                for r in rows:
                    if str(r.get("id")) == str(i):
                        base = (r.get("key") or "").lower().strip()
                        break
                new_binds.append(prefix + base if base else "")
            cfg["cycle_row_binds"] = new_binds
        else:
            for r in rows:
                base = (r.get("key") or "").lower().strip()
                cfg["persistent_character_binds"][r.get("id")] = prefix + base if base else ""
        self.config.save()
        self.setup_hotkeys()
        self.show_temporary_message("✅ Raccourcis enregistrés avec succès !", C["primary_bright"])

    @Slot(str)
    def catchBindKey(self, row_id):
        """Capture une touche simple (sans modificateur) pour le gestionnaire de binds."""
        if self._is_listening:
            return
        self._is_listening = True
        self.listeningChanged.emit()
        threading.Thread(target=self._listen_bind_thread, args=(str(row_id),), daemon=True).start()

    def _listen_bind_thread(self, row_id):
        captured = ""
        skip = ['alt', 'ctrl', 'shift', 'maj', 'right alt', 'right ctrl',
                'left alt', 'left ctrl', 'menu', 'windows', 'cmd']

        def on_key(e):
            nonlocal captured
            if e.event_type == keyboard.KEY_DOWN and e.name not in skip:
                captured = SCAN_TO_AZERTY.get(e.scan_code, e.name)

        hook = keyboard.hook(on_key, suppress=True)
        while not captured:
            if win32api.GetAsyncKeyState(0x05) < 0:
                captured = "mouse4"
            elif win32api.GetAsyncKeyState(0x06) < 0:
                captured = "mouse5"
            elif win32api.GetAsyncKeyState(0x04) < 0:
                captured = "middle_click"
            time.sleep(0.01)
        keyboard.unhook(hook)
        time.sleep(0.3)
        self.release_modifiers()
        if captured == "esc":
            captured = ""
        self._is_listening = False
        self.listeningChanged.emit()
        self.bindKeyCaptured.emit(row_id, captured)
