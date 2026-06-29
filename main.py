"""
REFRAMED — version PySide6 / QML.

Point d'entrée : élévation admin (UAC), instance unique, QApplication + QML,
system tray, et câblage AppController <-> RadialController <-> QML.
"""

import os
import sys
import socket
import ctypes
import threading

# DPI : on laisse Qt6 gérer (PerMonitorV2 par défaut). Le curseur win32 utilisé
# par la roue radiale est converti via devicePixelRatio (RadialController.scale).

# Forcer le clavier AZERTY (comme l'original)
try:
    ctypes.windll.user32.LoadKeyboardLayoutW("0000040C", 1 | 0x00000100)
except Exception:
    pass

# Style QtQuick.Controls personnalisable
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")

from PySide6.QtCore import QUrl, QTimer, Qt, QObject
from PySide6.QtGui import QGuiApplication, QIcon, QAction, QWindow
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtQml import QQmlApplicationEngine

from constants import resource_path, log_exception, COLORS as C
from app_controller import AppController
from radial_controller import RadialController

UDP_PORT = 43212


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except OSError as e:
        log_exception("is_admin", e)
        return False


def run_as_admin():
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv[1:]), parent_dir, 1)
    else:
        script = os.path.abspath(sys.argv[0])
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, f'"{script}" {params}', parent_dir, 1)


def handle_multiple_instances():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.bind(("127.0.0.1", UDP_PORT))
        return sock
    except OSError:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            client.sendto(b"SHOW", ("127.0.0.1", UDP_PORT))
        except OSError as e:
            log_exception("handle_multiple_instances", e)
        sys.exit(0)


def build_tray(qapp, controller):
    icon_path = resource_path("logo.ico")
    icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
    tray = QSystemTrayIcon(icon, qapp)
    tray.setToolTip("REFRAMED")
    menu = QMenu()
    act_toggle = QAction("Afficher / Cacher", qapp)
    act_quit = QAction("Quitter", qapp)
    act_toggle.triggered.connect(controller.requestToggleMain.emit)
    act_quit.triggered.connect(controller.quitApp)
    menu.addAction(act_toggle)
    menu.addAction(act_quit)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: controller.requestToggleMain.emit()
        if reason == QSystemTrayIcon.Trigger else None)
    tray.show()
    return tray


def main():
    skip_admin = "--no-admin" in sys.argv
    if not skip_admin and not is_admin():
        run_as_admin()
        sys.exit()

    app_sock = None
    if "--no-single" not in sys.argv:
        app_sock = handle_multiple_instances()

    qapp = QApplication(sys.argv)
    qapp.setQuitOnLastWindowClosed(False)
    icon_path = resource_path("logo.ico")
    if os.path.exists(icon_path):
        qapp.setWindowIcon(QIcon(icon_path))

    controller = AppController()

    radial = RadialController(controller.on_radial_focus_select)
    try:
        radial.set_scale(QGuiApplication.primaryScreen().devicePixelRatio())
    except Exception as e:
        log_exception("radial set_scale", e)
    controller.radial = radial
    radial.set_base_volume(controller.config.data.get("volume_level", 50) / 100.0)

    # Roue radiale : signaux backend -> contrôleur (queued, thread-safe)
    controller.radialShowRequested.connect(radial.show)
    controller.radialHideRequested.connect(radial.hide)

    engine = QQmlApplicationEngine()
    ctx = engine.rootContext()
    ctx.setContextProperty("app", controller)
    ctx.setContextProperty("radial", radial)
    ctx.setContextProperty("Colors", dict(C))

    qml_main = resource_path(os.path.join("qml", "Main.qml"))
    engine.load(QUrl.fromLocalFile(qml_main))
    if not engine.rootObjects():
        print("[REFRAMED] ERREUR : échec du chargement QML", file=sys.stderr)
        sys.exit(1)

    root = engine.rootObjects()[0]
    radial_win = root.findChild(QObject, "radialWin", Qt.FindChildOption.FindChildrenRecursively)
    if isinstance(radial_win, QWindow):
        radial.set_window(radial_win)
    else:
        log_exception("radial window", RuntimeError("RadialMenu introuvable"))

    tray = build_tray(qapp, controller)
    controller.tray_icon = tray

    controller.requestQuit.connect(qapp.quit)

    def _on_about_to_quit():
        controller.shutdown()
        try:
            radial._timer.stop()
        except Exception:
            pass
    qapp.aboutToQuit.connect(_on_about_to_quit)

    # Écoute UDP pour réveiller l'instance existante
    if app_sock is not None:
        def udp_listener():
            while True:
                try:
                    data, _ = app_sock.recvfrom(1024)
                    if data == b"SHOW":
                        controller.requestShowMain.emit()
                except OSError as e:
                    log_exception("udp_listener", e)
                    break
        threading.Thread(target=udp_listener, daemon=True).start()

    # Démarrage de la logique (listener, hotkeys, scan) après boucle lancée
    QTimer.singleShot(0, controller.start)

    # Mode self-test : lance réellement l'UI puis quitte (validation intégration)
    if "--selftest" in sys.argv:
        QTimer.singleShot(2500, lambda: (print("[REFRAMED] self-test OK : UI lancée puis fermée."), qapp.quit()))

    exit_code = qapp.exec()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
