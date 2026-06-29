# REFRAMED — édition PySide6 / QML

Réécriture de **REFRAMED** (gestionnaire multi-comptes Dofus, Windows) avec une
interface **PySide6 + QML** à la place de CustomTkinter. Mêmes fonctionnalités,
look moderne, transparence/anti-aliasing natifs et DPI géré par Qt6.

## Prérequis

- **Windows 10/11**, clavier **AZERTY**, droits **administrateur** (UAC au lancement)
- Python 3.10+ (testé 3.13)

## Lancement

### Mode dev (avec console, sans admin/instance unique)

```powershell
pip install -r requirements.txt
.\run_dev.bat
```

ou directement :

```powershell
py -3 main.py --no-admin --no-single
```

### Mode normal (admin + instance unique + tray)

```powershell
.\run.bat
```

### Flags utiles

| Flag | Effet |
|------|-------|
| `--no-admin` | ne demande pas l'élévation UAC (dev) |
| `--no-single` | désactive le verrou d'instance unique (dev) |
| `--selftest` | lance l'UI réelle puis se ferme après 2,5 s (CI/validation) |

## Tests

```powershell
py -3 tests/smoke_test.py        # imports, chargement QML, config, props, radial
py -3 tests/integration_test.py  # ouvre les fenêtres, toggles, roue radiale
```

Les deux tournent en **offscreen** (aucune fenêtre affichée) et échouent si le
moindre warning QML apparaît.

## Architecture

| Fichier | Rôle |
|---------|------|
| `main.py` | Entrée : QApplication, UAC, instance unique, moteur QML, tray, câblage |
| `app_controller.py` | Pont QObject↔QML : hotkeys, background listener, calibrations, tray, propriétés/slots/signals |
| `radial_controller.py` | État + polling curseur + sons de la roue radiale |
| `logic.py` | Logique Dofus pure Win32 (**identique à l'original**) |
| `config_manager.py` | Chargement/sauvegarde settings (**identique à l'original**) |
| `constants.py` | Couleurs (`COLORS`), mapping AZERTY, chemins ressources — **source de vérité UI** |
| `DESIGN.md` | Tokens, composants et règles de contraste |
| `qml/Main.qml` | Fenêtre principale + assemblage des fenêtres enfants |
| `qml/SettingsWindow.qml` | Paramètres |
| `qml/TutorialWindow.qml` | Tutoriel paginé |
| `qml/CharManagerWindow.qml` | Gestionnaire de binds avancé (cycle/bind) |
| `qml/ToolbarWindow.qml` | Toolbar flottante in-game (overlay translucide) |
| `qml/RadialMenu.qml` | Roue radiale (Canvas, fenêtre translucide topmost) |
| `qml/components/` | Composants thémés (`ThemedButton`, `ThemedSwitch`, `HotkeyButton`, `ThemedComboBox`, …) |

### Communication threads → UI

La logique tourne dans des threads (listener souris/clavier, hooks `keyboard`,
shell hook). Toute remontée vers l'UI passe par des **signals Qt** (queued,
thread-safe) — équivalent du `root.after()` de la version Tkinter.

## Différences vs la version Tkinter

- **DPI** : géré nativement par Qt6 (PerMonitorV2). Plus de hack de re-scaling.
- **Roue radiale** : rendu Canvas anti-aliasé, vraie transparence, click-through
  (`Qt.WindowTransparentForInput`) ; le curseur global est converti en
  coordonnées logiques via `devicePixelRatio`.
- **Tray** : `QSystemTrayIcon` (au lieu de pystray).
- **Tooltips / dialogs** : natifs Qt.
- **Sons** : pygame conservé.

## Build de l'exe

```powershell
pip install -r requirements.txt pyinstaller
pyinstaller Reframed.spec
```

Résultat : `dist\Reframed.exe`. Les settings sont écrits dans
`%LOCALAPPDATA%\Reframed\settings.json` (mode exe).

## Avertissement

L'automatisation de jeu peut enfreindre les CGU d'Ankama / Dofus. À vos risques.

## Stack

Python 3 · PySide6 (Qt Quick / QML) · pywin32 · keyboard · pygame-ce · PyInstaller
