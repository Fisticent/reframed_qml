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
import base64

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
QT_MCP_DEFAULT_PORT = 9142


def _qt_mcp_enabled() -> bool:
    return os.environ.get("QT_MCP_PROBE") == "1" or "--qt-mcp" in sys.argv


def _install_qt_mcp_probe():
    """In-process JSON-RPC probe for qt-mcp MCP server (dev / agent UX checks)."""
    if not _qt_mcp_enabled():
        return None
    try:
        from qt_mcp.probe import install
    except ImportError:
        print(
            "[REFRAMED] qt-mcp non installé — pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        return None
    port = int(os.environ.get("QT_MCP_PORT", str(QT_MCP_DEFAULT_PORT)))
    probe = install(port=port)
    if probe is None:
        print("[REFRAMED] qt-mcp : échec démarrage probe", file=sys.stderr)
        return None
    print(f"[REFRAMED] qt-mcp probe actif sur localhost:{port}", file=sys.stderr)
    return probe


def _patch_qt_mcp_for_qml(probe) -> None:
    """qt-mcp cible QWidget ; les fenêtres QML sont des QWindow — fallback grab()."""
    from qt_mcp.probe._qt_compat import QtCore

    QBuffer = QtCore.QBuffer
    QIODevice = QtCore.QIODevice
    Qt = QtCore.Qt
    orig_screenshot = probe._screenshotter.screenshot

    def _encode_pixmap(pixmap, fmt: str, quality: int, max_width: int, max_height: int) -> dict:
        if pixmap.isNull():
            raise ValueError("grab() returned null pixmap")
        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(
                max_width,
                max_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        image_format = fmt.upper()
        if image_format not in ("PNG", "JPEG"):
            image_format = "PNG"
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        if image_format == "JPEG":
            pixmap.save(buf, "JPEG", quality)
        else:
            pixmap.save(buf, "PNG")
        img_bytes = bytes(buf.data())
        buf.close()
        return {
            "image": base64.b64encode(img_bytes).decode("ascii"),
            "width": pixmap.width(),
            "height": pixmap.height(),
            "format": image_format.lower(),
        }

    def _grab_window(window: QWindow):
        from PySide6.QtQuick import QQuickWindow

        if isinstance(window, QQuickWindow):
            image = window.grabWindow()
            if image.isNull():
                raise ValueError("grabWindow() returned null image")
            from PySide6.QtGui import QPixmap

            return QPixmap.fromImage(image)
        screen = window.screen() or QGuiApplication.primaryScreen()
        if screen is None:
            raise ValueError("No screen for window grab")
        pixmap = screen.grabWindow(window.winId())
        if pixmap.isNull():
            raise ValueError("screen.grabWindow() returned null pixmap")
        return pixmap

    def _visible_qml_windows():
        windows = [w for w in QGuiApplication.allWindows() if w.isVisible()]
        return sorted(windows, key=lambda w: w.width() * w.height(), reverse=True)

    def screenshot(**params):
        try:
            return orig_screenshot(**params)
        except ValueError as exc:
            if "No visible" not in str(exc) and "not a QWidget" not in str(exc):
                raise
        windows = _visible_qml_windows()
        if not windows:
            raise ValueError("No visible QML/Qt window")
        window = windows[0]
        ref = params.get("ref")
        if ref:
            obj = probe._registry.resolve_or_raise(ref)
            if isinstance(obj, QWindow):
                window = obj
            else:
                raise ValueError(f"Ref {ref} is not a QWindow")
        return _encode_pixmap(
            _grab_window(window),
            params.get("format", "png"),
            int(params.get("quality", 80)),
            int(params.get("max_width", 1920)),
            int(params.get("max_height", 1080)),
        )

    probe._screenshotter.screenshot = screenshot

    orig_snapshot = probe._introspector.snapshot

    def snapshot(**params):
        result = orig_snapshot(**params)
        if result.get("widget_count", 0) > 0:
            return result
        lines = [result.get("tree", "").strip() or "(no QWidget tree)"]
        count = 0
        for window in QGuiApplication.allWindows():
            if not window.isVisible():
                continue
            ref = probe._registry.register(window, prefix="w")
            title = window.title() or window.objectName() or type(window).__name__
            lines.append(
                f"- {type(window).__name__} \"{title}\" "
                f"[{window.width()}x{window.height()}] [ref={ref}]"
            )
            count += 1
        if count:
            lines.insert(0, f"QML/Qt windows: {count}")
        return {
            "tree": "\n".join(lines),
            "widget_count": count,
            "generation": result.get("generation", 0),
        }

    probe._introspector.snapshot = snapshot


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except OSError as e:
        log_exception("is_admin", e)
        return False


def run_as_admin():
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, "frozen", False):
        params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, parent_dir, 1)
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

    pending_update = None
    if "--no-update" not in sys.argv:
        try:
            from updater import check_update_available
            pending_update = check_update_available()
        except Exception as e:
            log_exception("updater check", e)

    qapp = QApplication(sys.argv)
    qt_mcp_probe = _install_qt_mcp_probe()
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

    if qt_mcp_probe is not None:
        _patch_qt_mcp_for_qml(qt_mcp_probe)

    root = engine.rootObjects()[0]
    radial_win = root.findChild(QObject, "radialWin", Qt.FindChildOption.FindChildrenRecursively)
    if isinstance(radial_win, QWindow):
        radial.set_window(radial_win)
    else:
        log_exception("radial window", RuntimeError("RadialMenu introuvable"))

    tray = build_tray(qapp, controller)
    controller.tray_icon = tray

    controller.requestQuit.connect(qapp.quit)
    controller.updateReadyToApply.connect(controller.quitApp)

    if pending_update is not None:
        try:
            from updater import download_and_apply_async
            download_and_apply_async(pending_update, controller.updateReadyToApply.emit)
        except Exception as e:
            log_exception("updater download", e)

    def _on_about_to_quit():
        controller.shutdown()
        try:
            radial.shutdown()
        except Exception:
            pass
        if app_sock is not None:
            try:
                app_sock.close()
            except OSError:
                pass
        try:
            engine.clearComponentCache()
        except Exception:
            pass
        qapp.processEvents()
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
