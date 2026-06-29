"""
Test d'intégration REFRAMED QML (offscreen) — pilote l'UI au runtime :
 - ouvre chaque fenêtre secondaire (Paramètres, Tutoriel, Binds, Toolbar)
 - bascule des switches / change de mode via les slots
 - affiche la roue radiale avec des comptes factices
 - vérifie qu'AUCUN warning QML n'apparaît pendant ces interactions

Lancement : py -3 tests/integration_test.py
"""

import os
import sys

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["QT_QUICK_CONTROLS_STYLE"] = "Basic"
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "hide")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FAILURES = []
WARNINGS = []


def check(cond, msg):
    print(f"  [{'OK' if cond else 'FAIL'}]   {msg}")
    if not cond:
        FAILURES.append(msg)


def main():
    from PySide6.QtCore import QUrl, QTimer, QMetaObject, Qt
    from PySide6.QtWidgets import QApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from constants import resource_path, COLORS as C
    from app_controller import AppController
    from radial_controller import RadialController

    qapp = QApplication.instance() or QApplication(sys.argv)
    controller = AppController()
    radial = RadialController(controller.on_radial_focus_select)
    controller.radial = radial

    engine = QQmlApplicationEngine()
    engine.warnings.connect(lambda ws: WARNINGS.extend(str(w.toString()) for w in ws))
    ctx = engine.rootContext()
    ctx.setContextProperty("app", controller)
    ctx.setContextProperty("radial", radial)
    ctx.setContextProperty("Colors", dict(C))
    engine.load(QUrl.fromLocalFile(resource_path(os.path.join("qml", "Main.qml"))))

    roots = engine.rootObjects()
    check(len(roots) > 0, "Main.qml chargé")
    if not roots:
        return 1
    root = roots[0]

    def find(name):
        for child in root.findChildren(object):
            if child.objectName() == name:
                return child
        return None

    def drive():
        # ouvre les fenêtres secondaires
        for win_name, method in [
            ("settingsWin", "openSettings"),
            ("tutoWin", "openTutorial"),
            ("charWin", "openManager"),
        ]:
            w = find(win_name)
            check(w is not None, f"fenêtre {win_name} trouvée")
            if w is not None:
                QMetaObject.invokeMethod(w, method)

        # toolbar visible via toggle
        controller.saveValue("toolbar_active", True)
        tb = find("toolbarWin")
        if tb is not None:
            tb.setProperty("visible", True)

        # interactions backend
        controller.setMode("Team 1")
        controller.saveBool("show_tooltips", False)
        controller.saveBool("show_tooltips", True)
        controller.setVolume(80)

        # roue radiale avec comptes factices
        radial.set_scale(1.0)
        radial.show(600, 400,
                    [{"name": "Bob", "classe": "iop"},
                     {"name": "Alice", "classe": "cra"},
                     {"name": "Zed", "classe": "sram"}], "Bob")

        QTimer.singleShot(400, finish)

    def finish():
        radial.hide()
        # ferme les fenêtres
        for n in ["settingsWin", "tutoWin", "charWin", "toolbarWin"]:
            w = find(n)
            if w is not None:
                QMetaObject.invokeMethod(w, "close")
        QTimer.singleShot(100, qapp.quit)

    QTimer.singleShot(200, drive)
    qapp.exec()
    controller.shutdown()

    real_warns = [w for w in WARNINGS if "QSystemTrayIcon" not in w]
    if real_warns:
        print("  --- Warnings QML ---")
        for w in real_warns:
            print("   !", w)
    check(len(real_warns) == 0, "aucun warning QML pendant les interactions")

    print()
    if FAILURES:
        print(f"ÉCHEC : {len(FAILURES)} test(s)")
        return 1
    print("SUCCÈS : intégration OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
