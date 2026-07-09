"""
Smoke test REFRAMED QML — valide sans afficher de fenêtre (plateforme offscreen) :
 - tous les modules s'importent
 - le moteur QML charge Main.qml SANS aucun warning/erreur QML
 - les propriétés exposées à QML répondent
 - round-trip de configuration (save/load)
 - quelques slots du contrôleur ne lèvent pas

Lancement : py -3 tests/smoke_test.py
Sortie : code 0 si tout est OK, 1 sinon.
"""

import os
import sys
import json
import tempfile

# Headless : pas de vraie fenêtre, pas de display requis
os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "hide")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FAILURES = []


def check(cond, msg):
    if cond:
        print(f"  [OK]   {msg}")
    else:
        print(f"  [FAIL] {msg}")
        FAILURES.append(msg)


def main():
    print("== 1. Imports backend ==")
    import constants
    import config_manager
    import logic
    import app_controller
    import radial_controller
    check(True, "imports backend + contrôleurs")

    print("== 2. Config round-trip ==")
    tmp = os.path.join(tempfile.gettempdir(), "reframed_smoke_settings.json")
    if os.path.exists(tmp):
        os.remove(tmp)
    cfg = config_manager.Config(filename=tmp)
    cfg.data["prev_key"] = "tab"
    cfg.data["window_x"] = 123
    cfg.data["window_y"] = 456
    cfg.data["window_width"] = 640
    cfg.data["window_height"] = 720
    cfg.save()
    cfg2 = config_manager.Config(filename=tmp)
    check(cfg2.data.get("window_x") == 123, "config persiste window_x")
    check(cfg2.data.get("window_y") == 456, "config persiste window_y")
    check(cfg2.data.get("window_width") == 640, "config persiste window_width")
    check(cfg2.data.get("window_height") == 720, "config persiste window_height")
    check(cfg2.data.get("prev_key") == "tab", "config persiste prev_key")

    print("== 2b. Config reset ==")
    from config_manager import default_settings_data
    tmp_reset = os.path.join(tempfile.gettempdir(), "reframed_smoke_reset.json")
    if os.path.exists(tmp_reset):
        os.remove(tmp_reset)
    cfg_reset = config_manager.Config(filename=tmp_reset)
    cfg_reset.data["prev_key"] = "custom"
    cfg_reset.data["leader_name"] = "TestLeader"
    cfg_reset.save()
    cfg_reset.reset_settings()
    defaults = default_settings_data()
    check(cfg_reset.data.get("prev_key") == defaults["prev_key"], "reset restaure prev_key")
    check(cfg_reset.data.get("leader_name") == defaults["leader_name"], "reset vide leader_name")
    check(cfg_reset.migrated_from is None, "reset sans migration legacy")
    check(os.path.exists(tmp_reset), "reset réécrit settings.json")

    print("== 3. QApplication + QML ==")
    from PySide6.QtCore import QUrl, QTimer
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtWidgets import QApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from constants import resource_path, COLORS as C
    from app_controller import AppController
    from radial_controller import RadialController

    qapp = QApplication.instance() or QApplication(sys.argv)

    qml_warnings = []
    qapp.aboutToQuit.connect(lambda: None)

    controller = AppController()
    radial = RadialController(controller.on_radial_focus_select)
    controller.radial = radial

    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda warns: qml_warnings.extend(str(w.toString()) for w in warns))
    ctx = engine.rootContext()
    ctx.setContextProperty("app", controller)
    ctx.setContextProperty("radial", radial)
    ctx.setContextProperty("Colors", dict(C))

    qml_main = resource_path(os.path.join("qml", "Main.qml"))
    check(os.path.exists(qml_main), "qml/Main.qml présent")
    engine.load(QUrl.fromLocalFile(qml_main))

    # Injecte de faux comptes pour exercer le delegate de liste (icônes, combos,
    # position, équipe, leader) — non couvert par un scan vide.
    fake = [
        {"name": "Bob", "classe": "iop", "active": True, "team": "Team 1",
         "isLeader": True, "icon": controller.skinUrl("iop"), "pos": 1, "count": 2},
        {"name": "Alice", "classe": "cra", "active": False, "team": "Team 2",
         "isLeader": False, "icon": controller.skinUrl("cra"), "pos": 2, "count": 2},
    ]
    controller._accounts = fake
    controller.accountsChanged.emit()
    controller.activeHighlightChanged.emit("Bob")

    # laisse le moteur instancier l'arbre (et les fenêtres enfants) + delegates
    QTimer.singleShot(400, qapp.quit)
    qapp.exec()

    roots = engine.rootObjects()
    check(len(roots) > 0, "Main.qml chargé (rootObjects non vide)")

    # Filtre : on ignore les warnings inoffensifs liés à offscreen / tray
    real_warns = [w for w in qml_warnings
                  if "QSystemTrayIcon" not in w and "Wayland" not in w]
    if real_warns:
        print("  --- Warnings QML ---")
        for w in real_warns:
            print("   !", w)
    check(len(real_warns) == 0, "aucun warning/erreur QML")

    print("== 4. Propriétés exposées ==")
    check(isinstance(controller.property("accounts"), list), "property accounts")
    check(isinstance(controller.property("hotkeys"), dict), "property hotkeys")
    check(controller.property("currentMode") in ("ALL", "Team 1", "Team 2"), "property currentMode")
    check(isinstance(controller.property("calibStates"), dict), "property calibStates")
    check(isinstance(controller.property("autoZaapReady"), bool), "property autoZaapReady")
    check(isinstance(controller.property("groupInviteReady"), bool), "property groupInviteReady")
    check(isinstance(controller.property("swapXpReady"), bool), "property swapXpReady")
    check(isinstance(controller.property("colors"), dict), "property colors")

    print("== 5. Slots sûrs (sans Dofus) ==")
    try:
        controller.getStr("prev_key")
        controller.getBool("show_tooltips")
        controller.skinUrl("iop")
        controller.getBindManagerData()
        controller.refresh()  # scan win32 -> [] sans Dofus
        check(True, "getStr/getBool/skinUrl/getBindManagerData/refresh OK")
    except Exception as e:
        check(False, f"slot a levé : {e}")

    print("== 5b. Raccourcis souris interdits ==")
    from constants import hotkey_uses_blocked_mouse, sanitize_blocked_mouse_hotkeys
    check(hotkey_uses_blocked_mouse("left_click"), "left_click bloqué")
    check(hotkey_uses_blocked_mouse("alt+right_click"), "alt+right_click bloqué")
    check(not hotkey_uses_blocked_mouse("f3"), "f3 autorisé")
    check(not hotkey_uses_blocked_mouse("middle_click"), "middle_click autorisé")
    sample = {"prev_key": "tab", "sync_key": "left_click", "radial_menu_hotkey": "alt+right_click"}
    check(sanitize_blocked_mouse_hotkeys(sample), "sanitize détecte les clics G/D")
    check(sample["prev_key"] == "tab" and sample["sync_key"] == "", "sanitize conserve / efface")

    print("== 5c. Auto-refresh fenêtres Dofus ==")
    from logic import is_recognized_dofus_character_title, DofusLogic
    check(is_recognized_dofus_character_title("Bob - Iop"), "titre perso reconnu")
    check(not is_recognized_dofus_character_title("Dofus"), "titre launcher ignoré")
    check(not is_recognized_dofus_character_title(""), "titre vide ignoré")
    logic = DofusLogic(cfg)
    check(logic.shell_hook_needed(), "shell hook actif avec auto_refresh par défaut")
    logic.config.data["auto_refresh_windows"] = False
    logic.config.data["auto_accept_trade"] = False
    check(not logic.shell_hook_needed(), "shell hook off si tout désactivé")

    print("== 6. Radial controller ==")
    try:
        radial.set_scale(1.5)
        radial.show(500, 500, [{"name": "Bob", "classe": "iop"}], "Bob")
        check(radial.property("isOpen") is True, "radial s'ouvre")
        radial.hide()
        check(radial.property("isOpen") is False, "radial se ferme")
    except Exception as e:
        check(False, f"radial a levé : {e}")

    print()
    if FAILURES:
        print(f"ÉCHEC : {len(FAILURES)} test(s) en échec")
        return 1
    print("SUCCÈS : tous les tests passent")
    return 0


if __name__ == "__main__":
    sys.exit(main())
